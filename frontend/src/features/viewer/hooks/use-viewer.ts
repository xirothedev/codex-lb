import { create } from "zustand";

import { getViewerKeyInfo, getViewerQuota, loginViewer, logoutViewer } from "@/features/viewer/api";
import type { ViewerKeyInfo, ViewerQuotaEntry } from "@/features/viewer/schemas";
import { ApiError } from "@/lib/api-client";

type ViewerState = {
  authenticated: boolean;
  initialized: boolean;
  loading: boolean;
  error: string | null;
  keyInfo: ViewerKeyInfo | null;
  quota: ViewerQuotaEntry[] | null;
  refreshSession: () => Promise<void>;
  login: (apiKey: string) => Promise<void>;
  logout: () => Promise<void>;
  clearSession: () => void;
  setKeyInfo: (info: ViewerKeyInfo) => void;
  loadQuota: () => Promise<void>;
  clearError: () => void;
};

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

export const useViewerStore = create<ViewerState>((set) => ({
  authenticated: false,
  initialized: false,
  loading: false,
  error: null,
  keyInfo: null,
  quota: null,

  refreshSession: async () => {
    set({ loading: true, error: null });
    try {
      const keyInfo = await getViewerKeyInfo();
      set({ authenticated: true, initialized: true, keyInfo, error: null });
    } catch (err) {
      set({
        authenticated: false,
        initialized: true,
        keyInfo: null,
        quota: null,
        error: isUnauthorized(err) ? null : err instanceof Error ? err.message : "Session check failed",
      });
    } finally {
      set({ loading: false });
    }
  },

  login: async (apiKey: string) => {
    set({ loading: true, error: null });
    try {
      await loginViewer({ api_key: apiKey });
      const keyInfo = await getViewerKeyInfo();
      set({ authenticated: true, initialized: true, keyInfo });
    } catch (err) {
      set({
        authenticated: false,
        initialized: true,
        keyInfo: null,
        quota: null,
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
    set({ authenticated: false, initialized: true, keyInfo: null, quota: null });
  },

  clearSession: () => set({ authenticated: false, initialized: true, keyInfo: null, quota: null }),
  setKeyInfo: (info) => set({ keyInfo: info }),
  loadQuota: async () => {
    try {
      const quota = await getViewerQuota();
      set({ quota });
    } catch (err) {
      if (isUnauthorized(err)) {
        set({ authenticated: false, initialized: true, keyInfo: null, quota: null });
      }
    }
  },
  clearError: () => set({ error: null }),
}));
