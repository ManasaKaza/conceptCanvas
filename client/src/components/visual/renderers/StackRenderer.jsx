import { ArrowDown, CornerDownLeft, Layers3 } from "lucide-react";
import { getEdgeState, getNodeState, getRelationLabel, getVisualParts } from "../visualModel";

function StackNode({ node, revealedIds, activeIds }) {
  const state = getNodeState(node.id, revealedIds, activeIds);
  return (
    <div className={`cc-stack-node is-${state}`} data-element-id={node.id}>
      <div><Layers3 size={16} aria-hidden="true" /><span>{node.label}</span></div>
      {node.detail ? <small>{node.detail}</small> : null}
    </div>
  );
}

function StackRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const frameNodes = nodes.filter((node) => node.nodeKind === "stack_frame");
  const orderedNodes = frameNodes.length ? frameNodes : nodes;
  const surroundingNodes = frameNodes.length ? nodes.filter((node) => node.nodeKind !== "stack_frame") : [];

  return (
    <div className="cc-diagram-surface min-h-[400px] p-5 sm:p-7">
      <div className="mb-5 flex items-center justify-between gap-3">
        <span className="cc-diagram-label static">Call stack</span>
        <span className="text-xs text-gray-400">Newest frame appears on top</span>
      </div>
      <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_220px] md:items-center">
        <div className="mx-auto w-full max-w-md">
          <div className="cc-stack-shell">
            <div className="cc-stack-caption">Active frames</div>
            <div className="flex flex-col-reverse gap-2">
              {orderedNodes.map((node) => <StackNode key={node.id} node={node} revealedIds={revealedIds} activeIds={activeIds} />)}
            </div>
            <div className="cc-stack-base">Stack base</div>
          </div>
        </div>
        <div className="space-y-2">
          {surroundingNodes.length > 0 ? surroundingNodes.map((node) => <StackNode key={node.id} node={node} revealedIds={revealedIds} activeIds={activeIds} />) : <p className="cc-diagram-helper">Each call waits until the deeper call returns.</p>}
          {edges.map((edge) => {
            const state = getEdgeState(edge, revealedIds, activeIds);
            return (
              <div key={edge.id} className={`cc-stack-edge is-${state}`}>
                {edge.relation === "returns" ? <CornerDownLeft size={15} /> : <ArrowDown size={15} />}
                <span>{edge.label || getRelationLabel(edge.relation)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export default StackRenderer;
