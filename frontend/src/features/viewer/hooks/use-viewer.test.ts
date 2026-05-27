import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { getViewerKeyInfo, getViewerQuota, loginViewer, logoutViewer } from "@/features/viewer/api";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";
import { ApiError } from "@/lib/api-client";

vi.mock("@/features/viewer/api", () => ({
  getViewerKeyInfo: vi.fn(),
  getViewerQuota: vi.fn(),
  loginViewer: vi.fn(),
  logoutViewer: vi.fn(),
}));

function resetViewerStore(): void {
  useViewerStore.setState({
    authenticated: false,
    initialized: false,
    loading: false,
    error: null,
    keyInfo: null,
    quota: null,
  });
}

describe("useViewerStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetViewerStore();
  });

  it("refreshSession restores an existing viewer session", async () => {
    (getViewerKeyInfo as Mock).mockResolvedValue({
      key_id: "key-1",
      key_name: "Customer key",
      is_active: true,
    });

    await useViewerStore.getState().refreshSession();

    const state = useViewerStore.getState();
    expect(state.initialized).toBe(true);
    expect(state.authenticated).toBe(true);
    expect(state.keyInfo?.key_id).toBe("key-1");
    expect(state.loading).toBe(false);
  });

  it("refreshSession clears auth on viewer 401", async () => {
    (getViewerKeyInfo as Mock).mockRejectedValue(
      new ApiError({
        status: 401,
        code: "not_authenticated",
        message: "Not authenticated",
      }),
    );

    await useViewerStore.getState().refreshSession();

    const state = useViewerStore.getState();
    expect(state.initialized).toBe(true);
    expect(state.authenticated).toBe(false);
    expect(state.keyInfo).toBeNull();
    expect(state.error).toBeNull();
  });

  it("login stores key info after the cookie is set", async () => {
    (loginViewer as Mock).mockResolvedValue({ token: "opaque", expires_in: 86_400 });
    (getViewerKeyInfo as Mock).mockResolvedValue({
      key_id: "key-1",
      key_name: "Customer key",
      is_active: true,
    });

    await useViewerStore.getState().login("sk-clb-secret");

    expect(loginViewer).toHaveBeenCalledWith({ api_key: "sk-clb-secret" });
    expect(useViewerStore.getState().authenticated).toBe(true);
    expect(useViewerStore.getState().keyInfo?.key_name).toBe("Customer key");
  });

  it("loadQuota clears the session on viewer 401", async () => {
    useViewerStore.setState({ authenticated: true, initialized: true });
    (getViewerQuota as Mock).mockRejectedValue(
      new ApiError({
        status: 401,
        code: "session_expired",
        message: "Session expired",
      }),
    );

    await useViewerStore.getState().loadQuota();

    expect(useViewerStore.getState().authenticated).toBe(false);
  });

  it("logout clears local viewer state", async () => {
    useViewerStore.setState({
      authenticated: true,
      initialized: true,
      keyInfo: { key_id: "key-1", key_name: "Customer key", is_active: true },
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
    (logoutViewer as Mock).mockResolvedValue(undefined);

    await useViewerStore.getState().logout();

    expect(useViewerStore.getState().authenticated).toBe(false);
    expect(useViewerStore.getState().keyInfo).toBeNull();
    expect(useViewerStore.getState().quota).toBeNull();
  });
});

