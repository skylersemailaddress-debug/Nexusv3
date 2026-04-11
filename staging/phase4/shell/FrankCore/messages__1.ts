import { getApiProxyUrl, jsonHeaders, parseJsonResponse, toApiError } from './client'

type MessageAppendPayload =
  | string
  | {
      role?: string
      content: string
      meta?: Record<string, unknown>
    }

type OrchestratePayload =
  | string
  | {
      project_id?: string
      input?: string
      message?: string
      content?: string
      mode?: string
      meta?: Record<string, unknown>
      active_context?: Record<string, unknown>
      session_context?: Record<string, unknown>
      selected_artifact_id?: string | null
    }

export async function appendMessage(projectId: string, payload: MessageAppendPayload) {
  const body =
    typeof payload === 'string'
      ? { role: 'user', content: payload, meta: { source: 'workspace_ui' } }
      : {
          role: payload.role || 'user',
          content: payload.content,
          meta: payload.meta || {},
        }

  const response = await fetch(getApiProxyUrl('/messages/append'), {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({
      project_id: projectId,
      ...body,
    }),
    cache: 'no-store',
  })

  const data = await parseJsonResponse(response)
  if (!response.ok) {
    throw toApiError(response, data)
  }
  return data
}

export async function orchestrateAction(projectId: string, input: OrchestratePayload) {
  const body =
    typeof input === 'string'
      ? {
          project_id: projectId,
          input,
          mode: 'default',
          meta: { source: 'workspace_ui' },
        }
      : {
          project_id: input.project_id || projectId,
          input: input.input || input.message || input.content || '',
          mode: input.mode || 'default',
          meta: input.meta || {},
          active_context: input.active_context,
          session_context: input.session_context,
          selected_artifact_id: input.selected_artifact_id,
        }

  const response = await fetch(getApiProxyUrl('/orchestrate/action'), {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(body),
    cache: 'no-store',
  })

  const data = await parseJsonResponse(response)
  if (!response.ok) {
    throw toApiError(response, data)
  }
  return data
}
