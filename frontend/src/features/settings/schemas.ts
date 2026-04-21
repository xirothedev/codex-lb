import { z } from "zod";

export const RoutingStrategySchema = z.enum(["usage_weighted", "round_robin", "capacity_weighted"]);
export const UpstreamStreamTransportSchema = z.enum(["default", "auto", "http", "websocket"]);
export const ProxyEndpointConcurrencyLimitsSchema = z.object({
  responses: z.number().int().nonnegative(),
  responses_compact: z.number().int().nonnegative(),
  chat_completions: z.number().int().nonnegative(),
  transcriptions: z.number().int().nonnegative(),
  models: z.number().int().nonnegative(),
  usage: z.number().int().nonnegative(),
});

export const DashboardSettingsSchema = z.object({
  stickyThreadsEnabled: z.boolean(),
  upstreamStreamTransport: UpstreamStreamTransportSchema,
  preferEarlierResetAccounts: z.boolean(),
  routingStrategy: RoutingStrategySchema,
  openaiCacheAffinityMaxAgeSeconds: z.number().int().positive(),
  proxyEndpointConcurrencyLimits: ProxyEndpointConcurrencyLimitsSchema,
  importWithoutOverwrite: z.boolean(),
  totpRequiredOnLogin: z.boolean(),
  totpConfigured: z.boolean(),
  apiKeyAuthEnabled: z.boolean(),
});

export const SettingsUpdateRequestSchema = z.object({
  stickyThreadsEnabled: z.boolean(),
  upstreamStreamTransport: UpstreamStreamTransportSchema.optional(),
  preferEarlierResetAccounts: z.boolean(),
  routingStrategy: RoutingStrategySchema.optional(),
  openaiCacheAffinityMaxAgeSeconds: z.number().int().positive().optional(),
  proxyEndpointConcurrencyLimits: ProxyEndpointConcurrencyLimitsSchema.optional(),
  importWithoutOverwrite: z.boolean().optional(),
  totpRequiredOnLogin: z.boolean().optional(),
  apiKeyAuthEnabled: z.boolean().optional(),
});

export type DashboardSettings = z.infer<typeof DashboardSettingsSchema>;
export type ProxyEndpointConcurrencyLimits = z.infer<typeof ProxyEndpointConcurrencyLimitsSchema>;
export type SettingsUpdateRequest = z.infer<typeof SettingsUpdateRequestSchema>;
