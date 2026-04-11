import type { BuildContextResponse } from "@/lib/types/domain";
import { apiFetch } from "./client";

export async function fetchBuildContext(projectId: string, userMessage = ""): Promise<BuildContextResponse> {
  return apiFetch<BuildContextResponse>("/state/build-context", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId,
      user_message: userMessage,
    }),
  });
}
