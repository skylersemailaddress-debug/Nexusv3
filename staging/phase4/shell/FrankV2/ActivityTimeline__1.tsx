"use client";

import { useActivityTimeline } from "@/lib/hooks/queries";

function toneFor(eventType: string): string {
  switch (eventType) {
    case "message":
      return "border-sky-900/60 bg-sky-950/30 text-sky-300";
    case "job":
      return "border-emerald-900/60 bg-emerald-950/30 text-emerald-300";
    case "artifact":
      return "border-amber-900/60 bg-amber-950/30 text-amber-300";
    default:
      return "border-zinc-800 bg-zinc-950 text-zinc-300";
  }
}

function formatTime(value?: string): string {
  if (!value) return "Unknown time";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function ActivityTimeline({ projectId }: { projectId: string }) {
  const { data, isLoading, error } = useActivityTimeline(projectId);

  return (
    <section className="rounded border border-zinc-800 bg-zinc-900/50 p-4 lg:col-span-2">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Activity Timeline</h2>
          <p className="text-sm text-zinc-500">Unified operator history across messages, jobs, and artifacts.</p>
        </div>
        <div className="text-xs text-zinc-500">
          Total: {data?.counts?.total ?? 0} · Messages: {data?.counts?.messages ?? 0} · Jobs: {data?.counts?.jobs ?? 0} · Artifacts: {data?.counts?.artifacts ?? 0}
        </div>
      </div>

      {isLoading && <div className="text-sm text-zinc-500">Loading activity...</div>}
      {error && <div className="text-sm text-red-400">Failed to load activity timeline.</div>}

      <div className="space-y-3">
        {(data?.items ?? []).map((item) => (
          <div key={`${item.event_type}-${item.id}`} className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div className="font-medium text-zinc-100">{item.title ?? item.id}</div>
              <div className="text-xs text-zinc-500">{formatTime(item.created_at)}</div>
            </div>
            <div className="mb-2 flex flex-wrap gap-2">
              <span className={`rounded border px-2 py-1 text-xs uppercase tracking-wide ${toneFor(item.event_type)}`}>
                {item.event_type}
              </span>
              <span className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs uppercase tracking-wide text-zinc-400">
                {item.status ?? "unknown"}
              </span>
            </div>
            <div className="whitespace-pre-wrap break-words text-zinc-300">
              {item.summary || "No summary captured yet."}
            </div>
          </div>
        ))}
        {!isLoading && (data?.items?.length ?? 0) === 0 && (
          <div className="rounded border border-dashed border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-500">
            No activity yet. Send a message or trigger orchestration to populate the timeline.
          </div>
        )}
      </div>
    </section>
  );
}
