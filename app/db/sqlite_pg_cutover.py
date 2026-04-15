from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

import sqlalchemy as sa
from sqlalchemy import MetaData, Table, create_engine, delete, func, inspect, select, tuple_
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.engine import Connection
from sqlalchemy.engine.url import make_url

from app.db.migration_url import to_sync_database_url

Mode = Literal["full-copy", "final-sync"]


@dataclass(frozen=True, slots=True)
class TableSyncConfig:
    name: str
    pk_columns: tuple[str, ...]
    mode: Literal["sync", "append"]


@dataclass(frozen=True, slots=True)
class TableSyncResult:
    table_name: str
    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    skipped_missing_source: bool = False


@dataclass(frozen=True, slots=True)
class SyncResult:
    mode: Mode
    source_url: str
    target_url: str
    copied_tables: tuple[TableSyncResult, ...]
    skipped_transient_tables: tuple[str, ...]


_SYNC_TABLES: tuple[TableSyncConfig, ...] = (
    TableSyncConfig("dashboard_settings", ("id",), mode="sync"),
    TableSyncConfig("accounts", ("id",), mode="sync"),
    TableSyncConfig("api_firewall_allowlist", ("ip_address",), mode="sync"),
    TableSyncConfig("api_keys", ("id",), mode="sync"),
    TableSyncConfig("api_key_limits", ("id",), mode="sync"),
    TableSyncConfig("api_key_accounts", ("api_key_id", "account_id"), mode="sync"),
    TableSyncConfig("sticky_sessions", ("key", "kind"), mode="sync"),
)

_APPEND_ONLY_TABLES: tuple[TableSyncConfig, ...] = (
    TableSyncConfig("request_logs", ("id",), mode="append"),
    TableSyncConfig("usage_history", ("id",), mode="append"),
    TableSyncConfig("additional_usage_history", ("id",), mode="append"),
    TableSyncConfig("audit_logs", ("id",), mode="append"),
    TableSyncConfig("rate_limit_attempts", ("id",), mode="append"),
)

_FULL_COPY_TABLES: tuple[TableSyncConfig, ...] = _SYNC_TABLES + _APPEND_ONLY_TABLES

_SEQUENCE_TABLES: tuple[tuple[str, str], ...] = (
    ("request_logs", "id"),
    ("usage_history", "id"),
    ("additional_usage_history", "id"),
    ("audit_logs", "id"),
    ("rate_limit_attempts", "id"),
    ("api_key_limits", "id"),
)

_SKIPPED_TRANSIENT_TABLES: tuple[str, ...] = (
    "scheduler_leader",
    "cache_invalidation",
    "bridge_ring_members",
    "api_key_usage_reservations",
    "api_key_usage_reservation_items",
    "http_bridge_sessions",
    "http_bridge_session_aliases",
)


def run_sqlite_to_postgres_sync(
    *,
    source_sqlite: str,
    target_database_url: str,
    mode: Mode,
    batch_size: int = 1000,
) -> SyncResult:
    source_sync_url = _resolve_sqlite_source_sync_url(source_sqlite)
    target_sync_url = _resolve_postgres_target_sync_url(target_database_url)

    source_engine = create_engine(source_sync_url, future=True)
    target_engine = create_engine(target_sync_url, future=True)

    try:
        with source_engine.connect() as source_connection:
            source_metadata = MetaData()
            target_metadata = MetaData()
            source_tables = _reflect_tables(source_connection, source_metadata)

            with target_engine.begin() as target_connection:
                target_tables = _reflect_tables(target_connection, target_metadata)
                if mode == "full-copy":
                    results = _run_full_copy(
                        source_connection,
                        target_connection,
                        source_tables=source_tables,
                        target_tables=target_tables,
                        batch_size=batch_size,
                    )
                else:
                    results = _run_final_sync(
                        source_connection,
                        target_connection,
                        source_tables=source_tables,
                        target_tables=target_tables,
                        batch_size=batch_size,
                    )
                _reset_postgres_sequences(target_connection)
    finally:
        source_engine.dispose()
        target_engine.dispose()

    return SyncResult(
        mode=mode,
        source_url=source_sync_url,
        target_url=target_sync_url,
        copied_tables=tuple(results),
        skipped_transient_tables=_SKIPPED_TRANSIENT_TABLES,
    )


