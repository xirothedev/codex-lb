import { KeyRound, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ViewerApiKey } from "@/features/viewer/schemas";
import { formatCompactNumber, formatCurrency, formatTimeLong } from "@/utils/formatters";

function formatExpiry(value: string | null): string {
  if (!value) {
    return "Never";
  }
  const parsed = formatTimeLong(value);
  return `${parsed.date} ${parsed.time}`;
}

function formatLimitValue(limitType: string, value: number): string {
  if (limitType === "cost_usd") {
    return `$${(value / 1_000_000).toFixed(2)}`;
  }
  return formatCompactNumber(value);
}

export type ViewerKeyCardProps = {
  apiKey: ViewerApiKey;
  busy: boolean;
  onRegenerate: () => void;
};

export function ViewerKeyCard({ apiKey, busy, onRegenerate }: ViewerKeyCardProps) {
  const usage = apiKey.usageSummary;

  return (
    <section className="rounded-xl border bg-card p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <KeyRound className="h-5 w-5 text-primary" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight">{apiKey.name}</h2>
              <p className="text-sm text-muted-foreground">Your API key summary and request history.</p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetaItem label="Prefix" value={apiKey.keyPrefix} mono />
            <MetaItem label="Masked key" value={apiKey.maskedKey} mono />
            <MetaItem label="Expiry" value={formatExpiry(apiKey.expiresAt)} />
            <MetaItem label="Status" value={apiKey.isActive ? "Active" : "Disabled"} badge={apiKey.isActive ? "active" : "disabled"} />
          </div>
        </div>

        <Button type="button" onClick={onRegenerate} disabled={busy} className="gap-2 self-start">
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Regenerate key
        </Button>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="rounded-lg border bg-muted/20 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Limits</h3>
          <div className="mt-3 space-y-2">
            {apiKey.limits.length === 0 ? (
              <p className="text-sm text-muted-foreground">No explicit limits configured.</p>
            ) : (
              apiKey.limits.map((limit) => (
                <div key={limit.id} className="flex items-center justify-between gap-3 rounded-md border bg-background px-3 py-2 text-sm">
                  <div>
                    <p className="font-medium">{limit.limitType} / {limit.limitWindow}</p>
                    {limit.modelFilter ? <p className="text-xs text-muted-foreground">Model {limit.modelFilter}</p> : null}
                  </div>
                  <p className="font-mono text-xs">
                    {formatLimitValue(limit.limitType, limit.currentValue)} / {formatLimitValue(limit.limitType, limit.maxValue)}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-lg border bg-muted/20 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Policy</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="secondary">{apiKey.allowedModels?.length ? `${apiKey.allowedModels.length} model(s)` : "All models"}</Badge>
            {apiKey.enforcedModel ? <Badge variant="secondary">Forced model: {apiKey.enforcedModel}</Badge> : null}
            {apiKey.enforcedReasoningEffort ? <Badge variant="secondary">Reasoning: {apiKey.enforcedReasoningEffort}</Badge> : null}
            {usage ? <Badge variant="secondary">{formatCurrency(usage.totalCostUsd)} total cost</Badge> : null}
          </div>
        </div>
      </div>
    </section>
  );
}

type MetaItemProps = {
  label: string;
  value: string;
  mono?: boolean;
  badge?: "active" | "disabled";
};

function MetaItem({ label, value, mono = false, badge }: MetaItemProps) {
  return (
    <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
      <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
      {badge ? (
        <div className="mt-1.5">
          <Badge className={badge === "active" ? "bg-emerald-500 text-white" : "bg-zinc-500 text-white"}>{value}</Badge>
        </div>
      ) : (
        <p className={mono ? "mt-1.5 font-mono text-sm" : "mt-1.5 text-sm font-medium"}>{value}</p>
      )}
    </div>
  );
}
