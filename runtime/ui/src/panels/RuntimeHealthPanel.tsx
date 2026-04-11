import React from "react";
import type { DashboardStatus, HealthResponse } from "../lib/api";

type Props = {
  health: HealthResponse | null;
  status: DashboardStatus | null;
};

export function RuntimeHealthPanel({ health, status }: Props) {
  return (
    <section style={styles.card}>
      <div style={styles.cardLabel}>Runtime health</div>
      <div style={styles.metric}>{health?.status ?? "loading"}</div>
      <div style={styles.support}>
        {status?.system ?? "nexus"} - {status?.status ?? "unknown"} - {status?.runtime ?? "unknown"}
      </div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "rgba(17, 24, 67, 0.78)",
    borderRadius: 24,
    padding: 24,
    minHeight: 180,
    boxShadow: "0 18px 60px rgba(0, 0, 0, 0.22)"
  },
  cardLabel: { fontSize: 24, opacity: 0.85, marginBottom: 18 },
  metric: { fontSize: 54, fontWeight: 800, marginBottom: 10 },
  support: { fontSize: 22, opacity: 0.88, lineHeight: 1.4 }
};
