import { create } from "zustand";
import type { BuildContext } from "../types/domain";

type ContextStore = BuildContext & {
  setContext: (context: BuildContext) => void;
};

export const useContextStore = create<ContextStore>((set) => ({
  project_id: "default",
  objective: null,
  next_step: null,
  recent_messages: [],
  relevant_memory: [],
  setContext: (context) => set(context),
}));
