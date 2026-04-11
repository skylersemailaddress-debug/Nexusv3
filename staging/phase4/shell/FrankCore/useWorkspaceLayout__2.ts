'use client'

import { create } from 'zustand'

export type LayoutPreset = 'chat_only' | 'chat_context' | 'chat_artifact' | 'ops' | 'review'
export type PanelDock = 'hidden' | 'right' | 'bottom' | 'float' | 'chip'

export type PanelState = {
  dock: PanelDock
  collapsed: boolean
  x?: number
  y?: number
  width?: number
  height?: number
}

type WorkspaceLayoutState = {
  preset: LayoutPreset
  contextSurface: PanelState
  artifactPanel: PanelState
  setPreset: (preset: LayoutPreset) => void
  setContextSurfaceDock: (dock: PanelDock) => void
  setArtifactPanelDock: (dock: PanelDock) => void
  toggleContextSurfaceCollapsed: () => void
  toggleArtifactPanelCollapsed: () => void
}

export const useWorkspaceLayout = create<WorkspaceLayoutState>((set) => ({
  preset: 'chat_context',
  contextSurface: { dock: 'right', collapsed: false, width: 360 },
  artifactPanel: { dock: 'chip', collapsed: false },
  setPreset: (preset) => set({ preset }),
  setContextSurfaceDock: (dock) =>
    set((state) => ({ contextSurface: { ...state.contextSurface, dock } })),
  setArtifactPanelDock: (dock) =>
    set((state) => ({ artifactPanel: { ...state.artifactPanel, dock } })),
  toggleContextSurfaceCollapsed: () =>
    set((state) => ({ contextSurface: { ...state.contextSurface, collapsed: !state.contextSurface.collapsed } })),
  toggleArtifactPanelCollapsed: () =>
    set((state) => ({ artifactPanel: { ...state.artifactPanel, collapsed: !state.artifactPanel.collapsed } })),
}))
