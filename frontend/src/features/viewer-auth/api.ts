import { get, post } from "@/lib/api-client";
import { StatusResponseSchema } from "@/features/auth/schemas";

import {
  ViewerLoginRequestSchema,
  ViewerSessionSchema,
} from "@/features/viewer-auth/schemas";

const VIEWER_AUTH_BASE_PATH = "/api/viewer-auth";

export function getViewerSession() {
  return get(`${VIEWER_AUTH_BASE_PATH}/session`, ViewerSessionSchema);
}

export function loginViewer(payload: unknown) {
  const validated = ViewerLoginRequestSchema.parse(payload);
  return post(`${VIEWER_AUTH_BASE_PATH}/login`, ViewerSessionSchema, { body: validated });
}

export function logoutViewer() {
  return post(`${VIEWER_AUTH_BASE_PATH}/logout`, StatusResponseSchema);
}
