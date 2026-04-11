import { create } from "zustand";

type ProjectStore = {
  currentProjectId: string;
  setCurrentProjectId: (projectId: string) => void;
};

export const useProjectStore = create<ProjectStore>((set) => ({
  currentProjectId: "default",
  setCurrentProjectId: (projectId) => set({ currentProjectId: projectId }),
}));
