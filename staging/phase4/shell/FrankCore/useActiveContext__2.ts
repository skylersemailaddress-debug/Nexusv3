import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ContextMode } from './useContextMode'
import type { SkylerArtifact } from '@/lib/contracts/skyler'

export type ArtifactRecord = SkylerArtifact & {
  createdAt: number
}

export type MemoryRecord = {
  id: string
  title: string
  detail: string
  createdAt: number
}

export type ExecutionRecord = {
  id: string
  label: string
  detail: string
  createdAt: number
}

export type PinItem = {
  id: string
  type: 'artifact' | 'memory' | 'execution' | 'note'
  title: string
  detail: string
  refId?: string
  projectId?: string
  layoutMode?: 'docked' | 'floating'
  x?: number
  y?: number
  isMinimized?: boolean
}

type ActiveContextStore = {
  intent: string
  activeMode: ContextMode
  activeArtifactId: string | null
  artifacts: ArtifactRecord[]
  memories: MemoryRecord[]
  executions: ExecutionRecord[]
  pins: PinItem[]
  setIntent: (intent: string) => void
  setActiveMode: (mode: ContextMode) => void
  setActiveArtifactId: (id: string | null) => void
  addArtifact: (artifact: Omit<ArtifactRecord, 'createdAt'>) => void
  addMemory: (memory: Omit<MemoryRecord, 'createdAt'>) => void
  addExecution: (execution: Omit<ExecutionRecord, 'createdAt'>) => void
  pinItem: (item: PinItem) => void
  unpinItem: (id: string) => void
  clearTransient: () => void
}

function normalizePinItem(item: PinItem): PinItem {
  return {
    ...item,
    layoutMode: item.layoutMode ?? 'docked',
    isMinimized: item.isMinimized ?? false,
  }
}

export const useActiveContext = create<ActiveContextStore>()(
  persist(
    (set) => ({
      intent: '',
      activeMode: 'overview',
      activeArtifactId: null,
      artifacts: [],
      memories: [],
      executions: [],
      pins: [],
      setIntent: (intent) => set({ intent }),
      setActiveMode: (activeMode) => set({ activeMode }),
      setActiveArtifactId: (activeArtifactId) => set({ activeArtifactId }),
      addArtifact: (artifact) =>
        set((curr) => ({
          activeArtifactId: artifact.id,
          artifacts: [{ ...artifact, createdAt: Date.now() }, ...curr.artifacts.filter((item) => item.id !== artifact.id)].slice(0, 10),
          activeMode: 'artifacts',
        })),
      addMemory: (memory) =>
        set((curr) => ({
          memories: [{ ...memory, createdAt: Date.now() }, ...curr.memories.filter((item) => item.id !== memory.id)].slice(0, 10),
          activeMode: curr.activeMode === 'artifacts' ? curr.activeMode : 'memory',
        })),
      addExecution: (execution) =>
        set((curr) => ({
          executions: [{ ...execution, createdAt: Date.now() }, ...curr.executions.filter((item) => item.id !== execution.id)].slice(0, 12),
          activeMode: curr.activeArtifactId ? 'artifacts' : 'execution',
        })),
      pinItem: (item) =>
        set((curr) => ({
          pins: curr.pins.some((p) => p.id === item.id)
            ? curr.pins
            : [normalizePinItem(item), ...curr.pins].slice(0, 7),
        })),
      unpinItem: (id) => set((curr) => ({ pins: curr.pins.filter((item) => item.id !== id) })),
      clearTransient: () => set({ intent: '' }),
    }),
    {
      name: 'skyler-active-context-v1',
      partialize: (state) => ({
        activeArtifactId: state.activeArtifactId,
        pins: state.pins.map(normalizePinItem),
      }),
    },
  ),
)
