function ModeSelector({ mode, onModeChange, disabled = false }) {
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onModeChange("text")}
        disabled={disabled}
        className={`rounded-xl px-4 py-2 text-sm font-semibold ${
          mode === "text"
            ? "bg-blue-900 text-white"
            : "border border-gray-200 bg-white text-gray-600"
        } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
      >
        Text Only
      </button>

      <button
        onClick={() => onModeChange("visual")}
        disabled={disabled}
        className={`rounded-xl px-4 py-2 text-sm font-semibold ${
          mode === "visual"
            ? "bg-blue-900 text-white"
            : "border border-gray-200 bg-white text-gray-600"
        } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
      >
        Text + Visual
      </button>
    </div>
  );
}

export default ModeSelector;