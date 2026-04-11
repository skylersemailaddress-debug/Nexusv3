import React from "react";
import type { BriefResponse, Signal } from "../lib/api";

type Props = {
  brief: BriefResponse | null;
  signals: Signal[];
};

export function OperatorBriefPanel({ brief, signals }: Props) {
  return (
    <section style={styles.cardTall}>
      <div style={styles.cardLabel}>Operator brief</div>
      <div style={styles.briefHeadline}>{brief?.headline ?? "Loading brief..."}</div>
      <div style={styles.briefText}>{brief?.summary ?? ""}</div>
      <div style={styles.briefNext}>Next action: {brief?.next_action ?? "Loading..."}</div>

      <div style={{ height: 20 }} />

      <div style={styles.cardLabel}>Live signals</div>
      <div style={styles.signalList}>
        {signals.map((signal) => (
          <div key={signal.id} style={styles.signalItem}>
            <div style={styles.signalTitleRow}>
              <div style={styles.signalTitle}>{signal.title}</div>
              <div style={styles.signalSeverity}>{signal.severity}</div>
            </div>
            <div style={styles.signalDetail}>{signal.detail}</div>
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
  briefHeadline: { fontSize: 30, fontWeight: 800, marginBottom: 12 },
  briefText: { fontSize: 21, lineHeight: 1.55, opacity: 0.9, marginBottom: 18 },
  briefNext: { fontSize: 20, fontWeight: 700 },
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
