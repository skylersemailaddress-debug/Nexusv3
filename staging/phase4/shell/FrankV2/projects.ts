import { apiFetch } from "./client";
import type { ProjectResume } from "../types/domain";

export function getProjectResume(projectId: string) {
  return apiFetch<ProjectResume>(`/projects/${projectId}/resume`);
}

export function getProjectNow(projectId: string) {
  return apiFetch(`/projects/${projectId}/now`);
}

export function getProjectBrief(projectId: string) {
  return apiFetch(`/projects/${projectId}/brief`);
}
