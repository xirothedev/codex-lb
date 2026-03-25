import { get, post } from "@/lib/api-client";
import {
  RequestLogFilterOptionsSchema,
  RequestLogsResponseSchema,
} from "@/features/dashboard/schemas";
import {
  ViewerApiKeyRegenerateResponseSchema,
  ViewerApiKeySchema,
} from "@/features/viewer/schemas";

const VIEWER_BASE_PATH = "/api/viewer";

export type ViewerRequestLogsListFilters = {
  limit?: number;
  offset?: number;
  search?: string;
  statuses?: string[];
  modelOptions?: string[];
  since?: string;
  until?: string;
};

export type ViewerRequestLogFacetFilters = {
  since?: string;
  until?: string;
  modelOptions?: string[];
};

function appendMany(params: URLSearchParams, key: string, values?: string[]): void {
  if (!values || values.length === 0) {
    return;
  }
  for (const value of values) {
    if (value) {
      params.append(key, value);
    }
  }
}

export function getViewerApiKey() {
  return get(`${VIEWER_BASE_PATH}/api-key`, ViewerApiKeySchema);
}

export function regenerateViewerApiKey() {
  return post(`${VIEWER_BASE_PATH}/api-key/regenerate`, ViewerApiKeyRegenerateResponseSchema);
}

export function getViewerRequestLogs(params: ViewerRequestLogsListFilters = {}) {
  const query = new URLSearchParams();
  if (typeof params.limit === "number") {
    query.set("limit", String(params.limit));
  }
  if (typeof params.offset === "number") {
    query.set("offset", String(params.offset));
  }
  if (params.search) {
    query.set("search", params.search);
  }
  appendMany(query, "status", params.statuses);
  appendMany(query, "modelOption", params.modelOptions);
  if (params.since) {
    query.set("since", params.since);
  }
  if (params.until) {
    query.set("until", params.until);
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return get(`${VIEWER_BASE_PATH}/request-logs${suffix}`, RequestLogsResponseSchema);
}

export function getViewerRequestLogOptions(params: ViewerRequestLogFacetFilters = {}) {
  const query = new URLSearchParams();
  if (params.since) {
    query.set("since", params.since);
  }
  if (params.until) {
    query.set("until", params.until);
  }
  appendMany(query, "modelOption", params.modelOptions);
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return get(`${VIEWER_BASE_PATH}/request-logs/options${suffix}`, RequestLogFilterOptionsSchema);
}
