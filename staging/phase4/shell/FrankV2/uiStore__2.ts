import { create } from "zustand";

export type WorkspaceMode = "ask" | "timeline" | "tools" | "review" | "studio" | "settings";

type RightPanel = "context" | "jobs" | "artifacts" | "logs";

type UIStore = {
  mode: WorkspaceMode;
  activeRightPanel: RightPanel;
  setMode: (mode: WorkspaceMode) => void;
  setActiveRightPanel: (panel: RightPanel) => void;
};

export const useUIStore = create<UIStore>((set) => ({
  mode: "ask",
  activeRightPanel: "context",
  setMode: (mode) => set({ mode }),
  setActiveRightPanel: (activeRightPanel) => set({ activeRightPanel }),
}));