def _run_full_copy(
    source_connection: Connection,
    target_connection: Connection,
    *,
    source_tables: dict[str, Table],
    target_tables: dict[str, Table],
    batch_size: int,
) -> list[TableSyncResult]:
    _clear_full_copy_target_tables(target_connection, target_tables)
    results: list[TableSyncResult] = []
    for config in _FULL_COPY_TABLES:
        source_table = source_tables.get(config.name)
        target_table = _required_target_table(target_tables, config.name)
        if source_table is None:
            results.append(TableSyncResult(table_name=config.name, skipped_missing_source=True))
            continue
        copied = _copy_all_rows(source_connection, target_connection, source_table, target_table, config, batch_size)
        results.append(TableSyncResult(table_name=config.name, inserted=copied))
    return results


def _run_final_sync(
    source_connection: Connection,
    target_connection: Connection,
    *,
    source_tables: dict[str, Table],
    target_tables: dict[str, Table],
    batch_size: int,
) -> list[TableSyncResult]:
    results: list[TableSyncResult] = []

    for config in _SYNC_TABLES:
        source_table = source_tables.get(config.name)
        target_table = _required_target_table(target_tables, config.name)
        if source_table is None:
            deleted = _delete_all_rows(target_connection, target_table)
            results.append(
                TableSyncResult(table_name=config.name, deleted=deleted, skipped_missing_source=True)
            )
            continue
        inserted, updated, deleted = _sync_mutable_table(
            source_connection,
            target_connection,
            source_table,
            target_table,
            config,
            batch_size,
        )
        results.append(
            TableSyncResult(
                table_name=config.name,
                inserted=inserted,
                updated=updated,
                deleted=deleted,
            )
        )

    for config in _APPEND_ONLY_TABLES:
        source_table = source_tables.get(config.name)
        target_table = _required_target_table(target_tables, config.name)
        if source_table is None:
            results.append(TableSyncResult(table_name=config.name, skipped_missing_source=True))
            continue
        inserted = _append_new_rows(
            source_connection,
            target_connection,
            source_table,
            target_table,
            config,
            batch_size,
        )
        results.append(TableSyncResult(table_name=config.name, inserted=inserted))

    return results


def _reflect_tables(connection: Connection, metadata: MetaData) -> dict[str, Table]:
    inspector = inspect(connection)
    tables: dict[str, Table] = {}
    for table_name in inspector.get_table_names():
        tables[table_name] = Table(table_name, metadata, autoload_with=connection)
    return tables


def _required_target_table(target_tables: dict[str, Table], table_name: str) -> Table:
    table = target_tables.get(table_name)
    if table is None:
        raise RuntimeError(f"target PostgreSQL database is missing required table '{table_name}'")
    return table


def _clear_full_copy_target_tables(target_connection: Connection, target_tables: dict[str, Table]) -> None:
    for config in reversed(_FULL_COPY_TABLES):
        target_table = target_tables.get(config.name)
        if target_table is None:
            continue
        target_connection.execute(delete(target_table))


def _copy_all_rows(
    source_connection: Connection,
    target_connection: Connection,
    source_table: Table,
    target_table: Table,
    config: TableSyncConfig,
    batch_size: int,
) -> int:
    inserted = 0
    for rows in _iter_source_batches(source_connection, source_table, target_table, config, batch_size):
        if not rows:
            continue
        target_connection.execute(target_table.insert(), rows)
        inserted += len(rows)
    return inserted


