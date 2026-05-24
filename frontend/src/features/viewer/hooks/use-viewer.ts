import { create } from "zustand";

import { getViewerQuota, loginViewer, logoutViewer } from "@/features/viewer/api";
import type { ViewerKeyInfo, ViewerQuotaEntry } from "@/features/viewer/schemas";

type ViewerState = {
  authenticated: boolean;
  loading: boolean;
  error: string | null;
  keyInfo: ViewerKeyInfo | null;
  quota: ViewerQuotaEntry[] | null;
  login: (apiKey: string) => Promise<void>;
  logout: () => Promise<void>;
  setKeyInfo: (info: ViewerKeyInfo) => void;
  loadQuota: () => Promise<void>;
  clearError: () => void;
};

export const useViewerStore = create<ViewerState>((set) => ({
  authenticated: false,
  loading: false,
  error: null,
  keyInfo: null,
  quota: null,

  login: async (apiKey: string) => {
    set({ loading: true, error: null });
    try {
      await loginViewer({ api_key: apiKey });
      set({ authenticated: true });
    } catch (err) {
      set({
        authenticated: false,
        error: err instanceof Error ? err.message : "Login failed",
      });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  logout: async () => {
    try {
      await logoutViewer();
    } catch {
      // ignore
    }
    set({ authenticated: false, keyInfo: null, quota: null });
  },

  setKeyInfo: (info) => set({ keyInfo: info }),
  loadQuota: async () => {
    try {
      const quota = await getViewerQuota();
      set({ quota });
    } catch {
      // non-critical
    }
  },
  clearError: () => set({ error: null }),
}));
