import FlowScene from "./FlowScene";
import StackScene from "./StackScene";
import HighlightScene from "./HighlightScene";
import CompareScene from "./CompareScene";
import SplitScene from "./SplitScene";
import TimelineScene from "./TimelineScene";
import FallbackScene from "./FallbackScene";

const sceneRenderers = {
  flow: FlowScene,
  stack: StackScene,
  highlight: HighlightScene,
  compare: CompareScene,
  split: SplitScene,
  timeline: TimelineScene,
};

function SceneRenderer({ scene }) {
  const Renderer = sceneRenderers[scene.sceneType] || FallbackScene;

  return <Renderer scene={scene} />;
}

export default SceneRenderer;