def _sync_mutable_table(
    source_connection: Connection,
    target_connection: Connection,
    source_table: Table,
    target_table: Table,
    config: TableSyncConfig,
    batch_size: int,
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    source_keys: set[object] = set()

    shared_columns = _shared_column_names(source_table, target_table)
    non_pk_columns = [name for name in shared_columns if name not in config.pk_columns]

    for rows in _iter_source_batches(source_connection, source_table, target_table, config, batch_size):
        if not rows:
            continue
        source_keys.update(_row_key(row, config.pk_columns) for row in rows)
        statement = postgresql_insert(target_table).values(rows)
        if non_pk_columns:
            statement = statement.on_conflict_do_update(
                index_elements=[target_table.c[column_name] for column_name in config.pk_columns],
                set_={column_name: statement.excluded[column_name] for column_name in non_pk_columns},
            )
            updated += len(rows)
        else:
            statement = statement.on_conflict_do_nothing(
                index_elements=[target_table.c[column_name] for column_name in config.pk_columns]
            )
        target_connection.execute(statement)
        inserted += len(rows)

    target_keys = _fetch_target_keys(target_connection, target_table, config.pk_columns)
    missing_target_keys = target_keys - source_keys
    deleted = _delete_missing_rows(target_connection, target_table, config.pk_columns, missing_target_keys)
    return inserted, updated, deleted


def _append_new_rows(
    source_connection: Connection,
    target_connection: Connection,
    source_table: Table,
    target_table: Table,
    config: TableSyncConfig,
    batch_size: int,
) -> int:
    pk_column = config.pk_columns[0]
    max_target_pk = target_connection.execute(select(func.max(target_table.c[pk_column]))).scalar_one_or_none()
    statement = select(*(source_table.c[column.name] for column in source_table.columns)).order_by(
        source_table.c[pk_column].asc()
    )
    if max_target_pk is not None:
        statement = statement.where(source_table.c[pk_column] > max_target_pk)

    inserted = 0
    result = source_connection.execution_options(stream_results=True).execute(statement)
    while rows := result.fetchmany(batch_size):
        normalized = [_normalize_row(row._mapping, target_table) for row in rows]
        target_connection.execute(target_table.insert(), normalized)
        inserted += len(normalized)
    return inserted


def _iter_source_batches(
    source_connection: Connection,
    source_table: Table,
    target_table: Table,
    config: TableSyncConfig,
    batch_size: int,
):
    statement = select(*(source_table.c[column.name] for column in source_table.columns)).order_by(
        *(source_table.c[column_name].asc() for column_name in config.pk_columns)
    )
    result = source_connection.execution_options(stream_results=True).execute(statement)
    while rows := result.fetchmany(batch_size):
        yield [_normalize_row(row._mapping, target_table) for row in rows]


def _normalize_row(row_mapping, target_table: Table) -> dict[str, object]:
    shared_columns = _shared_column_names_from_mapping(row_mapping, target_table)
    normalized: dict[str, object] = {}
    for column_name in shared_columns:
        column = target_table.c[column_name]
        value = row_mapping[column_name]
        if isinstance(value, memoryview):
            value = bytes(value)
        if isinstance(column.type, sa.Boolean) and value in (0, 1):
            value = bool(value)
        normalized[column_name] = value
    return normalized


def _shared_column_names(source_table: Table, target_table: Table) -> list[str]:
    source_names = {column.name for column in source_table.columns}
    return [column.name for column in target_table.columns if column.name in source_names]


def _shared_column_names_from_mapping(row_mapping, target_table: Table) -> list[str]:
    source_names = set(row_mapping.keys())
    return [column.name for column in target_table.columns if column.name in source_names]


def _row_key(row: dict[str, object], pk_columns: tuple[str, ...]) -> object:
    if len(pk_columns) == 1:
        return row[pk_columns[0]]
    return tuple(row[column_name] for column_name in pk_columns)


def _fetch_target_keys(target_connection: Connection, target_table: Table, pk_columns: tuple[str, ...]) -> set[object]:
    statement = select(*(target_table.c[column_name] for column_name in pk_columns))
    result = target_connection.execute(statement)
    keys: set[object] = set()
    for row in result:
        if len(pk_columns) == 1:
            keys.add(row[0])
        else:
            keys.add(tuple(row))
    return keys


def _delete_missing_rows(
    target_connection: Connection,
    target_table: Table,
    pk_columns: tuple[str, ...],
    keys: set[object],
) -> int:
    if not keys:
        return 0
    predicate = _pk_in_predicate(target_table, pk_columns, keys)
    result = target_connection.execute(delete(target_table).where(predicate))
    return int(result.rowcount or 0)


def _pk_in_predicate(target_table: Table, pk_columns: tuple[str, ...], keys: set[object]):
    if len(pk_columns) == 1:
        return target_table.c[pk_columns[0]].in_(list(keys))
    return tuple_(*(target_table.c[column_name] for column_name in pk_columns)).in_(list(keys))


def _delete_all_rows(target_connection: Connection, target_table: Table) -> int:
    result = target_connection.execute(delete(target_table))
    return int(result.rowcount or 0)


def _reset_postgres_sequences(target_connection: Connection) -> None:
    for table_name, column_name in _SEQUENCE_TABLES:
        sequence_name = target_connection.execute(
            select(func.pg_get_serial_sequence(table_name, column_name))
        ).scalar_one_or_none()
        if not sequence_name:
            continue
        max_value = target_connection.execute(select(func.max(sa.column(column_name))).select_from(sa.table(table_name))).scalar_one()
        if max_value is None:
            target_connection.execute(select(func.setval(sequence_name, 1, False)))
        else:
            target_connection.execute(select(func.setval(sequence_name, int(max_value), True)))


def _resolve_sqlite_source_sync_url(source_sqlite: str) -> str:
    if source_sqlite.startswith("sqlite://") or source_sqlite.startswith("sqlite+aiosqlite://"):
        sync_url = to_sync_database_url(source_sqlite)
        parsed = make_url(sync_url)
        if parsed.drivername != "sqlite":
            raise RuntimeError("source database must be a SQLite URL")
        return sync_url

    source_path = Path(source_sqlite).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(f"sqlite source database not found: {source_path}")
    return f"sqlite:///{source_path}"


def _resolve_postgres_target_sync_url(target_database_url: str) -> str:
    sync_url = to_sync_database_url(target_database_url)
    parsed = make_url(sync_url)
    if not parsed.drivername.startswith("postgresql"):
        raise RuntimeError("target database must be PostgreSQL")
    return sync_url


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync codex-lb durable data from SQLite to PostgreSQL.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    for mode in ("full-copy", "final-sync"):
        subparser = subparsers.add_parser(mode, help=f"Run {mode} against a SQLite source and PostgreSQL target.")
        subparser.add_argument(
            "--source-sqlite",
            required=True,
            help="SQLite source path or sqlite:// URL.",
        )
        subparser.add_argument(
            "--target-database-url",
            required=True,
            help="Target PostgreSQL database URL. Asyncpg URLs are accepted.",
        )
        subparser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Row batch size for copy operations.",
        )

    return parser.parse_args(args=argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_sqlite_to_postgres_sync(
        source_sqlite=args.source_sqlite,
        target_database_url=args.target_database_url,
        mode=args.mode,
        batch_size=args.batch_size,
    )
    print(
        json.dumps(
            {
                "mode": result.mode,
                "source_url": result.source_url,
                "target_url": result.target_url,
                "skipped_transient_tables": list(result.skipped_transient_tables),
                "tables": [
                    {
                        "table": row.table_name,
                        "inserted": row.inserted,
                        "updated": row.updated,
                        "deleted": row.deleted,
                        "skipped_missing_source": row.skipped_missing_source,
                    }
                    for row in result.copied_tables
                ],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
