import { ChevronDown } from "lucide-react";
import ExplanationPanel from "./ExplanationPanel";

function CollapsibleExplanation({ explanation, source, modelUsed, groundingReport }) {
  return (
    <details className="cc-reading-drawer group">
      <summary>
        <div>
          <p className="cc-eyebrow">Optional reading</p>
          <p className="mt-1 text-sm font-medium text-gray-800">Open the complete written explanation</p>
        </div>
        <ChevronDown size={18} className="transition group-open:rotate-180" />
      </summary>
      <div className="cc-reading-drawer-body">
        <ExplanationPanel explanation={explanation} source={source} modelUsed={modelUsed} groundingReport={groundingReport} embedded />
      </div>
    </details>
  );
}

export default CollapsibleExplanation;
