"use client";

import { useArtifacts } from "@/lib/hooks/queries";

export function ArtifactList({ projectId }: { projectId: string }) {
  const { data, isLoading } = useArtifacts(projectId);

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Artifacts</h2>
      {isLoading && <div className="text-sm text-zinc-500">Loading artifacts...</div>}
      {(data ?? []).map((artifact) => (
        <div key={artifact.id} className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
          <div className="font-medium">{artifact.name ?? artifact.id}</div>
          <div className="text-zinc-500">{artifact.type ?? "unknown"}</div>
        </div>
      ))}
    </div>
  );
}
