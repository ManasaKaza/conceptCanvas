import { getElementActivity, isTypedVisual } from "./visualModel";
import ComparisonRenderer from "./renderers/ComparisonRenderer";
import CycleRenderer from "./renderers/CycleRenderer";
import HierarchyRenderer from "./renderers/HierarchyRenderer";
import RadialRenderer from "./renderers/RadialRenderer";
import SequenceRenderer from "./renderers/SequenceRenderer";
import StackRenderer from "./renderers/StackRenderer";
import TimelineRenderer from "./renderers/TimelineRenderer";
import TypedFallbackRenderer from "./renderers/TypedFallbackRenderer";

function renderTypedDiagram(diagramType, rendererProps) {
  switch (diagramType) {
    case "sequence":
    case "flow":
    case "cause_effect":
      return <SequenceRenderer {...rendererProps} />;
    case "hierarchy":
    case "tree":
      return <HierarchyRenderer {...rendererProps} />;
    case "stack":
      return <StackRenderer {...rendererProps} />;
    case "comparison":
      return <ComparisonRenderer {...rendererProps} />;
    case "timeline":
    case "state_transition":
    case "code_execution":
      return <TimelineRenderer {...rendererProps} />;
    case "architecture":
    case "concept_map":
    case "spatial":
    case "formula":
      return <RadialRenderer {...rendererProps} />;
    case "cycle":
      return <CycleRenderer {...rendererProps} />;
    default:
      return <TypedFallbackRenderer {...rendererProps} />;
  }
}

function TypedVisualCanvas({ scene, timeline, activeSegmentIndex }) {
  if (!isTypedVisual(scene)) return null;

  const { revealedIds, activeIds } = getElementActivity(
    timeline,
    activeSegmentIndex,
  );

  return renderTypedDiagram(scene.visual.diagramType, {
    visual: scene.visual,
    revealedIds,
    activeIds,
  });
}

export default TypedVisualCanvas;
