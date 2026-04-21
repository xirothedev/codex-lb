import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RoutingSettings } from "@/features/settings/components/routing-settings";
import type { DashboardSettings } from "@/features/settings/schemas";

const BASE_SETTINGS: DashboardSettings = {
  stickyThreadsEnabled: false,
  upstreamStreamTransport: "default",
  preferEarlierResetAccounts: true,
  routingStrategy: "usage_weighted",
  openaiCacheAffinityMaxAgeSeconds: 300,
  proxyEndpointConcurrencyLimits: {
    responses: 0,
    responses_compact: 0,
    chat_completions: 0,
    transcriptions: 0,
    models: 0,
    usage: 0,
  },
  importWithoutOverwrite: false,
  totpRequiredOnLogin: false,
  totpConfigured: false,
  apiKeyAuthEnabled: true,
};

describe("RoutingSettings", () => {
  it("saves a new prompt-cache affinity ttl from the button and Enter key", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <RoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />,
    );

    const ttlInput = screen.getByRole("spinbutton");
    await user.clear(ttlInput);
    await user.type(ttlInput, "180");
    await user.click(screen.getByRole("button", { name: "Save TTL" }));

    expect(onSave).toHaveBeenCalledWith({
      stickyThreadsEnabled: false,
      upstreamStreamTransport: "default",
      preferEarlierResetAccounts: true,
      routingStrategy: "usage_weighted",
      openaiCacheAffinityMaxAgeSeconds: 180,
      proxyEndpointConcurrencyLimits: {
        responses: 0,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
      importWithoutOverwrite: false,
      totpRequiredOnLogin: false,
      apiKeyAuthEnabled: true,
    });

    rerender(
      <RoutingSettings
        settings={{ ...BASE_SETTINGS, openaiCacheAffinityMaxAgeSeconds: 180 }}
        busy={false}
        onSave={onSave}
      />,
    );

    await user.clear(screen.getByRole("spinbutton"));
    await user.type(screen.getByRole("spinbutton"), "240{Enter}");

    expect(onSave).toHaveBeenLastCalledWith({
      stickyThreadsEnabled: false,
      upstreamStreamTransport: "default",
      preferEarlierResetAccounts: true,
      routingStrategy: "usage_weighted",
      openaiCacheAffinityMaxAgeSeconds: 240,
      proxyEndpointConcurrencyLimits: {
        responses: 0,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
      importWithoutOverwrite: false,
      totpRequiredOnLogin: false,
      apiKeyAuthEnabled: true,
    });
  });

  it("disables ttl save for invalid values and saves sticky-thread toggles", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<RoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />);

    const ttlInput = screen.getByRole("spinbutton");
    const saveButton = screen.getByRole("button", { name: "Save TTL" });
    expect(saveButton).toBeDisabled();

    await user.clear(ttlInput);
    await user.type(ttlInput, "0");
    expect(saveButton).toBeDisabled();

    await user.click(screen.getAllByRole("switch")[0]!);

    expect(onSave).toHaveBeenCalledWith({
      stickyThreadsEnabled: true,
      upstreamStreamTransport: "default",
      preferEarlierResetAccounts: true,
      routingStrategy: "usage_weighted",
      openaiCacheAffinityMaxAgeSeconds: 300,
      proxyEndpointConcurrencyLimits: {
        responses: 0,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
      importWithoutOverwrite: false,
      totpRequiredOnLogin: false,
      apiKeyAuthEnabled: true,
    });
  });

  it("saves proxy endpoint concurrency limits as a batch", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<RoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />);

    const responsesInput = screen.getByLabelText("Responses");
    const saveButton = screen.getByRole("button", { name: "Save concurrency limits" });

    expect(saveButton).toBeDisabled();

    await user.clear(responsesInput);
    await user.type(responsesInput, "2");
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalledWith({
      stickyThreadsEnabled: false,
      upstreamStreamTransport: "default",
      preferEarlierResetAccounts: true,
      routingStrategy: "usage_weighted",
      openaiCacheAffinityMaxAgeSeconds: 300,
      proxyEndpointConcurrencyLimits: {
        responses: 2,
        responses_compact: 0,
        chat_completions: 0,
        transcriptions: 0,
        models: 0,
        usage: 0,
      },
      importWithoutOverwrite: false,
      totpRequiredOnLogin: false,
      apiKeyAuthEnabled: true,
    });
  });

  it("preserves unsaved ttl and concurrency drafts across unrelated settings refreshes", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(
      <RoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />,
    );

    const ttlInput = screen.getByRole("spinbutton");
    const responsesInput = screen.getByLabelText("Responses");

    await user.clear(ttlInput);
    await user.type(ttlInput, "180");
    await user.clear(responsesInput);
    await user.type(responsesInput, "2");

    rerender(
      <RoutingSettings
        settings={{
          ...BASE_SETTINGS,
          stickyThreadsEnabled: true,
          routingStrategy: "round_robin",
        }}
        busy={false}
        onSave={onSave}
      />,
    );

    expect(screen.getByRole("spinbutton")).toHaveValue(180);
    expect(screen.getByLabelText("Responses")).toHaveValue("2");
    expect(screen.getByRole("button", { name: "Save TTL" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Save concurrency limits" })).toBeEnabled();
  });

  it("shows the configured upstream transport", () => {
    render(<RoutingSettings settings={BASE_SETTINGS} busy={false} onSave={vi.fn().mockResolvedValue(undefined)} />);

    expect(screen.getByText("Upstream stream transport")).toBeInTheDocument();
    expect(screen.getByText("Server default")).toBeInTheDocument();
  });
});
