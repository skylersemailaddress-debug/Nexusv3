"use client";

import { useBuildContext } from "@/lib/hooks/queries";

function toText(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map(toText).filter(Boolean).join(", ");
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    return (
      toText(record.content) ||
      toText(record.title) ||
      toText(record.name) ||
      toText(record.description) ||
      JSON.stringify(record, null, 2)
    );
  }
  return String(value);
}

export function ContextPanel({ projectId }: { projectId: string }) {
  const { data, isLoading, error } = useBuildContext(projectId);
  const recentMessages = (data?.recent_messages ?? []).slice(0, 6);
  const relevantMemory = (data?.relevant_memory ?? []).slice(0, 4);

  return (
    <aside className="w-80 border-l border-zinc-800 p-4">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-zinc-400">Context</h2>

      {isLoading && <div className="text-sm text-zinc-500">Loading context...</div>}
      {error && <div className="text-sm text-red-400">Failed to load context.</div>}

      <div className="space-y-4">
        <section>
          <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Objective</div>
          <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
            {toText(data?.objective) || "No objective resolved yet."}
          </div>
        </section>

        <section>
          <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Next Step</div>
          <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
            {toText(data?.next_step) || "No next step resolved yet."}
          </div>
        </section>

        <section>
          <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Recent Messages</div>
          <div className="space-y-2">
            {recentMessages.map((message: any, index: number) => (
              <div key={message?.id ?? index} className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
                <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">
                  {toText(message?.role) || "item"}
                </div>
                <div className="whitespace-pre-wrap break-words">
                  {toText(message?.content ?? message)}
                </div>
              </div>
            ))}
            {recentMessages.length === 0 && (
              <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-500">
                No recent messages surfaced yet.
              </div>
            )}
          </div>
        </section>

        <section>
          <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">Relevant Memory</div>
          <div className="space-y-2">
            {relevantMemory.map((memory: any, index: number) => (
              <div key={memory?.id ?? index} className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm">
                <div className="mb-1 flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-zinc-500">
                  <span>{toText(memory?.scope) || "memory"}</span>
                  <span>{memory?.confidence != null ? `${Math.round(Number(memory.confidence) * 100)}%` : "active"}</span>
                </div>
                <div className="font-medium text-zinc-100">{toText(memory?.title) || "Memory"}</div>
                <div className="mt-1 whitespace-pre-wrap break-words text-zinc-300">
                  {toText(memory?.content ?? memory)}
                </div>
              </div>
            ))}
            {relevantMemory.length === 0 && (
              <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-500">
                No durable memory surfaced yet.
              </div>
            )}
          </div>
        </section>
      </div>
    </aside>
  );
}
