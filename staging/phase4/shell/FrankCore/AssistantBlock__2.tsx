
export default function AssistantBlock({ content }: any) {
  return (
    <div className="frank-narrative">
      <div className="frank-narrative__label">System narrative</div>
      <div className="frank-narrative__body">{content}</div>
    </div>
  );
}
