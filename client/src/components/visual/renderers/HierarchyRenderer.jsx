import { buildHierarchyPositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

function HierarchyRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildHierarchyPositions(nodes, edges, visual.orientation);
  const markerId = `hierarchyrenderer-arrow-${nodes.map((node) => node.id).join("-")}`;
  const title = "Hierarchy / tree";
  return (
    <div className="cc-diagram-surface min-h-[400px]">
      <div className="cc-diagram-label">{title}</div>
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default HierarchyRenderer;
