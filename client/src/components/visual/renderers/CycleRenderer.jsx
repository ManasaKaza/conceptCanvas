import { buildCyclePositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

function CycleRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildCyclePositions(nodes);
  const markerId = `cyclerenderer-arrow-${nodes.map((node) => node.id).join("-")}`;
  const title = "Repeating cycle";
  return (
    <div className="cc-diagram-surface min-h-[420px]">
      <div className="cc-diagram-label">{title}</div>
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default CycleRenderer;
