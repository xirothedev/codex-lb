import { z } from "zod";

import { ApiKeySchema } from "@/features/api-keys/schemas";

export const ViewerApiKeySchema = ApiKeySchema.extend({
  maskedKey: z.string(),
});

export const ViewerApiKeyRegenerateResponseSchema = ViewerApiKeySchema.extend({
  key: z.string(),
});

export const ViewerFilterStateSchema = z.object({
  search: z.string(),
  timeframe: z.enum(["all", "1h", "24h", "7d"]),
  modelOptions: z.array(z.string()),
  statuses: z.array(z.string()),
  limit: z.number().int().positive(),
  offset: z.number().int().nonnegative(),
});

export type ViewerApiKey = z.infer<typeof ViewerApiKeySchema>;
export type ViewerApiKeyRegenerateResponse = z.infer<typeof ViewerApiKeyRegenerateResponseSchema>;
export type ViewerFilterState = z.infer<typeof ViewerFilterStateSchema>;
