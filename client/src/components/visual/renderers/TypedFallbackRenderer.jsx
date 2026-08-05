import { AlertTriangle } from "lucide-react";
import { getNodeState, getVisualParts } from "../visualModel";

function TypedFallbackRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  return (
    <div className="cc-diagram-surface min-h-[360px] p-5 sm:p-7">
      <div className="cc-fallback-notice">
        <AlertTriangle size={18} />
        <div><strong>Simplified visual</strong><p>This topic does not yet have a specialised renderer. The explanation remains available without pretending this is a complete model.</p></div>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {nodes.map((node) => {
          const state = getNodeState(node.id, revealedIds, activeIds);
          return <div key={node.id} className={`cc-fallback-node is-${state}`}><strong>{node.label}</strong>{node.detail ? <small>{node.detail}</small> : null}</div>;
        })}
      </div>
      {edges.length ? <div className="mt-4 flex flex-wrap gap-2">{edges.map((edge) => <span key={edge.id} className="cc-edge-chip">{edge.label || `${edge.fromId} → ${edge.toId}`}</span>)}</div> : null}
    </div>
  );
}
export default TypedFallbackRenderer;
