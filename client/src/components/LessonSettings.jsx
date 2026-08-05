import { SlidersHorizontal } from "lucide-react";

function SelectField({ label, value, onChange, disabled, children }) {
  return (
    <label className="cc-setting-field">
      <span>{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        {children}
      </select>
    </label>
  );
}

function LessonSettings({
  mode,
  audienceLevel,
  onAudienceLevelChange,
  explanationDepth,
  onExplanationDepthChange,
  requestedSceneCount,
  onRequestedSceneCountChange,
  groundingMode,
  onGroundingModeChange,
  disabled = false,
}) {
  return (
    <details className="cc-settings-panel">
      <summary>
        <SlidersHorizontal size={15} />
        Lesson settings
      </summary>
      <div className="cc-settings-grid">
        <SelectField label="Level" value={audienceLevel} onChange={onAudienceLevelChange} disabled={disabled}>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </SelectField>

        <SelectField label="Depth" value={explanationDepth} onChange={onExplanationDepthChange} disabled={disabled}>
          <option value="focused">Focused</option>
          <option value="standard">Standard</option>
          <option value="deep">Deep</option>
        </SelectField>

        <SelectField label="Sources" value={groundingMode} onChange={onGroundingModeChange} disabled={disabled}>
          <option value="preferred">Preferred</option>
          <option value="required">Required</option>
          <option value="off">Off</option>
        </SelectField>

        {mode === "visual" && (
          <SelectField
            label="Scenes"
            value={requestedSceneCount == null ? "auto" : String(requestedSceneCount)}
            onChange={(value) => onRequestedSceneCountChange(value === "auto" ? null : Number(value))}
            disabled={disabled}
          >
            <option value="auto">Auto</option>
            {[3, 4, 5, 6, 7].map((count) => (
              <option key={count} value={count}>Exactly {count}</option>
            ))}
          </SelectField>
        )}
      </div>
    </details>
  );
}

export default LessonSettings;
