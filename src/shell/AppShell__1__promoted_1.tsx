import { LeftNav } from "./LeftNav";
import { TopBar } from "./TopBar";
import { ContextPanel } from "@/components/panels/ContextPanel";
import { Composer } from "@/components/composer/Composer";

export function AppShell({
  projectId,
  title,
  children,
}: {
  projectId: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <LeftNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} />
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-auto p-6">{children}</main>
          <ContextPanel projectId={projectId} />
        </div>
        <Composer projectId={projectId} />
      </div>
    </div>
  );
}
