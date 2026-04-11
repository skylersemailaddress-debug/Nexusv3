export type ActivityItem = {
  id: string
  project_id: string
  type: string
  title: string
  summary?: string
  status?: string | null
  timestamp?: string | null
  metadata?: Record<string, unknown>
}

export type MemoryItem = {
  id?: string
  project_id?: string
  scope?: string
  title?: string
  content?: string
  status?: string
  confidence?: number
  meta?: Record<string, unknown>
  updated_at?: string | null
}

export type CheckpointItem = {
  id: string
  project_id: string
  title: string
  summary?: string
  created_at?: string | null
  snapshot?: Record<string, unknown>
}

export type SuggestedAction = {
  id: string
  priority?: string
  kind?: string
  title: string
  reason?: string
  payload?: Record<string, unknown>
}

export type BuildContextResponse = {
  ok?: boolean
  project_id: string
  user_message?: string
  project?: {
    id: string
    last_user_message?: string
    state_root?: string
  }
  objective?: { title?: string | null }
  next_step?: { title?: string | null }
  blockers?: Array<{ title?: string; reason?: string } | string>
  recent_jobs?: Array<Record<string, unknown>>
  recent_artifacts?: Array<Record<string, unknown>>
  recent_messages?: Array<Record<string, unknown>>
  relevant_memory?: MemoryItem[]
  latest_checkpoint?: CheckpointItem | null
  latest_ramble_capture?: Record<string, unknown> | null
  operator?: {
    status?: string
    summary?: string
    prioritized_actions?: SuggestedAction[]
    workflow_chain?: string[]
    signals?: Record<string, unknown>
    richer_summary?: {
      objective_title?: string | null
      next_step_title?: string | null
      top_blocker?: string | null
      top_memory_titles?: string[]
      workflow_readiness?: string | null
    }
  }
  next_suggested_actions?: SuggestedAction[]
  continuity?: {
    recent_message_count?: number
    memory_signal_count?: number
    recent_message_preview?: Array<Record<string, unknown>>
    memory_signal_titles?: string[]
    latest_checkpoint_title?: string | null
    latest_ramble_capture_title?: string | null
  }
}
