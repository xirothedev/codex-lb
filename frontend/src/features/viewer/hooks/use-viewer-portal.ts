import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getViewerApiKey, regenerateViewerApiKey } from "@/features/viewer/api";

export function useViewerPortal() {
  const queryClient = useQueryClient();

  const apiKeyQuery = useQuery({
    queryKey: ["viewer", "api-key"],
    queryFn: getViewerApiKey,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  });

  const regenerateMutation = useMutation({
    mutationFn: regenerateViewerApiKey,
    onSuccess: () => {
      toast.success("API key regenerated");
      void queryClient.invalidateQueries({ queryKey: ["viewer", "api-key"] });
      void queryClient.invalidateQueries({ queryKey: ["viewer", "auth", "session"] });
      void queryClient.invalidateQueries({ queryKey: ["viewer", "request-logs"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to regenerate API key");
    },
  });

  return {
    apiKeyQuery,
    regenerateMutation,
  };
}
