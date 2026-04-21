import { useState } from "react";
import { Route } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { buildSettingsUpdateRequest } from "@/features/settings/payload";
import type {
  DashboardSettings,
  ProxyEndpointConcurrencyLimits,
  SettingsUpdateRequest,
} from "@/features/settings/schemas";

const CONCURRENCY_LIMIT_FIELDS: Array<{
  key: keyof ProxyEndpointConcurrencyLimits;
  label: string;
}> = [
  { key: "responses", label: "Responses" },
  { key: "responses_compact", label: "Responses compact" },
  { key: "chat_completions", label: "Chat completions" },
  { key: "transcriptions", label: "Transcriptions" },
  { key: "models", label: "Models" },
  { key: "usage", label: "Usage" },
];

export type RoutingSettingsProps = {
  settings: DashboardSettings;
  busy: boolean;
  onSave: (payload: SettingsUpdateRequest) => Promise<void>;
};

export function RoutingSettings({ settings, busy, onSave }: RoutingSettingsProps) {
  const [cacheAffinityTtl, setCacheAffinityTtl] = useState(
    String(settings.openaiCacheAffinityMaxAgeSeconds),
  );
  const [concurrencyLimits, setConcurrencyLimits] = useState<Record<keyof ProxyEndpointConcurrencyLimits, string>>(
    () => buildConcurrencyLimitInputs(settings.proxyEndpointConcurrencyLimits),
  );

  const save = (patch: Partial<SettingsUpdateRequest>) =>
    void onSave(buildSettingsUpdateRequest(settings, patch));

  const parsedCacheAffinityTtl = Number.parseInt(cacheAffinityTtl, 10);
  const cacheAffinityTtlValid = Number.isInteger(parsedCacheAffinityTtl) && parsedCacheAffinityTtl > 0;
  const cacheAffinityTtlChanged =
    cacheAffinityTtlValid && parsedCacheAffinityTtl !== settings.openaiCacheAffinityMaxAgeSeconds;
  const parsedConcurrencyLimits = parseConcurrencyLimitInputs(concurrencyLimits);
  const concurrencyLimitsChanged =
    parsedConcurrencyLimits !== null &&
    CONCURRENCY_LIMIT_FIELDS.some(
      ({ key }) => parsedConcurrencyLimits[key] !== settings.proxyEndpointConcurrencyLimits[key],
    );

  return (
    <section className="rounded-xl border bg-card p-5">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Route className="h-4 w-4 text-primary" aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Routing</h3>
              <p className="text-xs text-muted-foreground">Control how requests are distributed across accounts.</p>
            </div>
          </div>
        </div>

        <div className="divide-y rounded-lg border">
          <div className="flex items-center justify-between gap-4 p-3">
            <div>
              <p className="text-sm font-medium">Upstream stream transport</p>
              <p className="text-xs text-muted-foreground">
                Choose how `codex-lb` connects upstream for streaming responses.
              </p>
            </div>
            <Select
              value={settings.upstreamStreamTransport}
              onValueChange={(value) =>
                save({ upstreamStreamTransport: value as "default" | "auto" | "http" | "websocket" })
              }
            >
              <SelectTrigger className="h-8 w-44 text-xs" disabled={busy}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="end">
                <SelectItem value="default">Server default</SelectItem>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="http">Responses</SelectItem>
                <SelectItem value="websocket">WebSockets</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between gap-4 p-3">
            <div>
              <p className="text-sm font-medium">Routing strategy</p>
              <p className="text-xs text-muted-foreground">Choose how requests are distributed across accounts.</p>
            </div>
            <Select
              value={settings.routingStrategy}
              onValueChange={(value) => save({ routingStrategy: value as "usage_weighted" | "round_robin" | "capacity_weighted" })}
            >
              <SelectTrigger className="h-8 w-44 text-xs" disabled={busy}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="end">
                <SelectItem value="capacity_weighted">Capacity weighted</SelectItem>
                <SelectItem value="usage_weighted">Usage weighted</SelectItem>
                <SelectItem value="round_robin">Round robin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between p-3">
            <div>
              <p className="text-sm font-medium">Sticky threads</p>
              <p className="text-xs text-muted-foreground">Keep related requests on the same account.</p>
            </div>
            <Switch
              checked={settings.stickyThreadsEnabled}
              disabled={busy}
              onCheckedChange={(checked) => save({ stickyThreadsEnabled: checked })}
            />
          </div>

          <div className="flex items-center justify-between p-3">
            <div>
              <p className="text-sm font-medium">Prefer earlier reset</p>
              <p className="text-xs text-muted-foreground">Bias traffic to accounts with earlier quota reset.</p>
            </div>
            <Switch
              checked={settings.preferEarlierResetAccounts}
              disabled={busy}
              onCheckedChange={(checked) => save({ preferEarlierResetAccounts: checked })}
            />
          </div>

          <div className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium">Prompt-cache affinity TTL</p>
              <p className="text-xs text-muted-foreground">
                Keep OpenAI-style prompt-cache mappings warm for a bounded number of seconds.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1}
                step={1}
                inputMode="numeric"
                value={cacheAffinityTtl}
                disabled={busy}
                onChange={(event) => setCacheAffinityTtl(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && cacheAffinityTtlChanged) {
                    void save({ openaiCacheAffinityMaxAgeSeconds: parsedCacheAffinityTtl });
                  }
                }}
                className="h-8 w-28 text-xs"
              />
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-8 text-xs"
                disabled={busy || !cacheAffinityTtlChanged}
                onClick={() => void save({ openaiCacheAffinityMaxAgeSeconds: parsedCacheAffinityTtl })}
              >
                Save TTL
              </Button>
            </div>
          </div>

          <div className="flex flex-col gap-3 p-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">Proxy endpoint concurrency limits</p>
              <p className="text-xs text-muted-foreground">
                Limit in-flight requests per proxy family on this replica. Set `0` to keep a family unlimited.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {CONCURRENCY_LIMIT_FIELDS.map(({ key, label }) => {
                const inputId = `proxy-endpoint-limit-${key}`;
                return (
                  <div key={key} className="space-y-1.5">
                    <label htmlFor={inputId} className="text-xs font-medium text-foreground">
                      {label}
                    </label>
                    <Input
                      id={inputId}
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={concurrencyLimits[key]}
                      disabled={busy}
                      onChange={(event) =>
                        setConcurrencyLimits((current) => ({
                          ...current,
                          [key]: event.target.value,
                        }))
                      }
                      className="h-8 text-xs"
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-end">
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-8 text-xs"
                disabled={busy || parsedConcurrencyLimits === null || !concurrencyLimitsChanged}
                onClick={() => {
                  if (parsedConcurrencyLimits !== null) {
                    void save({ proxyEndpointConcurrencyLimits: parsedConcurrencyLimits });
                  }
                }}
              >
                Save concurrency limits
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function buildConcurrencyLimitInputs(
  limits: ProxyEndpointConcurrencyLimits,
): Record<keyof ProxyEndpointConcurrencyLimits, string> {
  return {
    responses: String(limits.responses),
    responses_compact: String(limits.responses_compact),
    chat_completions: String(limits.chat_completions),
    transcriptions: String(limits.transcriptions),
    models: String(limits.models),
    usage: String(limits.usage),
  };
}

function parseConcurrencyLimitInputs(
  limits: Record<keyof ProxyEndpointConcurrencyLimits, string>,
): ProxyEndpointConcurrencyLimits | null {
  const parsedEntries = CONCURRENCY_LIMIT_FIELDS.map(({ key }) => {
    const value = limits[key].trim();
    if (!/^\d+$/.test(value)) {
      return null;
    }
    return [key, Number.parseInt(value, 10)] as const;
  });
  if (parsedEntries.some((entry) => entry === null)) {
    return null;
  }

  return Object.fromEntries(parsedEntries) as ProxyEndpointConcurrencyLimits;
}
