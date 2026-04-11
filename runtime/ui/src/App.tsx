import { useEffect, useState } from "react";
import { HeroPanel } from "./components/HeroPanel";
import { RuntimeHealthPanel } from "./panels/RuntimeHealthPanel";
import { OperatorActionsPanel } from "./panels/OperatorActionsPanel";
import { OpenLoopsPanel } from "./panels/OpenLoopsPanel";
import { OperatorBriefPanel } from "./panels/OperatorBriefPanel";
import { addOpenLoop, fetchDashboard, refreshDashboard } from "./lib/api";
import type { BriefResponse, DashboardStatus, HealthResponse, LoopItem, Signal } from "./lib/api";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [loops, setLoops] = useState<LoopItem[]>([]);
  const [loopTitle, setLoopTitle] = useState("Follow up on first commercial workflow");
  const [actionResult, setActionResult] = useState("No action executed yet.");
  const [loading, setLoading] = useState(false);

  async function loadDashboard() {
    const data = await fetchDashboard();
    setHealth(data.health);
    setStatus(data.status);
    setSignals(data.signals);
    setBrief(data.brief);
    setLoops(data.loops);
  }

  async function runRefresh() {
    setLoading(true);
    try {
      const data = await refreshDashboard();
      setActionResult(data.result ? `${data.result} @ ${data.refreshed_at ?? ""}` : "Refresh completed.");
      await loadDashboard();
    } catch (err) {
      setActionResult(`Refresh failed: ${String(err)}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddLoop() {
    setLoading(true);
    try {
      const data = await addOpenLoop(loopTitle);
      setActionResult(data.result ? `${data.result}: ${data.item?.title ?? ""}` : "Open loop added.");
      await loadDashboard();
    } catch (err) {
      setActionResult(`Add open loop failed: ${String(err)}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard().catch((err) => {
      setActionResult(`Dashboard load failed: ${String(err)}`);
    });
  }, []);

  return (
    <div style={styles.page}>
      <div style={styles.shell}>
        <HeroPanel />

        <div style={styles.grid}>
          <RuntimeHealthPanel health={health} status={status} />
          <OperatorActionsPanel loading={loading} actionResult={actionResult} onRefresh={runRefresh} />
        </div>

        <div style={styles.grid}>
          <OpenLoopsPanel
            loops={loops}
            loopTitle={loopTitle}
            loading={loading}
            onLoopTitleChange={setLoopTitle}
            onAddLoop={handleAddLoop}
          />
          <OperatorBriefPanel brief={brief} signals={signals} />
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(180deg, #04091c 0%, #071132 100%)",
    color: "#eef2ff",
    fontFamily: "Inter, system-ui, sans-serif",
    padding: "40px 24px"
  },
  shell: { maxWidth: 1180, margin: "0 auto" },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }
};

export default App;
