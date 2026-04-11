
export default function Composer() {
  return (
    <div className="frank-composer-wrap">
      <div className="frank-composer">
        <div className="frank-composer__left">
          <div className="frank-composer__label">Intent Bar</div>
          <textarea
            placeholder='Ask FRANK… (e.g., "build a local transformer tool", "inspect runtime drift")'
            rows={1}
            defaultValue=""
          />
        </div>
        <button className="frank-btn frank-btn--primary frank-composer__button">Execute</button>
      </div>
      <div className="frank-shortcuts">
        <span>/build</span>
        <span>/inspect</span>
        <span>/promote</span>
        <span>/recall</span>
      </div>
    </div>
  );
}
