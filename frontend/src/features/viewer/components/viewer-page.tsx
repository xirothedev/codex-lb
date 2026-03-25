import { useMemo, useState } from "react";
import { Activity, Coins, Database, DollarSign, KeyRound } from "lucide-react";

import { AlertMessage } from "@/components/alert-message";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { EmptyState } from "@/components/empty-state";
import { ApiKeyCreatedDialog } from "@/features/api-keys/components/api-key-created-dialog";
import { StatsGrid } from "@/features/dashboard/components/stats-grid";
import { ViewerKeyCard } from "@/features/viewer/components/viewer-key-card";
import { useViewerPortal } from "@/features/viewer/hooks/use-viewer-portal";
import type { DashboardStat } from "@/features/dashboard/utils";
import { formatCompactNumber, formatCurrency } from "@/utils/formatters";
import { getErrorMessageOrNull } from "@/utils/errors";

export function ViewerPage() {
  const { apiKeyQuery, regenerateMutation } = useViewerPortal();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  const apiKey = apiKeyQuery.data;

  const stats = useMemo<DashboardStat[]>(() => {
    if (!apiKey?.usageSummary) {
      return [];
    }
    return [
      {
        label: "Requests",
        value: formatCompactNumber(apiKey.usageSummary.requestCount),
        meta: "Total matched requests",
        icon: Activity,
        trend: [],
        trendColor: "#3b82f6",
      },
      {
        label: "Tokens",
        value: formatCompactNumber(apiKey.usageSummary.totalTokens),
        meta: "Across this API key",
        icon: Coins,
        trend: [],
        trendColor: "#8b5cf6",
      },
      {
        label: "Cached",
        value: formatCompactNumber(apiKey.usageSummary.cachedInputTokens),
        meta: "Cached input tokens",
        icon: Database,
        trend: [],
        trendColor: "#10b981",
      },
      {
        label: "Cost",
        value: formatCurrency(apiKey.usageSummary.totalCostUsd),
        meta: "Estimated total cost",
        icon: DollarSign,
        trend: [],
        trendColor: "#f59e0b",
      },
    ];
  }, [apiKey]);

  const errorMessage =
    getErrorMessageOrNull(apiKeyQuery.error) ||
    getErrorMessageOrNull(regenerateMutation.error);

  const handleRegenerate = async () => {
    const response = await regenerateMutation.mutateAsync();
    setCreatedKey(response.key);
    setConfirmOpen(false);
  };

  return (
    <div className="animate-fade-in-up space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Quota</h1>
        <p className="mt-1 text-sm text-muted-foreground">View limits, policy, and regenerate your API key.</p>
      </div>

      {errorMessage ? <AlertMessage variant="error">{errorMessage}</AlertMessage> : null}

      {!apiKey ? (
        <EmptyState icon={KeyRound} title="Loading your API key" description="Fetching viewer metadata..." />
      ) : (
        <>
          <ViewerKeyCard apiKey={apiKey} busy={regenerateMutation.isPending} onRegenerate={() => setConfirmOpen(true)} />
          {stats.length > 0 ? <StatsGrid stats={stats} /> : null}
        </>
      )}

      <ConfirmDialog
        open={confirmOpen}
        title="Regenerate API key?"
        description="This will immediately invalidate the current key and reveal the new key exactly once."
        confirmLabel={regenerateMutation.isPending ? "Regenerating..." : "Regenerate"}
        onOpenChange={setConfirmOpen}
        onConfirm={() => {
          void handleRegenerate();
        }}
      />

      <ApiKeyCreatedDialog open={createdKey !== null} apiKey={createdKey} onOpenChange={(open) => !open && setCreatedKey(null)} />
    </div>
  );
}
