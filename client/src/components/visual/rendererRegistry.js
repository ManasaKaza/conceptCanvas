import ComparisonRenderer from "./renderers/ComparisonRenderer";
import CycleRenderer from "./renderers/CycleRenderer";
import HierarchyRenderer from "./renderers/HierarchyRenderer";
import RadialRenderer from "./renderers/RadialRenderer";
import SequenceRenderer from "./renderers/SequenceRenderer";
import StackRenderer from "./renderers/StackRenderer";
import TimelineRenderer from "./renderers/TimelineRenderer";
import TypedFallbackRenderer from "./renderers/TypedFallbackRenderer";

const rendererRegistry = {
  sequence: SequenceRenderer,
  flow: SequenceRenderer,
  hierarchy: HierarchyRenderer,
  tree: HierarchyRenderer,
  stack: StackRenderer,
  comparison: ComparisonRenderer,
  timeline: TimelineRenderer,
  state_transition: TimelineRenderer,
  code_execution: TimelineRenderer,
  architecture: RadialRenderer,
  concept_map: RadialRenderer,
  spatial: RadialRenderer,
  formula: RadialRenderer,
  cycle: CycleRenderer,
  cause_effect: SequenceRenderer,
};

export function getRenderer(diagramType) {
  return rendererRegistry[diagramType] || TypedFallbackRenderer;
}

export function getRegisteredDiagramTypes() {
  return Object.keys(rendererRegistry);
}
