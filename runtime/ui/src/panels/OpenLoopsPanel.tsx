import React from "react";
import type { LoopItem } from "../lib/api";

type Props = {
  loops: LoopItem[];
  loopTitle: string;
  loading: boolean;
  onLoopTitleChange: (value: string) => void;
  onAddLoop: () => void;
};

export function OpenLoopsPanel({ loops, loopTitle, loading, onLoopTitleChange, onAddLoop }: Props) {
  return (
    <section style={styles.cardTall}>
      <div style={styles.cardHeaderRow}>
        <div style={styles.cardLabel}>Open loops</div>
        <div style={styles.badge}>{loops.length} active</div>
      </div>

      <div style={styles.addRow}>
        <input
          value={loopTitle}
          onChange={(e) => onLoopTitleChange(e.target.value)}
          style={styles.input}
          placeholder="Add a new open loop"
        />
        <button style={styles.primaryButton} onClick={onAddLoop} disabled={loading}>
          Add loop
        </button>
      </div>

      <div style={styles.signalList}>
        {loops.map((loop) => (
          <div key={loop.id} style={styles.signalItem}>
            <div style={styles.signalTitleRow}>
              <div style={styles.signalTitle}>{loop.title}</div>
              <div style={styles.signalSeverity}>{loop.priority}</div>
            </div>
            <div style={styles.signalDetail}>
              Owner: {loop.owner} - Status: {loop.status}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  cardTall: {
    background: "rgba(17, 24, 67, 0.78)",
    borderRadius: 24,
    padding: 24,
    minHeight: 320,
    boxShadow: "0 18px 60px rgba(0, 0, 0, 0.22)"
  },
  cardLabel: { fontSize: 24, opacity: 0.85, marginBottom: 18 },
  cardHeaderRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 18
  },
  badge: {
    borderRadius: 999,
    border: "1px solid rgba(238,242,255,0.24)",
    padding: "8px 14px",
    fontSize: 16
  },
  addRow: { display: "flex", gap: 12, marginBottom: 18 },
  input: {
    flex: 1,
    borderRadius: 14,
    padding: "14px 16px",
    fontSize: 18,
    border: "1px solid rgba(238,242,255,0.25)",
    background: "rgba(7, 17, 50, 0.92)",
    color: "#eef2ff"
  },
  primaryButton: {
    border: 0,
    borderRadius: 14,
    padding: "14px 18px",
    fontSize: 18,
    fontWeight: 700,
    cursor: "pointer"
  },
  signalList: { display: "grid", gap: 14 },
  signalItem: {
    borderRadius: 18,
    background: "rgba(7, 17, 50, 0.92)",
    padding: 16
  },
  signalTitleRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 8
  },
  signalTitle: { fontSize: 21, fontWeight: 700 },
  signalSeverity: { fontSize: 16, opacity: 0.72, textTransform: "uppercase" },
  signalDetail: { fontSize: 18, opacity: 0.88, lineHeight: 1.45 }
};
