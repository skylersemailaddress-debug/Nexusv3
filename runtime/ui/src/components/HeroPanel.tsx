import React from "react";

export function HeroPanel() {
  return (
    <section style={styles.hero}>
      <div style={styles.eyebrow}>NEXUS V3</div>
      <h1 style={styles.title}>Command Center Panel</h1>
      <p style={styles.subtitle}>Locked runtime with first data-backed workflow.</p>
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  hero: {
    background: "rgba(17, 24, 67, 0.78)",
    borderRadius: 28,
    padding: 28,
    boxShadow: "0 24px 80px rgba(0, 0, 0, 0.28)",
    marginBottom: 24
  },
  eyebrow: { fontSize: 16, opacity: 0.72, letterSpacing: "0.12em" },
  title: { fontSize: 58, lineHeight: 1.02, margin: "12px 0 10px", fontWeight: 800 },
  subtitle: { margin: 0, fontSize: 24, opacity: 0.9 }
};
