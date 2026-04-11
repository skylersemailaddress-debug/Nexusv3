
export default function ApprovalBlock({ approval }: any) {
  return (
    <div className="frank-card frank-approval frank-focus-secondary frank-hover-lift">
      <div className="frank-meta-row">
        <span>Approval</span>
        <span>{approval?.status || "pending"}</span>
      </div>
      <div className="frank-title">Approval Required</div>
      <div className="frank-body">{approval?.scope || "No approval scope provided."}</div>

      <div className="frank-actions">
        <button className="frank-btn frank-btn--primary">Approve</button>
        <button className="frank-btn">Modify</button>
        <button className="frank-btn frank-btn--ghost">Reject</button>
      </div>
    </div>
  );
}
