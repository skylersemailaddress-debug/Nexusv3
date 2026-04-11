
export default function ArtifactBlock({ artifact }: any) {
  const rows = Array.isArray(artifact?.data) ? artifact.data : [];

  return (
    <div className="frank-card frank-card--artifact frank-hover-lift frank-focus-secondary">
      <div className="frank-meta-row">
        <span>Artifact • {artifact?.type || "unknown"}</span>
        <span>{artifact?.status || "draft"}</span>
      </div>

      <div className="frank-title">{artifact?.title || "Artifact Output"}</div>
      {artifact?.primary ? <div className="frank-body">{artifact.primary}</div> : null}

      {rows.length > 0 ? (
        <div className="frank-table">
          {rows.map((row: Record<string, any>, index: number) => (
            <div className="frank-row" key={index} style={{gridTemplateColumns: `repeat(${Object.keys(row).length}, 1fr)`}}>
              {Object.values(row).map((value, cellIndex) => (
                <div key={cellIndex}>{String(value)}</div>
              ))}
            </div>
          ))}
        </div>
      ) : null}

      {artifact?.secondary ? <div className="frank-subtle">{artifact.secondary}</div> : null}

      <div className="frank-actions">
        <button className="frank-btn frank-btn--primary">Open</button>
        <button className="frank-btn">Copy</button>
        <button className="frank-btn frank-btn--ghost">Export</button>
      </div>
    </div>
  );
}
