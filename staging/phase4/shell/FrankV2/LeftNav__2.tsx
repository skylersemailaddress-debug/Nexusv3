"use client";

import Link from "next/link";
import { useProjectStore } from "@/lib/stores/projectStore";

export function LeftNav() {
  const { currentProjectId } = useProjectStore();

  return (
    <aside className="w-64 border-r border-zinc-800 p-4">
      <div className="mb-6 text-lg font-semibold">ODP</div>
      <nav className="space-y-2 text-sm">
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}`}>Ask</Link>
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}/timeline`}>Timeline</Link>
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}/tools`}>Tools</Link>
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}/review`}>Review</Link>
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}/studio`}>Studio</Link>
        <Link className="block rounded px-3 py-2 hover:bg-zinc-900" href={`/projects/${currentProjectId}/settings`}>Settings</Link>
      </nav>
    </aside>
  );
}
