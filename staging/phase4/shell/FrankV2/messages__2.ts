import { apiFetch } from "./client";

export function appendMessage(projectId: string, content: string) {
  return apiFetch("/messages/append", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId,
      role: "user",
      content,
      meta: {}
    }),
  });
}

export function orchestrateAction(projectId: string, input: string) {
  return apiFetch("/orchestrate/action", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId,
      input,
    }),
  });
}
