import { create } from "zustand";

import { setUnauthorizedHandler } from "@/lib/api-client";
import {
  getViewerSession,
  loginViewer,
  logoutViewer,
} from "@/features/viewer-auth/api";
import type { ViewerSession } from "@/features/viewer-auth/schemas";

type ViewerAuthState = {
  authenticated: boolean;
  apiKeyName: string | null;
  loading: boolean;
  initialized: boolean;
  error: string | null;
  refreshSession: () => Promise<ViewerSession>;
  login: (apiKey: string) => Promise<ViewerSession>;
  logout: () => Promise<void>;
  clearError: () => void;
};

function applySession(set: (next: Partial<ViewerAuthState>) => void, session: ViewerSession): ViewerSession {
  set({
    authenticated: session.authenticated,
    apiKeyName: session.apiKey?.name ?? null,
    initialized: true,
    error: null,
  });
  return session;
}

export const useViewerAuthStore = create<ViewerAuthState>((set) => ({
  authenticated: false,
  apiKeyName: null,
  loading: false,
  initialized: false,
  error: null,
  refreshSession: async () => {
    set({ loading: true, error: null });
    try {
      const session = await getViewerSession();
      return applySession(set, session);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to refresh viewer session",
      });
      throw error;
    } finally {
      set({ loading: false, initialized: true });
    }
  },
  login: async (apiKey) => {
    set({ loading: true, error: null });
    try {
      const session = await loginViewer({ apiKey });
      return applySession(set, session);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Viewer login failed" });
      throw error;
    } finally {
      set({ loading: false, initialized: true });
    }
  },
  logout: async () => {
    set({ loading: true, error: null });
    try {
      await logoutViewer();
      set({ authenticated: false, apiKeyName: null, initialized: true });
    } finally {
      set({ loading: false });
    }
  },
  clearError: () => set({ error: null }),
}));

setUnauthorizedHandler(
  () => {
    useViewerAuthStore.setState({
      authenticated: false,
      apiKeyName: null,
      initialized: true,
      error: null,
    });
  },
  (path) => path.startsWith("/api/viewer") || path.startsWith("/api/viewer-auth"),
);
