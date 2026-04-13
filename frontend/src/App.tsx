import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AppHeader } from "@/components/layout/app-header";
import { StatusBar } from "@/components/layout/status-bar";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthGate } from "@/features/auth/components/auth-gate";
import { useAuthStore } from "@/features/auth/hooks/use-auth";
import { AccountsPage } from "@/features/accounts/components/accounts-page";
import { ApisPage } from "@/features/apis/components/apis-page";
import { DashboardPage } from "@/features/dashboard/components/dashboard-page";
import { SettingsPage } from "@/features/settings/components/settings-page";
import { ViewerAuthGate } from "@/features/viewer-auth/components/viewer-auth-gate";
import { useViewerAuthStore } from "@/features/viewer-auth/hooks/use-viewer-auth";
import { ViewerDashboardPage } from "@/features/viewer/components/viewer-dashboard-page";
import { ViewerPage } from "@/features/viewer/components/viewer-page";
import { ViewerSettingsPage } from "@/features/viewer/components/viewer-settings-page";
import { useTimeFormatStore } from "@/hooks/use-time-format";

const VIEWER_NAV_ITEMS = [
  { to: "/viewer/dashboard", label: "Dashboard" },
  { to: "/viewer/quota", label: "Quota" },
  { to: "/viewer/settings", label: "Settings" },
] as const;

function AdminAppLayout() {
  const logout = useAuthStore((state) => state.logout);
  const passwordRequired = useAuthStore((state) => state.passwordRequired);
  const timeFormat = useTimeFormatStore((state) => state.timeFormat);

  return (
    <div className="flex min-h-screen flex-col bg-background pb-10" data-time-format={timeFormat}>
      <AppHeader
        onLogout={() => {
          void logout();
        }}
        showLogout={passwordRequired}
      />
      <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>
      <StatusBar />
    </div>
  );
}

function ViewerAppLayout() {
  const logout = useViewerAuthStore((state) => state.logout);

  return (
    <div className="flex min-h-screen flex-col bg-background pb-10">
      <AppHeader
        navItems={VIEWER_NAV_ITEMS}
        onLogout={() => {
          void logout();
        }}
        showLogout
      />
      <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <TooltipProvider>
      <Toaster richColors />
      <Routes>
        <Route
          path="/viewer"
          element={(
            <ViewerAuthGate>
              <ViewerAppLayout />
            </ViewerAuthGate>
          )}
        >
          <Route index element={<Navigate to="/viewer/dashboard" replace />} />
          <Route path="dashboard" element={<ViewerDashboardPage />} />
          <Route path="quota" element={<ViewerPage />} />
          <Route path="settings" element={<ViewerSettingsPage />} />
        </Route>

        <Route
          element={(
            <AuthGate>
              <AdminAppLayout />
            </AuthGate>
          )}
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/accounts" element={<AccountsPage />} />
          <Route path="/apis" element={<ApisPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/firewall" element={<Navigate to="/settings" replace />} />
        </Route>
      </Routes>
    </TooltipProvider>
  );
}
