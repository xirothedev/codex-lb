import { describe, expect, it } from "vitest";

import {
  DashboardSettingsSchema,
  SettingsUpdateRequestSchema,
} from "@/features/settings/schemas";

describe("DashboardSettingsSchema", () => {
  it("parses settings payload", () => {
    const parsed = DashboardSettingsSchema.parse({
      stickyThreadsEnabled: true,
      upstreamStreamTransport: "default",
      preferEarlierResetAccounts: false,
      routingStrategy: "round_robin",
      openaiCacheAffinityMaxAgeSeconds: 300,
      proxyEndpointConcurrencyLimits: {
        responses: 1,
        responses_compact: 2,
        chat_completions: 3,
        transcriptions: 4,
        models: 5,
        usage: 6,
      },
      importWithoutOverwrite: true,
      totpRequiredOnLogin: true,
      totpConfigured: false,
      apiKeyAuthEnabled: true,
    });

    expect(parsed.stickyThreadsEnabled).toBe(true);
    expect(parsed.upstreamStreamTransport).toBe("default");
    expect(parsed.routingStrategy).toBe("round_robin");
    expect(parsed.openaiCacheAffinityMaxAgeSeconds).toBe(300);
    expect(parsed.proxyEndpointConcurrencyLimits.chat_completions).toBe(3);
    expect(parsed.importWithoutOverwrite).toBe(true);
    expect(parsed.apiKeyAuthEnabled).toBe(true);
  });
});

describe("SettingsUpdateRequestSchema", () => {
  it("accepts required fields and optional updates", () => {
    const parsed = SettingsUpdateRequestSchema.parse({
      stickyThreadsEnabled: false,
      upstreamStreamTransport: "websocket",
      preferEarlierResetAccounts: true,
      routingStrategy: "usage_weighted",
      openaiCacheAffinityMaxAgeSeconds: 120,
      proxyEndpointConcurrencyLimits: {
        responses: 1,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
      importWithoutOverwrite: true,
      totpRequiredOnLogin: true,
      apiKeyAuthEnabled: false,
    });

    expect(parsed.openaiCacheAffinityMaxAgeSeconds).toBe(120);
    expect(parsed.upstreamStreamTransport).toBe("websocket");
    expect(parsed.importWithoutOverwrite).toBe(true);
    expect(parsed.routingStrategy).toBe("usage_weighted");
    expect(parsed.totpRequiredOnLogin).toBe(true);
    expect(parsed.apiKeyAuthEnabled).toBe(false);
    expect(parsed.proxyEndpointConcurrencyLimits?.responses).toBe(1);
  });

  it("accepts payload without optional fields", () => {
    const parsed = SettingsUpdateRequestSchema.parse({
      stickyThreadsEnabled: false,
      preferEarlierResetAccounts: true,
      proxyEndpointConcurrencyLimits: {
        responses: 0,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
    });

    expect(parsed.upstreamStreamTransport).toBeUndefined();
    expect(parsed.importWithoutOverwrite).toBeUndefined();
    expect(parsed.totpRequiredOnLogin).toBeUndefined();
    expect(parsed.apiKeyAuthEnabled).toBeUndefined();
    expect(parsed.openaiCacheAffinityMaxAgeSeconds).toBeUndefined();
    expect(parsed.proxyEndpointConcurrencyLimits?.responses_compact).toBe(0);
  });

  it("rejects invalid types", () => {
    const result = SettingsUpdateRequestSchema.safeParse({
      stickyThreadsEnabled: "yes",
      preferEarlierResetAccounts: true,
    });

    expect(result.success).toBe(false);
  });

  it("rejects negative proxy endpoint concurrency limits", () => {
    const result = SettingsUpdateRequestSchema.safeParse({
      stickyThreadsEnabled: false,
      preferEarlierResetAccounts: true,
      proxyEndpointConcurrencyLimits: {
        responses: -1,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
    });

    expect(result.success).toBe(false);
  });
});
