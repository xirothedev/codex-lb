import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AlertMessage } from "@/components/alert-message";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useViewerStore } from "@/features/viewer/hooks/use-viewer";

const formSchema = z.object({ api_key: z.string().min(1, "API key is required") });

export function ViewerLogin() {
  const login = useViewerStore((s) => s.login);
  const loading = useViewerStore((s) => s.loading);
  const error = useViewerStore((s) => s.error);
  const clearError = useViewerStore((s) => s.clearError);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: { api_key: "" },
  });

  const handleSubmit = async (values: { api_key: string }) => {
    clearError();
    try {
      await login(values.api_key);
    } catch {
      // error handled in store
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(handleSubmit)}
          className="w-full max-w-sm rounded-2xl border bg-card p-6 shadow-[var(--shadow-md)]"
        >
          <div className="space-y-1.5">
            <h2 className="text-base font-semibold tracking-tight">API Usage Viewer</h2>
            <p className="text-sm text-muted-foreground">
              Enter your API key to view request logs and usage stats.
            </p>
          </div>

          <div className="mt-5">
            <FormField
              control={form.control}
              name="api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs font-medium">API Key</FormLabel>
                  <div className="relative">
                    <KeyRound className="text-muted-foreground/50 absolute left-3 top-1/2 -translate-y-1/2 size-4" />
                    <FormControl>
                      <Input
                        {...field}
                        type="password"
                        placeholder="sk-clb-..."
                        className="pl-9"
                        autoComplete="off"
                      />
                    </FormControl>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {error ? (
            <AlertMessage variant="error" className="mt-4">
              {error}
            </AlertMessage>
          ) : null}

          <Button type="submit" className="press-scale mt-5 w-full" disabled={loading}>
            {loading ? <Spinner size="sm" className="mr-2" /> : null}
            View Usage
          </Button>
        </form>
      </Form>
    </div>
  );
}
