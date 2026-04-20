import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ExpiryPicker } from "@/features/api-keys/components/expiry-picker";
import type { ApiKey, ApiKeyUpdateRequest } from "@/features/api-keys/schemas";

export type ApiKeyRenewDialogProps = {
  open: boolean;
  busy: boolean;
  apiKey: ApiKey | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: ApiKeyUpdateRequest) => Promise<void>;
};

export function ApiKeyRenewDialog({
  open,
  busy,
  apiKey,
  onOpenChange,
  onSubmit,
}: ApiKeyRenewDialogProps) {
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);

  useEffect(() => {
    if (open) {
      setExpiresAt(null);
    }
  }, [apiKey?.id, open]);

  const handleSubmit = async () => {
    try {
      await onSubmit({
        expiresAt: expiresAt?.toISOString() ?? null,
        resetUsage: true,
      });
    } catch {
      return;
    }

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Renew API key</DialogTitle>
          <DialogDescription>
            Reset current quota counters and refresh expiry without rotating the secret. Lifetime logs
            and usage history stay intact.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1">
            <div className="text-sm font-medium">Expiry</div>
            <ExpiryPicker value={expiresAt} onChange={setExpiresAt} />
          </div>

          {apiKey ? (
            <div className="rounded-lg border bg-muted/30 p-3 text-xs text-muted-foreground">
              Renewing <span className="font-medium text-foreground">{apiKey.name}</span> keeps the same
              key prefix <span className="font-mono text-foreground">{apiKey.keyPrefix}</span>.
            </div>
          ) : null}
        </div>

        <DialogFooter>
          <Button type="button" onClick={() => void handleSubmit()} disabled={busy}>
            Renew
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
