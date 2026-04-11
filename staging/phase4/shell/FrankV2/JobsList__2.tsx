"use client";

import { useRecentJobs } from "@/lib/hooks/queries";

export function JobsList() {
  const { data, isLoading } = useRecentJobs();

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Recent Jobs</h2>
      {isLoading && <div className="text-sm text-zinc-500">Loading jobs...</div>}
      {(data ?? []).map((job) => (
        <div key={job.id} className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
          <div className="font-medium">{job.kind ?? job.id}</div>
          <div className="text-zinc-500">{job.status ?? "unknown"}</div>
        </div>
      ))}
    </div>
  );
}
