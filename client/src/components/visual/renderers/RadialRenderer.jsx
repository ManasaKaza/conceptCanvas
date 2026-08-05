import { buildRadialPositions, getVisualParts } from "../visualModel";
import { DiagramEdges, DiagramNode } from "./DiagramPrimitives";

const LABELS = {
  architecture: "Component architecture",
  concept_map: "Concept relationships",
  spatial: "Spatial schematic",
  formula: "Quantitative relationship",
};

function RadialRenderer({ visual, revealedIds, activeIds }) {
  const { nodes, edges } = getVisualParts(visual);
  const positions = buildRadialPositions(nodes);
  const markerId = `radial-arrow-${nodes.map((node) => node.id).join("-")}`;
  return (
    <div className="cc-diagram-surface min-h-[420px]">
      <div className="cc-diagram-label">{LABELS[visual.diagramType] || "Relationship map"}</div>
      {visual.diagramType === "spatial" ? <div className="cc-diagram-note">Schematic, not a geographic map</div> : null}
      <DiagramEdges edges={edges} positions={positions} revealedIds={revealedIds} activeIds={activeIds} markerId={markerId} />
      {nodes.map((node) => <DiagramNode key={node.id} node={node} position={positions[node.id]} revealedIds={revealedIds} activeIds={activeIds} />)}
    </div>
  );
}
export default RadialRenderer;
