import { apiFetch } from "./client";
import type { ActivityResponse } from "../types/domain";

export function getActivity(projectId: string) {
  return apiFetch<ActivityResponse>(`/projects/${projectId}/activity`);
}
