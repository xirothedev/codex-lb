import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound } from "lucide-react";
import { useForm } from "react-hook-form";

import { AlertMessage } from "@/components/alert-message";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { ViewerLoginRequestSchema } from "@/features/viewer-auth/schemas";
import { useViewerAuthStore } from "@/features/viewer-auth/hooks/use-viewer-auth";

export function ViewerLoginForm() {
  const login = useViewerAuthStore((state) => state.login);
  const loading = useViewerAuthStore((state) => state.loading);
  const error = useViewerAuthStore((state) => state.error);
  const clearError = useViewerAuthStore((state) => state.clearError);

  const form = useForm({
    resolver: zodResolver(ViewerLoginRequestSchema),
    defaultValues: { apiKey: "" },
  });

  const handleSubmit = async (values: { apiKey: string }) => {
    clearError();
    await login(values.apiKey.trim());
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="rounded-2xl border bg-card p-6 shadow-[var(--shadow-md)]">
        <div className="space-y-1.5">
          <h2 className="text-base font-semibold tracking-tight">Sign in</h2>
          <p className="text-sm text-muted-foreground">Enter your API key to access your usage portal.</p>
        </div>

        <div className="mt-5">
          <FormField
            control={form.control}
            name="apiKey"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium">API Key</FormLabel>
                <div className="relative">
                  <KeyRound className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" aria-hidden="true" />
                  <FormControl>
                    <Input
                      {...field}
                      type="password"
                      autoComplete="off"
                      placeholder="sk-clb-..."
                      disabled={loading}
                      className="pl-9"
                    />
                  </FormControl>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {error ? <AlertMessage variant="error" className="mt-4">{error}</AlertMessage> : null}

        <Button type="submit" className="press-scale mt-5 w-full" disabled={loading}>
          {loading ? <Spinner size="sm" className="mr-2" /> : null}
          Sign In
        </Button>
      </form>
    </Form>
  );
}
