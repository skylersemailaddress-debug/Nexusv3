import { create } from "zustand";
import type { BuildContext } from "../types/domain";

type ContextStore = BuildContext & {
  setContext: (context: BuildContext) => void;
};

export const useContextStore = create<ContextStore>((set) => ({
  objective: null,
  next_step: null,
  recent_messages: [],
  memory: [],
  setContext: (context) => set(context),
}));
