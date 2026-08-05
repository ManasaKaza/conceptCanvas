import { buildTwoColumnPositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

function ComparisonRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildTwoColumnPositions(nodes);
  const markerId = `comparisonrenderer-arrow-${nodes.map((node) => node.id).join("-")}`;
  const title = "Comparison";
  return (
    <div className="cc-diagram-surface min-h-[360px]">
      <div className="cc-diagram-label">{title}</div>
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default ComparisonRenderer;
