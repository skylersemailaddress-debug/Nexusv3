
export default function SystemBlock({ content = "System event" }: any) {
  return (
    <div className="frank-card frank-card--secondary frank-focus-background">
      <div className="frank-meta-row">
        <span>System</span>
      </div>
      <div className="frank-body">{content}</div>
    </div>
  );
}
