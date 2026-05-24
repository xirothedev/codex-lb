import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { LogOut, BarChart3, Clock, DollarSign, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getViewerKeyInfo, getViewerLogs, getViewerUsage } from "@/features/viewer/api";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";

function formatTokens(n: number | null): string {
  if (n === null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatCost(n: number): string {
  return `$${n.toFixed(4)}`;
}

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
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

  const { data: keyInfo, isLoading: keyLoading } = useQuery({
    queryKey: ["viewer", "key-info"],
    queryFn: getViewerKeyInfo,
  });

  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ["viewer", "usage"],
    queryFn: () => getViewerUsage(),
  });

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ["viewer", "logs"],
    queryFn: () => getViewerLogs({ limit: 50 }),
  });

  const isLoading = keyLoading || usageLoading || logsLoading;

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
