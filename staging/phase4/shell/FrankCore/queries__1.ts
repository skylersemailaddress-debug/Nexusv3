"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getProjectResume } from "../api/projects";
import { buildContext } from "../api/state";
import { appendMessage, orchestrateAction } from "../api/messages";
import { getRecentJobs } from "../api/jobs";
import { getArtifacts } from "../api/artifacts";
import { getActivity } from "../api/activity";

export function useProjectResume(projectId: string) {
  return useQuery({
    queryKey: ["project-resume", projectId],
    queryFn: () => getProjectResume(projectId),
    enabled: Boolean(projectId),
  });
}

export function useBuildContext(projectId: string) {
  return useQuery({
    queryKey: ["build-context", projectId],
    queryFn: () => buildContext(projectId),
    enabled: Boolean(projectId),
    refetchInterval: 15000,
  });
}

export function useRecentJobs() {
  return useQuery({
    queryKey: ["jobs-recent"],
    queryFn: getRecentJobs,
    refetchInterval: 5000,
  });
}

export function useArtifacts(projectId: string) {
  return useQuery({
    queryKey: ["artifacts", projectId],
    queryFn: () => getArtifacts(projectId),
    enabled: Boolean(projectId),
    refetchInterval: 10000,
  });
}

export function useActivityTimeline(projectId: string) {
  return useQuery({
    queryKey: ["activity", projectId],
    queryFn: () => getActivity(projectId),
    enabled: Boolean(projectId),
    refetchInterval: 5000,
  });
}

export function useSendMessage(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (content: string) => {
      await appendMessage(projectId, content);
      return orchestrateAction(projectId, content);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["project-resume", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["build-context", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["jobs-recent"] }),
        queryClient.invalidateQueries({ queryKey: ["artifacts", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["activity", projectId] }),
      ]);
    },
  });
}
