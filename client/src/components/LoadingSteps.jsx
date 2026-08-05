import { LoaderCircle, X } from "lucide-react";

function LoadingSteps({ onCancel }) {
  return (
    <div className="cc-loading-strip" role="status" aria-live="polite">
      <LoaderCircle size={18} className="animate-spin" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-800">Building your lesson</p>
        <p className="mt-0.5 text-xs text-gray-500">Planning the explanation, visuals, narration, and quality checks.</p>
      </div>
      <button type="button" onClick={onCancel} className="cc-icon-button" aria-label="Cancel generation">
        <X size={16} />
      </button>
    </div>
  );
}

export default LoadingSteps;
