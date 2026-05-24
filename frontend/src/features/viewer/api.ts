import { z } from "zod";
import { get, post } from "@/lib/api-client";
import {
  ViewerKeyInfoSchema,
  ViewerLoginRequestSchema,
  ViewerLoginResponseSchema,
  ViewerQuotaEntrySchema,
  ViewerRequestLogsResponseSchema,
  ViewerUsageSummarySchema,
} from "@/features/viewer/schemas";
import type { ViewerLoginRequest, ViewerQuotaEntry } from "@/features/viewer/schemas";

const BASE = "/viewer";

export function loginViewer(payload: ViewerLoginRequest) {
  const validated = ViewerLoginRequestSchema.parse(payload);
  return post(`${BASE}/auth/login`, ViewerLoginResponseSchema, {
    body: validated,
  });
}

export function logoutViewer() {
  return post(`${BASE}/auth/logout`, null as never);
}

export function getViewerLogs(params?: { limit?: number; cursor?: string }) {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.cursor) searchParams.set("cursor", params.cursor);
  const qs = searchParams.toString();
  return get(`${BASE}/logs${qs ? `?${qs}` : ""}`, ViewerRequestLogsResponseSchema);
}

export function getViewerUsage(since?: string) {
  const qs = since ? `?since=${encodeURIComponent(since)}` : "";
  return get(`${BASE}/usage${qs}`, ViewerUsageSummarySchema);
}

export function getViewerKeyInfo() {
  return get(`${BASE}/key-info`, ViewerKeyInfoSchema);
}

export function getViewerQuota(): Promise<ViewerQuotaEntry[]> {
  return get(`${BASE}/quota`, z.array(ViewerQuotaEntrySchema));
}
