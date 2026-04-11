import { apiFetch } from "./client";
import type { BuildContext } from "../types/domain";

export function buildContext(projectId: string) {
  return apiFetch<BuildContext>("/state/build-context", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export function updateProjectState(projectId: string, patch: Record<string, unknown>) {
  return apiFetch(`/projects/${projectId}/state/update`, {
    method: "POST",
    body: JSON.stringify(patch),
  });
}
