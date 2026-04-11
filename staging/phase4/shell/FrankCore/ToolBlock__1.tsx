
export default function ToolBlock({ tool }: any) {
  return (
    <div className="frank-card frank-card--tool frank-focus-primary frank-hover-lift">
      <div className="frank-meta-row">
        <span>Tool</span>
        <span>{tool?.status || "idle"}</span>
      </div>

      <div className="frank-title">{tool?.name || "Untitled Tool"}</div>
      {tool?.primary ? <div className="frank-body">{tool.primary}</div> : null}
      {tool?.secondary ? <div className="frank-subtle">{tool.secondary}</div> : null}
      {tool?.status === "running" ? <div className="frank-running-bar" /> : null}

      <div className="frank-actions">
        <button className="frank-btn frank-btn--primary">Inspect</button>
        <button className="frank-btn">Modify</button>
        <button className="frank-btn frank-btn--ghost">Logs</button>
      </div>
    </div>
  );
}
