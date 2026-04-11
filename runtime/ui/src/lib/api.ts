export const API = "http://127.0.0.1:8000";
const TOKEN_KEY = "nexus_auth_token";

export type HealthResponse = { status?: string };
export type DashboardStatus = { system?: string; status?: string; runtime?: string; actor?: { username?: string; role?: string } };
export type Signal = { id: string; title: string; severity: string; detail: string; ts: number };
export type BriefResponse = { headline?: string; summary?: string; next_action?: string; actor?: { username?: string; role?: string } };
export type LoopItem = { id: string; title: string; owner: string; status: string; priority: string };
export type OpenLoopsResponse = { items: LoopItem[]; count: number; actor?: { username?: string; role?: string } };
export type ActionResponse = { result?: string; refreshed_at?: number; item?: LoopItem; count?: number; actor?: { username?: string; role?: string } };
export type LoginResponse = { access_token: string; token_type: string; role: string };

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

async function authFetch(url: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}

export async function ensureLogin(username = "operator") {
  if (getToken()) return;
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username })
  });
  const data = (await res.json()) as LoginResponse;
  setToken(data.access_token);
}

export async function fetchDashboard() {
  await ensureLogin();
  const [healthRes, statusRes, signalsRes, briefRes, loopsRes] = await Promise.all([
    authFetch(`${API}/health`),
    authFetch(`${API}/dashboard/status`),
    authFetch(`${API}/dashboard/signals`),
    authFetch(`${API}/dashboard/brief`),
    authFetch(`${API}/workflows/open-loops`)
  ]);

  return {
    health: (await healthRes.json()) as HealthResponse,
    status: (await statusRes.json()) as DashboardStatus,
    signals: ((await signalsRes.json()).signals ?? []) as Signal[],
    brief: (await briefRes.json()) as BriefResponse,
    loops: ((await loopsRes.json()).items ?? []) as LoopItem[],
  };
}

export async function refreshDashboard() {
  await ensureLogin();
  const res = await authFetch(`${API}/action/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "command-center-panel" })
  });
  return (await res.json()) as ActionResponse;
}

export async function addOpenLoop(title: string) {
  await ensureLogin();
  const res = await authFetch(`${API}/workflows/open-loops/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, owner: "Skyler", priority: "high" })
  });
  return (await res.json()) as ActionResponse;
}
