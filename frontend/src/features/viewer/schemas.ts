import { z } from "zod";

export const ViewerLoginRequestSchema = z.object({
  api_key: z.string().min(1),
});

export const ViewerLoginResponseSchema = z.object({
  token: z.string(),
  expires_in: z.number(),
});

export const ViewerRequestLogEntrySchema = z.object({
  requested_at: z.string(),
  request_id: z.string(),
  model: z.string(),
  status: z.string(),
  input_tokens: z.number().nullable(),
  output_tokens: z.number().nullable(),
  cached_input_tokens: z.number().nullable(),
  cost_usd: z.number().nullable(),
  latency_ms: z.number().nullable(),
  latency_first_token_ms: z.number().nullable(),
});

export const ViewerRequestLogsResponseSchema = z.object({
  requests: z.array(ViewerRequestLogEntrySchema),
  total: z.number(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  total_pages: z.number().int().nonnegative(),
  has_more: z.boolean(),
  has_next: z.boolean(),
  has_previous: z.boolean(),
});

export const ViewerUsageSummarySchema = z.object({
  total_requests: z.number(),
  successful_requests: z.number(),
  failed_requests: z.number(),
  total_input_tokens: z.number(),
  total_output_tokens: z.number(),
  total_cached_input_tokens: z.number(),
  total_cost_usd: z.number(),
  avg_latency_ms: z.number().nullable(),
});

export const ViewerKeyInfoSchema = z.object({
  key_id: z.string(),
  key_name: z.string(),
  is_active: z.boolean(),
});

export const ViewerQuotaEntrySchema = z.object({
  limit_type: z.string(),
  limit_window: z.string(),
  max_value: z.number(),
  current_value: z.number(),
  reset_at: z.string(),
});

export type ViewerLoginRequest = z.infer<typeof ViewerLoginRequestSchema>;
export type ViewerLoginResponse = z.infer<typeof ViewerLoginResponseSchema>;
export type ViewerRequestLogEntry = z.infer<typeof ViewerRequestLogEntrySchema>;
export type ViewerRequestLogsResponse = z.infer<typeof ViewerRequestLogsResponseSchema>;
export type ViewerUsageSummary = z.infer<typeof ViewerUsageSummarySchema>;
export type ViewerKeyInfo = z.infer<typeof ViewerKeyInfoSchema>;
export type ViewerQuotaEntry = z.infer<typeof ViewerQuotaEntrySchema>;
