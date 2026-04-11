"use client";

import { FormEvent, useState } from "react";
import { useSendMessage } from "@/lib/hooks/queries";

export function Composer({ projectId }: { projectId: string }) {
  const [value, setValue] = useState("");
  const mutation = useSendMessage(projectId);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next = value.trim();
    if (!next || mutation.isPending) return;
    setValue("");
    await mutation.mutateAsync(next);
  }

  return (
    <form onSubmit={onSubmit} className="border-t border-zinc-800 p-4">
      <div className="flex gap-3">
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Ask ODP, issue a command, or dump working context..."
          className="flex-1 rounded border border-zinc-700 bg-zinc-950 px-4 py-3 text-sm outline-none"
        />
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded border border-zinc-700 px-4 py-3 text-sm font-medium hover:bg-zinc-900 disabled:opacity-50"
        >
          {mutation.isPending ? "Running..." : "Send"}
        </button>
      </div>
      {mutation.error && (
        <div className="mt-2 text-sm text-red-400">{(mutation.error as Error).message}</div>
      )}
    </form>
  );
}
