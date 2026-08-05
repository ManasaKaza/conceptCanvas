import { buildLinearPositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

function SequenceRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildLinearPositions(nodes, visual.orientation);
  const markerId = `sequencerenderer-arrow-${nodes.map((node) => node.id).join("-")}`;
  const title = visual.diagramType === "flow" ? "Data flow" : "Sequence";
  return (
    <div className="cc-diagram-surface min-h-[360px]">
      <div className="cc-diagram-label">{title}</div>
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default SequenceRenderer;
