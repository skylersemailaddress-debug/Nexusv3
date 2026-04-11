import { apiFetch } from './client'

export type ControlPlaneInspectorProject = {
  project_id: string
  control_plane_state: Record<string, unknown>
  objects: Array<Record<string, unknown>>
  ledger: Array<Record<string, unknown>>
  checkpoints: Array<Record<string, unknown>>
  tool_runs: Array<Record<string, unknown>>
  sandboxes: Array<Record<string, unknown>>
  promotions: Array<Record<string, unknown>>
  permission_events: Array<Record<string, unknown>>
  startup_summary: Record<string, unknown>
}

export async function getControlPlaneRuntime() {
  return apiFetch<Record<string, unknown>>('/control-plane/inspect/runtime', { method: 'GET' })
}

export async function getControlPlaneProject(projectId: string) {
  return apiFetch<ControlPlaneInspectorProject>(`/control-plane/inspect/project/${projectId}`, { method: 'GET' })
}
