import { create } from 'zustand'

export type ContextMode = 'memory' | 'artifacts' | 'execution' | 'agent_trace' | 'voice' | 'overview'

type ContextModeStore = {
  mode: ContextMode
  autoMode: ContextMode
  isPinnedOpen: boolean
  setMode: (mode: ContextMode) => void
  setAutoMode: (mode: ContextMode) => void
  resetToAuto: () => void
  setPinnedOpen: (value: boolean) => void
}

export const useContextMode = create<ContextModeStore>((set, get) => ({
  mode: 'overview',
  autoMode: 'overview',
  isPinnedOpen: true,
  setMode: (mode) => set({ mode }),
  setAutoMode: (mode) => {
    const { mode: currentMode } = get()
    set({ autoMode: mode, mode: currentMode === get().autoMode ? mode : currentMode })
  },
  resetToAuto: () => set((curr) => ({ mode: curr.autoMode })),
  setPinnedOpen: (value) => set({ isPinnedOpen: value }),
}))
