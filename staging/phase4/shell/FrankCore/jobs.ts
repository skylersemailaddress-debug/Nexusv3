import { apiFetch } from "./client";
import type { JobItem } from "../types/domain";

export function getRecentJobs() {
  return apiFetch<JobItem[]>("/jobs/recent");
}

export function getRecentFailures() {
  return apiFetch<JobItem[]>("/failures/recent");
}
