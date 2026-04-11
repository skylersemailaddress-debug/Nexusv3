import { getApiProxyUrl, jsonHeaders, parseJsonResponse, toApiError } from './client'

export async function getProjectResume(projectId: string) {
  const response = await fetch(getApiProxyUrl(`/projects/${projectId}/resume`), {
    method: 'GET',
    headers: jsonHeaders(),
    cache: 'no-store',
  })

  const data = await parseJsonResponse(response)
  if (!response.ok) {
    throw toApiError(response, data)
  }
  return data
}
