import { create } from "zustand";

import { loginViewer, logoutViewer } from "@/features/viewer/api";
import type { ViewerKeyInfo } from "@/features/viewer/schemas";

type ViewerState = {
  authenticated: boolean;
  loading: boolean;
  error: string | null;
  keyInfo: ViewerKeyInfo | null;
  login: (apiKey: string) => Promise<void>;
  logout: () => Promise<void>;
  setKeyInfo: (info: ViewerKeyInfo) => void;
  clearError: () => void;
};

export const useViewerStore = create<ViewerState>((set) => ({
  authenticated: false,
  loading: false,
  error: null,
  keyInfo: null,

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
    set({ authenticated: false, keyInfo: null });
  },

  setKeyInfo: (info) => set({ keyInfo: info }),
  clearError: () => set({ error: null }),
}));
