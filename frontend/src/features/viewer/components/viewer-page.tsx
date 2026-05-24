import { useViewerStore } from "@/features/viewer/hooks/use-viewer";
import { ViewerDashboard } from "@/features/viewer/components/viewer-dashboard";
import { ViewerLogin } from "@/features/viewer/components/viewer-login";

export function ViewerPage() {
  const authenticated = useViewerStore((s) => s.authenticated);

  if (!authenticated) {
    return <ViewerLogin />;
  }

  return <ViewerDashboard />;
}
