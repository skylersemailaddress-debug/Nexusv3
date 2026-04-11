const API_BASE = process.env.NEXT_PUBLIC_ODP_API_BASE ?? "http://localhost:8000";
const API_TOKEN = process.env.NEXT_PUBLIC_ODP_API_TOKEN ?? "dev-api-token";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_TOKEN}`,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status} ${response.statusText}: ${text}`);
  }

  return response.json() as Promise<T>;
}
