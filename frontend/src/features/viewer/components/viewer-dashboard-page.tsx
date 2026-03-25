import { useMemo } from "react";
import { Activity, Coins, Database, DollarSign } from "lucide-react";

import { AlertMessage } from "@/components/alert-message";
import { RecentRequestsTable } from "@/features/dashboard/components/recent-requests-table";
import type { MultiSelectOption } from "@/features/dashboard/components/filters/multi-select-filter";
import { StatsGrid } from "@/features/dashboard/components/stats-grid";
import { ViewerRequestFilters } from "@/features/viewer/components/viewer-request-filters";
import { useViewerPortal } from "@/features/viewer/hooks/use-viewer-portal";
import { useViewerRequestLogs } from "@/features/viewer/hooks/use-viewer-request-logs";
import type { DashboardStat } from "@/features/dashboard/utils";
import { REQUEST_STATUS_LABELS } from "@/utils/constants";
import { formatCompactNumber, formatCurrency, formatSlug } from "@/utils/formatters";
import { getErrorMessageOrNull } from "@/utils/errors";

const MODEL_OPTION_DELIMITER = ":::";

export function ViewerDashboardPage() {
  const { apiKeyQuery } = useViewerPortal();
  const { filters, logsQuery, optionsQuery, updateFilters, resetFilters } = useViewerRequestLogs();

  const apiKey = apiKeyQuery.data;
  const logPage = logsQuery.data;
  const options = optionsQuery.data;
  const usageSummary = apiKey?.usageSummary;

  const stats = useMemo<DashboardStat[]>(() => {
    return [
      {
        label: "Requests",
        value: formatCompactNumber(usageSummary?.requestCount ?? 0),
        meta: "Total matched requests",
        icon: Activity,
        trend: [],
        trendColor: "#3b82f6",
      },
      {
        label: "Tokens",
        value: formatCompactNumber(usageSummary?.totalTokens ?? 0),
        meta: "Across this API key",
        icon: Coins,
        trend: [],
        trendColor: "#8b5cf6",
      },
      {
        label: "Cached",
        value: formatCompactNumber(usageSummary?.cachedInputTokens ?? 0),
        meta: "Cached input tokens",
        icon: Database,
        trend: [],
        trendColor: "#10b981",
      },
      {
        label: "Cost",
        value: formatCurrency(usageSummary?.totalCostUsd ?? 0),
        meta: "Estimated total cost",
        icon: DollarSign,
        trend: [],
        trendColor: "#f59e0b",
      },
    ];
  }, [usageSummary]);

  const modelOptions = useMemo<MultiSelectOption[]>(
    () =>
      (options?.modelOptions ?? []).map((option) => ({
        value: `${option.model}${MODEL_OPTION_DELIMITER}${option.reasoningEffort ?? ""}`,
        label: option.reasoningEffort ? `${option.model} (${option.reasoningEffort})` : option.model,
      })),
    [options?.modelOptions],
  );

  const statusOptions = useMemo<MultiSelectOption[]>(
    () =>
      (options?.statuses ?? []).map((status) => ({
        value: status,
        label: REQUEST_STATUS_LABELS[status] ?? formatSlug(status),
      })),
    [options?.statuses],
  );

  const errorMessage =
    getErrorMessageOrNull(apiKeyQuery.error) ||
    getErrorMessageOrNull(logsQuery.error) ||
    getErrorMessageOrNull(optionsQuery.error);

  return (
    <div className="animate-fade-in-up space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">Overview and recent requests for your API key.</p>
      </div>

      {errorMessage ? <AlertMessage variant="error">{errorMessage}</AlertMessage> : null}

      <StatsGrid stats={stats} />

      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <h2 className="text-[13px] font-medium uppercase tracking-wider text-muted-foreground">Request Logs</h2>
          <div className="h-px flex-1 bg-border" />
        </div>
        <ViewerRequestFilters
          filters={filters}
          modelOptions={modelOptions}
          statusOptions={statusOptions}
          onSearchChange={(value) => updateFilters({ search: value, offset: 0 })}
          onTimeframeChange={(value) => updateFilters({ timeframe: value, offset: 0 })}
          onModelChange={(values) => updateFilters({ modelOptions: values, offset: 0 })}
          onStatusChange={(values) => updateFilters({ statuses: values, offset: 0 })}
          onReset={resetFilters}
        />
        <RecentRequestsTable
          requests={logPage?.requests ?? []}
          accounts={[]}
          total={logPage?.total ?? 0}
          limit={filters.limit}
          offset={filters.offset}
          hasMore={logPage?.hasMore ?? false}
          onLimitChange={(limit) => updateFilters({ limit, offset: 0 })}
          onOffsetChange={(offset) => updateFilters({ offset })}
          showAccountColumn={false}
          showApiKeyColumn={false}
        />
      </section>
    </div>
  );
}
