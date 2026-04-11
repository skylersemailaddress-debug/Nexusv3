"use client"

type NoviceModeProps = {
  projectName?: string
  objective?: string
  blockers?: string[]
  nextMove?: string
  assets?: string[]
  openQuestions?: string[]
  readiness?: string
}

function SectionCard({
  title,
  body,
  hint,
}: {
  title: string
  body: string
  hint?: string
}) {
  return (
    <section className="rounded-2xl border border-neutral-800 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-neutral-900">{title}</div>
      <p className="mt-2 text-sm leading-6 text-neutral-700">{body}</p>
      {hint ? <div className="mt-3 text-xs text-neutral-500">{hint}</div> : null}
    </section>
  )
}

function BulletList({
  title,
  items,
  empty,
}: {
  title: string
  items: string[]
  empty: string
}) {
  return (
    <section className="rounded-2xl border border-neutral-800 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-neutral-900">{title}</div>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm text-neutral-700">
          {items.map((item, idx) => (
            <li key={`${title}-${idx}`} className="rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm leading-6 text-neutral-700">{empty}</p>
      )}
    </section>
  )
}

function PromptCard({
  title,
  prompt,
}: {
  title: string
  prompt: string
}) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-neutral-500">{title}</div>
      <div className="mt-2 text-sm leading-6 text-neutral-800">{prompt}</div>
    </div>
  )
}

function SortCard({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-neutral-500">{label}</div>
      <div className="mt-2 text-sm leading-6 text-neutral-800">{value}</div>
    </div>
  )
}

export function NoviceMode({
  projectName = "This project",
  objective = "Clarify what you are trying to build.",
  blockers = [],
  nextMove = "Capture the first useful version of the problem in plain language.",
  assets = [],
  openQuestions = [],
  readiness = "forming",
}: NoviceModeProps) {
  const activeBlocker = blockers[0] || "No blocker is captured yet."
  const readinessCopy =
    readiness === "ready"
      ? "This project looks ready for the next execution step."
      : readiness === "partial"
        ? "This project is partly ready, but still needs a few important decisions."
        : "This project is still forming and needs more structure before a push forward."

  const assetSummary = assets.length
    ? `${assets.length} useful project item${assets.length === 1 ? "" : "s"} already surfaced.`
    : "No clear project assets are surfaced yet."

  const questionSummary = openQuestions.length
    ? `${openQuestions.length} open question${openQuestions.length === 1 ? "" : "s"} still need answers.`
    : "No major open questions are surfaced yet."

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-neutral-200 bg-gradient-to-b from-white to-neutral-50 p-5 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">Novice Mode</div>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-neutral-950">Guided Builder</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-700">
          A plain-language path for turning rough ideas into a usable project shape without exposing dense operator controls.
        </p>
        <div className="mt-4 rounded-2xl border border-neutral-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-neutral-500">Project</div>
          <div className="mt-1 text-base font-medium text-neutral-950">{projectName}</div>
        </div>
      </div>

      <section className="rounded-2xl border border-neutral-800 bg-white p-4 shadow-sm">
        <div className="text-sm font-semibold text-neutral-900">Quick start prompts</div>
        <p className="mt-2 text-sm leading-6 text-neutral-700">
          Use these plain-language prompts to turn rough input into a workable project shape.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <PromptCard
            title="Start here"
            prompt="What are you trying to build, in one or two plain sentences?"
          />
          <PromptCard
            title="Useful context"
            prompt="What do you already have, and what is missing right now?"
          />
          <PromptCard
            title="Next move"
            prompt="What is the single most useful thing to do next?"
          />
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-white p-4 shadow-sm">
        <div className="text-sm font-semibold text-neutral-900">Messy input sorted into a project shape</div>
        <p className="mt-2 text-sm leading-6 text-neutral-700">
          This view turns rough notes into a simple project picture: goal, blockers, assets, open questions, and the next move.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <SortCard label="Goal" value={objective} />
          <SortCard label="Main blocker" value={activeBlocker} />
          <SortCard label="Assets" value={assetSummary} />
          <SortCard label="Open questions" value={questionSummary} />
        </div>
      </section>

      <SectionCard
        title="Current working picture"
        body={`You are building: ${objective} Main blocker: ${activeBlocker} Current next move: ${nextMove}`}
        hint="This is the simple project shape the system can refine over time."
      />

      <SectionCard
        title="1. What are you trying to build?"
        body={objective}
        hint="Describe the goal in one or two plain sentences."
      />

      <SectionCard
        title="2. What do you already have?"
        body={assets.length ? "These are the main things already in place for this project." : "Collect rough notes, links, decisions, drafts, assets, and any previous work that already exists."}
        hint="Messy input is fine. The system should sort it later."
      />

      <BulletList
        title="Project map"
        items={[
          `Goal: ${objective}`,
          `Main blocker: ${activeBlocker}`,
          `Next move: ${nextMove}`,
          ...assets.slice(0, 2).map((item) => `Asset: ${item}`),
          ...openQuestions.slice(0, 2).map((item) => `Open question: ${item}`),
        ]}
        empty="The project map will appear here once more structure is captured."
      />

      <SectionCard
        title="3. What is blocking you?"
        body={activeBlocker}
        hint="Start with the single biggest blocker instead of listing everything."
      />

      <SectionCard
        title="4. What matters most right now?"
        body={nextMove}
        hint="This becomes the immediate next move for the guided builder flow."
      />

      <BulletList
        title="5. What do you already have?"
        items={assets}
        empty="No project assets are surfaced yet."
      />

      <BulletList
        title="6. Open questions"
        items={openQuestions}
        empty="No open questions are surfaced yet."
      />

      <SectionCard
        title="7. Readiness snapshot"
        body={readinessCopy}
        hint={`Current status: ${readiness}`}
      />

      <SectionCard
        title="8. Suggested next move"
        body={nextMove}
        hint="Recommend one clear action, not a long queue."
      />
    </div>
  )
}
