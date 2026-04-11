"use client";

export function TopBar({ title }: { title: string }) {
  return (
    <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
      <div>
        <div className="text-sm text-zinc-400">Workspace</div>
        <div className="font-medium">{title}</div>
      </div>
      <div className="text-xs text-zinc-500">ODP Operator</div>
    </div>
  );
}
