import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import {
  getViewerKeyInfo,
  getViewerLogs,
  getViewerQuota,
  getViewerTrends,
  getViewerUsage,
  getViewerUsage7Day,
  loginViewer,
  logoutViewer,
} from "@/features/viewer/api";
import { ViewerDashboard } from "@/features/viewer/components/viewer-dashboard";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";
import { renderWithProviders } from "@/test/utils";

vi.mock("@/features/apis/components/account-cost-donut", () => ({
  AccountCostDonut: ({ totalCostUsd }: { totalCostUsd: number }) => (
    <div data-testid="viewer-account-cost-donut">donut {totalCostUsd}</div>
  ),
}));

vi.mock("@/features/apis/components/api-trend-chart", () => ({
  ApiTrendChart: ({ cost, tokens }: { cost: unknown[]; tokens: unknown[] }) => (
    <div data-testid="viewer-api-trend-chart">
      trend {cost.length}/{tokens.length}
    </div>
  ),
}));

vi.mock("@/features/viewer/api", () => ({
  getViewerKeyInfo: vi.fn(),
  getViewerLogs: vi.fn(),
  getViewerQuota: vi.fn(),
  getViewerTrends: vi.fn(),
  getViewerUsage: vi.fn(),
  getViewerUsage7Day: vi.fn(),
  loginViewer: vi.fn(),
  logoutViewer: vi.fn(),
}));

function resetViewerStore(): void {
  useViewerStore.setState({
    authenticated: true,
    initialized: true,
    loading: false,
    error: null,
    keyInfo: null,
    quota: null,
  });
}

describe("ViewerDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetViewerStore();
    useViewerStore.setState({
      quota: [
        {
          limit_type: "cost_usd",
          limit_window: "monthly",
          current_value: 20_158_733,
          max_value: 730_000_000,
          reset_at: "2026-06-20T14:05:00Z",
        },
      ],
    });

    (getViewerKeyInfo as Mock).mockResolvedValue({
      key_id: "key-1",
      key_name: "Customer key",
      is_active: true,
    });
    (getViewerUsage as Mock).mockResolvedValue({
      total_requests: 10,
      successful_requests: 9,
      failed_requests: 1,
      total_input_tokens: 1_000,
      total_output_tokens: 250,
      total_cached_input_tokens: 100,
      total_cost_usd: 20.158733,
      avg_latency_ms: 1_250,
    });
    (getViewerLogs as Mock).mockResolvedValue({
      requests: [],
      total: 0,
      page: 1,
      page_size: 25,
      total_pages: 0,
      has_more: false,
      has_next: false,
      has_previous: false,
    });
    (getViewerQuota as Mock).mockResolvedValue(useViewerStore.getState().quota);
    (loginViewer as Mock).mockResolvedValue({ token: "opaque", expires_in: 86_400 });
    (logoutViewer as Mock).mockResolvedValue(undefined);
    (getViewerTrends as Mock).mockResolvedValue({
      keyId: "key-1",
      cost: [{ t: "2026-05-27T10:00:00Z", v: 1.25 }],
      tokens: [{ t: "2026-05-27T10:00:00Z", v: 300 }],
    });
    (getViewerUsage7Day as Mock).mockResolvedValue({
      keyId: "key-1",
      totalTokens: 300,
      totalCostUsd: 1.25,
      totalRequests: 1,
      cachedInputTokens: 100,
      accountCosts: [
        {
          accountId: "account-secret",
          email: "secret-account@example.com",
          costUsd: 1.25,
          isDeleted: false,
        },
      ],
    });
  });

  it("renders graph panel without leaking account costs and formats cost quota limits as dollars", async () => {
    renderWithProviders(<ViewerDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Customer key")).toBeInTheDocument();
    });

    expect(screen.getByTestId("viewer-api-trend-chart")).toBeInTheDocument();
    expect(screen.queryByTestId("viewer-account-cost-donut")).not.toBeInTheDocument();
    expect(screen.queryByText("secret-account@example.com")).not.toBeInTheDocument();
    expect(screen.getByText("$20.16 / $730.00")).toBeInTheDocument();
    expect(screen.getByText("Accumulated")).toBeInTheDocument();
    expect(getViewerUsage7Day).not.toHaveBeenCalled();
  });

  it("fetches the next request-log page from pagination controls", async () => {
    const user = userEvent.setup();
    (getViewerLogs as Mock).mockImplementation(({ page }: { page: number }) =>
      Promise.resolve({
        requests: [
          {
            requested_at: page === 1 ? "2026-05-27T10:00:00Z" : "2026-05-27T09:00:00Z",
            request_id: page === 1 ? "first-page-request" : "second-page-request",
            model: page === 1 ? "model-page-1" : "model-page-2",
            status: "success",
            input_tokens: 10,
            output_tokens: 20,
            cached_input_tokens: 0,
            cost_usd: 0.1,
            latency_ms: 1200,
            latency_first_token_ms: null,
          },
        ],
        total: 30,
        page,
        page_size: 25,
        total_pages: 2,
        has_more: page === 1,
        has_next: page === 1,
        has_previous: page > 1,
      }),
    );

    renderWithProviders(<ViewerDashboard />);

    await waitFor(() => {
      expect(screen.getByText("model-page-1")).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText("Next logs page"));

    await waitFor(() => {
      expect(screen.getByText("model-page-2")).toBeInTheDocument();
    });
    expect(getViewerLogs).toHaveBeenCalledWith({ page: 2, pageSize: 25 });
    expect(screen.getByText("30 requests · page 2 of 2")).toBeInTheDocument();
  });
});
