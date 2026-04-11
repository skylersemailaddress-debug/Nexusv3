import type { BuildContextResponse } from "@/lib/types/domain"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:5050"
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN || "dev-api-token"

export async function fetchBuildContext(projectId: string, userMessage = ""): Promise<BuildContextResponse> {
  const response = await fetch(`${API_BASE}/state/build-context`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_TOKEN}`,
    },
    body: JSON.stringify({
      project_id: projectId,
      user_message: userMessage,
    }),
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch build-context: ${response.status}`)
  }

  return response.json()
}
