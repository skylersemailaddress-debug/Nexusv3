import { create } from 'zustand'

export type AttentionTarget = 'chat' | 'dock' | 'surface' | 'voice' | 'none'

type AttentionStore = {
  target: AttentionTarget
  intensity: number
  setAttention: (target: AttentionTarget, intensity?: number) => void
  clearAttention: () => void
}

export const useAttention = create<AttentionStore>((set) => ({
  target: 'none',
  intensity: 0,
  setAttention: (target, intensity = 1) => set({ target, intensity }),
  clearAttention: () => set({ target: 'none', intensity: 0 }),
}))
