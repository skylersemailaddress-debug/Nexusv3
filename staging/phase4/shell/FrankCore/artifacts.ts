import { apiFetch } from "./client";
import type { ArtifactItem } from "../types/domain";

export function getArtifacts(projectId: string) {
  return apiFetch<ArtifactItem[]>(`/projects/${projectId}/artifacts`);
}
