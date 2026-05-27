import { useEffect } from "react";

import { Spinner } from "@/components/ui/spinner";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";
import { ViewerDashboard } from "@/features/viewer/components/viewer-dashboard";
import { ViewerLogin } from "@/features/viewer/components/viewer-login";

export function ViewerPage() {
  const refreshSession = useViewerStore((s) => s.refreshSession);
  const authenticated = useViewerStore((s) => s.authenticated);
  const initialized = useViewerStore((s) => s.initialized);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  if (!initialized) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!authenticated) {
    return <ViewerLogin />;
  }

  return <ViewerDashboard />;
}
