import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { get, setUnauthorizedHandler } from "@/lib/api-client";

const OkSchema = z.object({ ok: z.boolean() });

describe("api-client unauthorized handlers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("dispatches 401 handlers only to matching paths", async () => {
    const adminHandler = vi.fn();
    const viewerHandler = vi.fn();

    setUnauthorizedHandler(adminHandler, (path) => path.startsWith("/api/") && !path.startsWith("/api/viewer"));
    setUnauthorizedHandler(viewerHandler, (path) => path.startsWith("/api/viewer"));

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "authentication_required", message: "Authentication is required" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(get("/api/viewer/api-key", OkSchema)).rejects.toThrow();

    expect(viewerHandler).toHaveBeenCalledTimes(1);
    expect(adminHandler).not.toHaveBeenCalled();
  });
});
