import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import {
  getViewerRequestLogOptions,
  getViewerRequestLogs,
  type ViewerRequestLogFacetFilters,
  type ViewerRequestLogsListFilters,
} from "@/features/viewer/api";
import { ViewerFilterStateSchema, type ViewerFilterState } from "@/features/viewer/schemas";

const DEFAULT_FILTER_STATE: ViewerFilterState = {
  search: "",
  timeframe: "all",
  modelOptions: [],
  statuses: [],
  limit: 25,
  offset: 0,
};

function parseNumber(value: string | null, fallback: number): number {
  if (value === null) {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseFilterState(params: URLSearchParams): ViewerFilterState {
  const candidate = {
    search: params.get("search") ?? "",
    timeframe: params.get("timeframe") ?? "all",
    modelOptions: params.getAll("modelOption"),
    statuses: params.getAll("status"),
    limit: parseNumber(params.get("limit"), DEFAULT_FILTER_STATE.limit),
    offset: parseNumber(params.get("offset"), DEFAULT_FILTER_STATE.offset),
  };
  const parsed = ViewerFilterStateSchema.safeParse(candidate);
  if (parsed.success) {
    return parsed.data;
  }
  return DEFAULT_FILTER_STATE;
}

function writeFilterState(state: ViewerFilterState): URLSearchParams {
  const params = new URLSearchParams();
  if (state.search) {
    params.set("search", state.search);
  }
  if (state.timeframe !== "all") {
    params.set("timeframe", state.timeframe);
  }
  for (const value of state.modelOptions) {
    params.append("modelOption", value);
  }
  for (const value of state.statuses) {
    params.append("status", value);
  }
  params.set("limit", String(state.limit));
  params.set("offset", String(state.offset));
  return params;
}

function timeframeToSinceIso(timeframe: ViewerFilterState["timeframe"]): string | undefined {
  if (timeframe === "all") {
    return undefined;
  }
  const now = Date.now();
  const lookup: Record<Exclude<ViewerFilterState["timeframe"], "all">, number> = {
    "1h": 60 * 60 * 1000,
    "24h": 24 * 60 * 60 * 1000,
    "7d": 7 * 24 * 60 * 60 * 1000,
  };
  return new Date(now - lookup[timeframe]).toISOString();
}

export function useViewerRequestLogs() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(() => parseFilterState(searchParams), [searchParams]);
  const since = useMemo(() => timeframeToSinceIso(filters.timeframe), [filters.timeframe]);
  const listFilters = useMemo<ViewerRequestLogsListFilters>(
    () => ({
      search: filters.search || undefined,
      limit: filters.limit,
      offset: filters.offset,
      statuses: filters.statuses,
      modelOptions: filters.modelOptions,
      since,
    }),
    [filters, since],
  );
  const facetFilters = useMemo<ViewerRequestLogFacetFilters>(
    () => ({
      since,
      modelOptions: filters.modelOptions,
    }),
    [filters.modelOptions, since],
  );

  const logsQuery = useQuery({
    queryKey: ["viewer", "request-logs", listFilters],
    queryFn: () => getViewerRequestLogs(listFilters),
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    placeholderData: keepPreviousData,
  });

  const optionsQuery = useQuery({
    queryKey: ["viewer", "request-log-options", facetFilters],
    queryFn: () => getViewerRequestLogOptions(facetFilters),
    staleTime: 30_000,
  });

  const updateFilters = (patch: Partial<ViewerFilterState>) => {
    const next: ViewerFilterState = {
      ...filters,
      ...patch,
      offset: patch.offset ?? (patch.limit && patch.limit !== filters.limit ? 0 : filters.offset),
    };
    setSearchParams(writeFilterState(next), { replace: true });
  };

  const resetFilters = () => {
    setSearchParams(writeFilterState(DEFAULT_FILTER_STATE), { replace: true });
  };

  return {
    filters,
    logsQuery,
    optionsQuery,
    updateFilters,
    resetFilters,
  };
}
