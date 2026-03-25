import { Settings } from "lucide-react";

import { AppearanceSettings } from "@/features/settings/components/appearance-settings";

export function ViewerSettingsPage() {
  return (
    <div className="animate-fade-in-up space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <Settings className="h-5 w-5 text-primary" />
          Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">Choose how the viewer portal looks.</p>
      </div>

      <AppearanceSettings />
    </div>
  );
}
