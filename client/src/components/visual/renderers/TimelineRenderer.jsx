import { buildLinearPositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

function TimelineRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildLinearPositions(nodes, "top_to_bottom");
  const markerId = `timelinerenderer-arrow-${nodes.map((node) => node.id).join("-")}`;
  const title = visual.diagramType === "code_execution" ? "Execution trace" : visual.diagramType === "state_transition" ? "State transitions" : "Timeline";
  return (
    <div className="cc-diagram-surface min-h-[430px]">
      <div className="cc-diagram-label">{title}</div>
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default TimelineRenderer;
