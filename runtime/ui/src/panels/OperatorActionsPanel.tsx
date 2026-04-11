import React from "react";

type Props = {
  loading: boolean;
  actionResult: string;
  onRefresh: () => void;
};

export function OperatorActionsPanel({ loading, actionResult, onRefresh }: Props) {
  return (
    <section style={styles.card}>
      <div style={styles.cardLabel}>Operator actions</div>
      <div style={styles.buttonRow}>
        <button style={styles.primaryButton} onClick={onRefresh} disabled={loading}>
          {loading ? "Working..." : "Refresh dashboard"}
        </button>
      </div>
      <div style={styles.support}>{actionResult}</div>
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
  buttonRow: { display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 20 },
  primaryButton: {
    border: 0,
    borderRadius: 14,
    padding: "14px 18px",
    fontSize: 18,
    fontWeight: 700,
    cursor: "pointer"
  },
  support: { fontSize: 22, opacity: 0.88, lineHeight: 1.4 }
};
