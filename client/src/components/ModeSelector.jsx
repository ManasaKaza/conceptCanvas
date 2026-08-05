import { AlignLeft, MonitorPlay } from "lucide-react";

function ModeSelector({ mode, onModeChange, disabled = false }) {
  return (
    <div className="cc-segmented-control" aria-label="Lesson format">
      <button
        type="button"
        onClick={() => onModeChange("text")}
        disabled={disabled}
        aria-pressed={mode === "text"}
        className={mode === "text" ? "is-active" : ""}
      >
        <AlignLeft size={15} />
        Text
      </button>
      <button
        type="button"
        onClick={() => onModeChange("visual")}
        disabled={disabled}
        aria-pressed={mode === "visual"}
        className={mode === "visual" ? "is-active" : ""}
      >
        <MonitorPlay size={15} />
        Visual
      </button>
    </div>
  );
}

export default ModeSelector;
