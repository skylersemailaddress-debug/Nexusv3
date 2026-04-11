import { apiFetch } from "./client";
import type { Capability } from "../types/domain";

export function getCapabilities() {
  return apiFetch<Capability[]>("/registry/capabilities");
}
