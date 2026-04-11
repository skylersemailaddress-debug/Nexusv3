import { create } from 'zustand'

export type SystemState = 'idle' | 'thinking' | 'acting' | 'done' | 'error' | 'listening'

export type WhisperItem = {
  id: string
  text: string
  kind: 'info' | 'memory' | 'artifact' | 'execution' | 'error'
  createdAt: number
}

const precedence: Record<SystemState, number> = {
  idle: 0,
  done: 1,
  thinking: 2,
  acting: 3,
  listening: 4,
  error: 5,
}

const whisperLifetime: Record<WhisperItem['kind'], number> = {
  info: 1800,
  memory: 2200,
  artifact: 2200,
  execution: 1800,
  error: 3200,
}

type SystemStateStore = {
  state: SystemState
  lastCompletedAt: number | null
  whispers: WhisperItem[]
  setState: (state: SystemState) => void
  transitionTo: (state: SystemState) => void
  pulseDone: () => void
  addWhisper: (text: string, kind?: WhisperItem['kind']) => void
  clearWhisper: (id: string) => void
  clearWhispers: () => void
}

export const useSystemState = create<SystemStateStore>((set, get) => ({
  state: 'idle',
  lastCompletedAt: null,
  whispers: [],
  setState: (state) => set({ state }),
  transitionTo: (next) => {
    const current = get().state
    if (next === 'done' || next === 'idle') {
      set({ state: next, lastCompletedAt: next === 'done' ? Date.now() : get().lastCompletedAt })
      return
    }
    set({ state: precedence[next] >= precedence[current] ? next : current })
  },
  pulseDone: () =>
    set({
      state: 'done',
      lastCompletedAt: Date.now(),
    }),
  addWhisper: (text, kind = 'info') => {
    const normalizedText = text.trim()
    if (!normalizedText) return

    const id = `whisper_${Math.random().toString(36).slice(2, 10)}`
    const createdAt = Date.now()

    set((curr) => {
      const deduped = curr.whispers.filter((item) => item.text !== normalizedText || item.kind !== kind)
      return {
        whispers: [{ id, text: normalizedText, kind, createdAt }, ...deduped].slice(0, 2),
      }
    })

    if (typeof window !== 'undefined') {
      window.setTimeout(() => {
        set((curr) => ({
          whispers: curr.whispers.filter((item) => item.id !== id),
        }))
      }, whisperLifetime[kind])
    }
  },
  clearWhisper: (id) =>
    set((curr) => ({
      whispers: curr.whispers.filter((item) => item.id !== id),
    })),
  clearWhispers: () => set({ whispers: [] }),
}))
