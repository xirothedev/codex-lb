import { z } from "zod";

import { ViewerApiKeySchema } from "@/features/viewer/schemas";

export const ViewerLoginRequestSchema = z.object({
  apiKey: z.string().min(1),
});

export const ViewerSessionSchema = z.object({
  authenticated: z.boolean(),
  apiKey: ViewerApiKeySchema.nullable().default(null),
  canRegenerate: z.boolean().default(false),
});

export type ViewerLoginRequest = z.infer<typeof ViewerLoginRequestSchema>;
export type ViewerSession = z.infer<typeof ViewerSessionSchema>;
