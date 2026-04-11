"use client";

import { useEffect } from "react";
import { useProjectStore } from "@/lib/stores/projectStore";

export function BootProjectProvider({ projectId }: { projectId: string }) {
  const setCurrentProjectId = useProjectStore((state) => state.setCurrentProjectId);

  useEffect(() => {
    setCurrentProjectId(projectId);
  }, [projectId, setCurrentProjectId]);

  return null;
}
