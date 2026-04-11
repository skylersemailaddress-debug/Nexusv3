export type ArtifactType = 'text' | 'markdown' | 'list' | 'table' | 'code' | 'document_ref'

export type ArtifactTable = {
  columns: string[]
  rows: Array<Array<string | number | boolean | null>>
}

export type ArtifactCodeBlock = {
  language?: string
  content: string
}

export type SkylerArtifact = {
  id: string
  type: ArtifactType
  title: string
  kind: string
  path?: string | null
  content?: string
  items?: string[]
  table?: ArtifactTable
  code?: ArtifactCodeBlock
  meta?: Record<string, unknown>
}

export type SkylerJob = {
  id?: string
  status?: string
  label?: string
}

export type SkylerAssistantMessage = {
  id?: string
  content?: string
}

export type SkylerOrchestrateResponse = {
  ok?: boolean
  status?: string
  message?: string
  reply?: string
  assistant_message?: SkylerAssistantMessage
  artifact?: Partial<SkylerArtifact> & {
    payload?: unknown
    items?: string[]
    table?: ArtifactTable
    code?: ArtifactCodeBlock
    meta?: Record<string, unknown>
  }
  job?: SkylerJob
}

export type SkylerOrchestrateRequest = {
  project_id: string
  input: string
  mode?: string
  meta?: Record<string, unknown>
  active_context?: Record<string, unknown>
  session_context?: Record<string, unknown>
  selected_artifact_id?: string | null
}

export function normalizeArtifact(input?: SkylerOrchestrateResponse['artifact']): SkylerArtifact | null {
  if (!input || !input.id) return null

  const payload = input.payload as Record<string, unknown> | undefined
  const directContent = typeof input.content === 'string' ? input.content : undefined
  const payloadContent = typeof payload?.content === 'string' ? payload.content : undefined
  const content = directContent || payloadContent

  const items = Array.isArray(input.items)
    ? input.items.filter((item): item is string => typeof item === 'string')
    : Array.isArray(payload?.items)
    ? (payload.items as unknown[]).filter((item): item is string => typeof item === 'string')
    : undefined

  const table = isArtifactTable(input.table) ? input.table : isArtifactTable(payload?.table) ? (payload?.table as ArtifactTable) : undefined
  const code = isArtifactCodeBlock(input.code)
    ? input.code
    : isArtifactCodeBlock(payload?.code)
    ? (payload?.code as ArtifactCodeBlock)
    : undefined

  const path = typeof input.path === 'string' ? input.path : typeof payload?.path === 'string' ? payload.path : undefined
  const title =
    input.title ||
    (typeof payload?.title === 'string' ? payload.title : undefined) ||
    (typeof input.kind === 'string' ? input.kind : undefined) ||
    'Generated artifact'
  const kind = input.kind || (typeof payload?.kind === 'string' ? payload.kind : undefined) || 'artifact'

  const explicitType = typeof input.type === 'string' ? input.type : typeof payload?.type === 'string' ? payload.type : undefined
  const type = normalizeArtifactType(explicitType, { content, items, table, code, path })

  return {
    id: input.id,
    type,
    title,
    kind,
    path,
    content,
    items,
    table,
    code,
    meta: input.meta || (isRecord(payload?.meta) ? (payload?.meta as Record<string, unknown>) : undefined),
  }
}

function normalizeArtifactType(
  explicitType: string | undefined,
  shape: { content?: string; items?: string[]; table?: ArtifactTable; code?: ArtifactCodeBlock; path?: string | null },
): ArtifactType {
  if (explicitType && isArtifactType(explicitType)) return explicitType
  if (shape.table) return 'table'
  if (shape.items && shape.items.length > 0) return 'list'
  if (shape.code) return 'code'
  if (shape.path) return 'document_ref'
  if (shape.content && /(^#|\n#|\*\*|^- )/m.test(shape.content)) return 'markdown'
  return 'text'
}

function isArtifactType(value: string): value is ArtifactType {
  return ['text', 'markdown', 'list', 'table', 'code', 'document_ref'].includes(value)
}

function isArtifactTable(value: unknown): value is ArtifactTable {
  return isRecord(value) && Array.isArray(value.columns) && Array.isArray(value.rows)
}

function isArtifactCodeBlock(value: unknown): value is ArtifactCodeBlock {
  return isRecord(value) && typeof value.content === 'string'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
