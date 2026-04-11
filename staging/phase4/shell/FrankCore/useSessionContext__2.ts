import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type SessionContextStore = {
  lastIntent: string
  lastReply: string
  lastArtifactId: string | null
  recentActions: string[]
  setLastIntent: (value: string) => void
  setLastReply: (value: string) => void
  setLastArtifactId: (value: string | null) => void
  pushAction: (value: string) => void
}

export const useSessionContext = create<SessionContextStore>()(
  persist(
    (set) => ({
      lastIntent: '',
      lastReply: '',
      lastArtifactId: null,
      recentActions: [],
      setLastIntent: (value) => set({ lastIntent: value }),
      setLastReply: (value) => set({ lastReply: value }),
      setLastArtifactId: (value) => set({ lastArtifactId: value }),
      pushAction: (value) =>
        set((curr) => ({
          recentActions: [value, ...curr.recentActions.filter((item) => item !== value)].slice(0, 5),
        })),
    }),
    {
      name: 'skyler-session-context-v1',
    },
  ),
)
