import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { LogOut, BarChart3, Clock, DollarSign, Zap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AccountCostDonut } from "@/features/apis/components/account-cost-donut";
import { ApiTrendChart } from "@/features/apis/components/api-trend-chart";
import {
  getViewerKeyInfo,
  getViewerLogs,
  getViewerTrends,
  getViewerUsage,
  getViewerUsage7Day,
} from "@/features/viewer/api";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";
import { ApiError } from "@/lib/api-client";

function formatTokens(n: number | null): string {
  if (n === null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatCost(n: number): string {
  return `$${n.toFixed(4)}`;
}

function formatLimitValue(limitType: string, value: number): string {
  if (limitType === "cost_usd") {
    return `$${(value / 1_000_000).toFixed(2)}`;
  }
  return formatTokens(value);
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function accumulateData(data: { t: string; v: number }[]): { t: string; v: number }[] {
  let sum = 0;
  return data.map((point) => {
    sum += point.v;
    return { ...point, v: sum };
  });
}

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

function StatusBadge({ status }: { status: string }) {
  const isSuccess = status === "success";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        isSuccess
          ? "bg-emerald-500/10 text-emerald-600"
          : "bg-red-500/10 text-red-600"
      }`}
    >
      {status}
    </span>
  );
}

export function ViewerDashboard() {
  const logout = useViewerStore((s) => s.logout);
  const clearSession = useViewerStore((s) => s.clearSession);
  const loadQuota = useViewerStore((s) => s.loadQuota);
  const quota = useViewerStore((s) => s.quota);
  const [showAccumulated, setShowAccumulated] = useState(false);

  useEffect(() => {
    void loadQuota();
  }, [loadQuota]);

  const { data: keyInfo, error: keyError, isLoading: keyLoading } = useQuery({
    queryKey: ["viewer", "key-info"],
    queryFn: getViewerKeyInfo,
  });

  const { data: usage, error: usageError, isLoading: usageLoading } = useQuery({
    queryKey: ["viewer", "usage"],
    queryFn: () => getViewerUsage(),
  });

  const { data: logs, error: logsError, isLoading: logsLoading } = useQuery({
    queryKey: ["viewer", "logs"],
    queryFn: () => getViewerLogs({ limit: 50 }),
  });

  const { data: trends, error: trendsError, isLoading: trendsLoading } = useQuery({
    queryKey: ["viewer", "trends"],
    queryFn: getViewerTrends,
  });

  const { data: usage7Day, error: usage7DayError, isLoading: usage7DayLoading } = useQuery({
    queryKey: ["viewer", "usage-7d"],
    queryFn: getViewerUsage7Day,
  });

  useEffect(() => {
    if ([keyError, usageError, logsError, trendsError, usage7DayError].some(isUnauthorized)) {
      clearSession();
    }
  }, [clearSession, keyError, logsError, trendsError, usage7DayError, usageError]);

  const chartData = useMemo(() => {
    if (!trends) return null;
    if (!showAccumulated) return trends;
    return {
      cost: accumulateData(trends.cost),
      tokens: accumulateData(trends.tokens),
    };
  }, [showAccumulated, trends]);

  const hasDonutData = Boolean(usage7Day && usage7Day.accountCosts.length > 0);
  const hasTrends = Boolean(trends && (trends.cost.length > 0 || trends.tokens.length > 0));
  const isLoading = keyLoading || usageLoading || logsLoading || trendsLoading || usage7DayLoading;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold tracking-tight">
              {keyInfo?.key_name ?? "API Usage Viewer"}
            </h1>
            {keyInfo ? (
              <StatusBadge status={keyInfo.is_active ? "success" : "inactive"} />
            ) : null}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void logout()}
            className="text-muted-foreground"
          >
            <LogOut className="mr-1.5 size-4" />
            Disconnect
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] px-4 py-6 sm:px-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner />
          </div>
        ) : (
          <>
            {usage ? (
              <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <Zap className="size-3.5" />
                      Total Requests
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-semibold">{usage.total_requests}</div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {usage.successful_requests} ok / {usage.failed_requests} failed
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <BarChart3 className="size-3.5" />
                      Tokens
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-semibold">
                      {formatTokens(usage.total_input_tokens + usage.total_output_tokens)}
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatTokens(usage.total_input_tokens)} in /{" "}
                      {formatTokens(usage.total_output_tokens)} out
                      {usage.total_cached_input_tokens > 0
                        ? ` · ${formatTokens(usage.total_cached_input_tokens)} cached`
                        : ""}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <DollarSign className="size-3.5" />
                      Cost
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-semibold">{formatCost(usage.total_cost_usd)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <Clock className="size-3.5" />
                      Avg Latency
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-semibold">
                      {formatLatency(usage.avg_latency_ms)}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : null}

            {hasDonutData || hasTrends ? (
              <div className="mb-6 rounded-xl border bg-card p-4 lg:flex lg:items-start">
                {hasDonutData && usage7Day ? (
                  <div className={hasTrends ? "lg:w-[25%] lg:shrink-0 lg:pr-4" : "lg:w-full"}>
                    <AccountCostDonut
                      accountCosts={usage7Day.accountCosts}
                      totalCostUsd={usage7Day.totalCostUsd}
                    />
                  </div>
                ) : null}
                {hasTrends ? (
                  <div
                    className={
                      hasDonutData
                        ? "mt-6 border-t pt-4 lg:mt-0 lg:w-[75%] lg:border-t-0 lg:border-l lg:pt-0 lg:pl-6"
                        : "w-full"
                    }
                  >
                    <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="text-sm font-semibold">Usage Trend</h3>
                        <p className="text-xs text-muted-foreground">7-day token and cost activity</p>
                      </div>
                      <div className="flex flex-wrap items-center justify-start gap-3 md:justify-end">
                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-1.5">
                            Tokens
                            <span className="inline-block h-2 w-2 rounded-full bg-chart-2" />
                          </span>
                          <span className="flex items-center gap-1.5">
                            Cost
                            <span className="inline-block h-2 w-2 rounded-full bg-chart-1" />
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 rounded-md border px-2 py-1">
                          <span id="viewer-trend-accumulated-label" className="text-[10px]">
                            Accumulated
                          </span>
                          <Switch
                            size="sm"
                            aria-labelledby="viewer-trend-accumulated-label"
                            checked={showAccumulated}
                            onCheckedChange={setShowAccumulated}
                          />
                        </div>
                      </div>
                    </div>
                    {chartData ? <ApiTrendChart cost={chartData.cost} tokens={chartData.tokens} /> : null}
                  </div>
                ) : null}
              </div>
            ) : null}

            {quota && quota.length > 0 ? (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Quota Limits</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {quota.map((q) => {
                      const percent =
                        q.max_value > 0 ? Math.min(100, (q.current_value / q.max_value) * 100) : 0;
                      return (
                        <div
                          key={`${q.limit_type}-${q.limit_window}-${q.reset_at}`}
                          className="rounded-lg border bg-muted/50 p-3"
                        >
                          <div className="text-xs font-medium text-muted-foreground capitalize">
                            {q.limit_type.replace("_", " ")}
                          </div>
                          <div className="mt-1 text-lg font-semibold">
                            {formatLimitValue(q.limit_type, q.current_value)} /{" "}
                            {formatLimitValue(q.limit_type, q.max_value)}
                          </div>
                          <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary transition-all"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                          <div className="mt-1.5 text-xs text-muted-foreground">
                            {q.limit_window} · resets {format(new Date(q.reset_at), "MMM d, HH:mm")}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            ) : null}

            {logs ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-semibold">Request Logs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-xs">Time</TableHead>
                          <TableHead className="text-xs">Model</TableHead>
                          <TableHead className="text-xs">Status</TableHead>
                          <TableHead className="text-xs text-right">Input</TableHead>
                          <TableHead className="text-xs text-right">Output</TableHead>
                          <TableHead className="text-xs text-right">Cost</TableHead>
                          <TableHead className="text-xs text-right">Latency</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {logs.requests.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                              No requests found
                            </TableCell>
                          </TableRow>
                        ) : (
                          logs.requests.map((r) => (
                            <TableRow key={r.request_id}>
                              <TableCell className="text-xs whitespace-nowrap">
                                {format(new Date(r.requested_at), "MMM d, HH:mm:ss")}
                              </TableCell>
                              <TableCell className="text-xs font-mono">{r.model}</TableCell>
                              <TableCell>
                                <StatusBadge status={r.status} />
                              </TableCell>
                              <TableCell className="text-xs text-right">
                                {formatTokens(r.input_tokens)}
                              </TableCell>
                              <TableCell className="text-xs text-right">
                                {formatTokens(r.output_tokens)}
                              </TableCell>
                              <TableCell className="text-xs text-right">
                                {r.cost_usd !== null ? formatCost(r.cost_usd) : "—"}
                              </TableCell>
                              <TableCell className="text-xs text-right">
                                {formatLatency(r.latency_ms)}
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}
