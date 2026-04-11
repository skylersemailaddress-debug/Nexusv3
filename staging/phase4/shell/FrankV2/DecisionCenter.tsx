"use client"

import type { BuildContextResponse, SuggestedAction, MemoryItem } from "@/lib/types/domain"

function niceKind(kind?: string) {
  switch (kind) {
    case "next_step":
      return "Recommended next step"
    case "checkpoint":
      return "Saved milestone"
    case "workflow":
      return "Recommended plan"
    case "memory":
      return "Saved insight"
    case "ramble":
      return "Idea capture"
    default:
      return "Action"
  }
}

function HealthBadge({ value }: { value: string }) {
  const label = (value || "forming").trim()
  return (
    <div className="rounded-md border border-neutral-700 bg-neutral-900 px-2 py-0.5 text-[11px] uppercase tracking-wide text-neutral-200">
      {label}
    </div>
  )
}

function ActionList({ actions }: { actions: SuggestedAction[] }) {
  if (!actions.length) {
    return <p className="text-sm text-neutral-400">No recommended actions are surfaced yet.</p>
  }

  return (
    <div className="space-y-3">
      {actions.map((action, idx) => (
        <div key={action.id || `${action.title}-${idx}`} className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-neutral-100">{action.title}</div>
              {action.priority ? (
                <div className="mt-1 text-[11px] uppercase tracking-wide text-neutral-500">Priority: {action.priority}</div>
              ) : null}
            </div>
            <div className="rounded-md border border-neutral-700 px-2 py-0.5 text-[11px] uppercase tracking-wide text-neutral-300">
              {niceKind(action.kind)}
            </div>
          </div>
          {action.reason ? <p className="mt-2 text-sm text-neutral-400">{action.reason}</p> : null}
        </div>
      ))}
    </div>
  )
}

function MemoryList({ items }: { items: MemoryItem[] }) {
  if (!items.length) {
    return <p className="text-sm text-neutral-400">No saved insights are active for this project context.</p>
  }

  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={item.id || `${item.title}-${idx}`} className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-3">
          <div className="text-sm font-medium text-neutral-100">{item.title || "Saved insight"}</div>
          {item.content ? <p className="mt-2 text-sm text-neutral-400">{item.content}</p> : null}
        </div>
      ))}
    </div>
  )
}

function SimpleList({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) return <p className="text-sm text-neutral-400">{empty}</p>
  return (
    <ul className="space-y-2 text-sm text-neutral-300">
      {items.map((item, idx) => (
        <li key={`${item}-${idx}`} className="rounded-xl border border-neutral-800 bg-neutral-950/60 px-3 py-2">
          {item}
        </li>
      ))}
    </ul>
  )
}

function StatCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-3">
      <div className="text-[11px] uppercase tracking-wide text-neutral-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-neutral-100">{value}</div>
      {detail ? <div className="mt-1 text-xs text-neutral-500">{detail}</div> : null}
    </div>
  )
}

export function DecisionCenter({ context }: { context: BuildContextResponse }) {
  const blockers = (context.blockers || []).map((b) => (typeof b === "string" ? b : b?.title || b?.reason || "Open blocker"))
  const actions = context.next_suggested_actions || context.operator?.prioritized_actions || []
  const memoryItems = context.relevant_memory || []
  const keyDecisions = memoryItems.map((m) => m.title || "").filter(Boolean)
  const objectiveTitle =
    context.objective?.title ||
    context.operator?.richer_summary?.objective_title ||
    "No objective set."
  const nextStepTitle =
    context.next_step?.title ||
    context.operator?.richer_summary?.next_step_title ||
    "No next step resolved."
  const currentDirection = context.operator?.summary || nextStepTitle
  const workflowReadiness = context.operator?.richer_summary?.workflow_readiness || "forming"
  const checkpointTitle = context.continuity?.latest_checkpoint_title || context.latest_checkpoint?.title || null
  const topBlocker = context.operator?.richer_summary?.top_blocker || blockers[0] || "No active blockers are open."
  const memorySignalTitles = context.continuity?.memory_signal_titles || []
  const workflowChain = context.operator?.workflow_chain || []

  return (
    <aside className="w-full space-y-4">
      <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Decision Center</div>
          <HealthBadge value={workflowReadiness} />
        </div>
        <p className="mt-2 text-sm text-neutral-400">
          Clear direction, durable decisions, active blockers, saved insight, and the next best moves for this project.
        </p>
      </div>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Objective</div>
        <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3 text-sm text-neutral-100">
          {objectiveTitle}
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Current direction</div>
        <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3 text-sm text-neutral-100">
          {currentDirection}
        </div>
        <div className="mt-3 rounded-xl border border-dashed border-neutral-800 bg-neutral-950/40 p-3">
          <div className="text-[11px] uppercase tracking-wide text-neutral-500">Resolved next step</div>
          <div className="mt-1 text-sm text-neutral-300">{nextStepTitle}</div>
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Key decisions made</div>
        <div className="mt-3">
          <SimpleList items={keyDecisions} empty="No durable decisions have surfaced yet." />
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Risks and blockers</div>
        <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3">
          <div className="text-[11px] uppercase tracking-wide text-neutral-500">Top blocker</div>
          <div className="mt-1 text-sm text-neutral-100">{topBlocker}</div>
        </div>
        <div className="mt-3">
          <SimpleList items={blockers} empty="No active blockers are open." />
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Saved milestone</div>
        <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3 text-sm text-neutral-100">
          {checkpointTitle || "No saved milestone yet."}
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Saved insights</div>
        <div className="mt-3">
          <MemoryList items={memoryItems} />
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Recommended actions</div>
        <div className="mt-3">
          <ActionList actions={actions} />
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Build health</div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <StatCard label="Messages" value={context.continuity?.recent_message_count ?? 0} detail="Recent continuity captured" />
          <StatCard label="Saved insights" value={context.continuity?.memory_signal_count ?? 0} detail="Memory signals in context" />
          <StatCard label="Action queue" value={actions.length} detail="Recommended actions surfaced" />
          <StatCard label="Workflow chain" value={workflowChain.length} detail="Sequenced execution steps" />
        </div>

        <div className="mt-3 rounded-xl border border-dashed border-neutral-800 bg-neutral-950/40 p-3">
          <div className="text-[11px] uppercase tracking-wide text-neutral-500">Active signals</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(memorySignalTitles.length ? memorySignalTitles : ["No active signal titles yet."]).map((item, idx) => (
              <div
                key={`${item}-${idx}`}
                className="rounded-full border border-neutral-800 bg-neutral-950/60 px-2.5 py-1 text-xs text-neutral-300"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    </aside>
  )
}
