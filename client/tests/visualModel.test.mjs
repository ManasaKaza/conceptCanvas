import test from "node:test";
import assert from "node:assert/strict";
import {
  buildCyclePositions,
  buildHierarchyPositions,
  buildLinearPositions,
  buildRadialPositions,
  buildTwoColumnPositions,
  getElementActivity,
  getVisualParts,
  isTypedVisual,
} from "../src/components/visual/visualModel.js";
import { getSceneTimeline } from "../src/utils/sceneUtils.js";

const typedScene = {
  visual: {
    schemaVersion: "2.0",
    diagramType: "sequence",
    orientation: "left_to_right",
    elements: [
      { type: "node", id: "client", label: "Client", nodeKind: "client" },
      { type: "node", id: "server", label: "Server", nodeKind: "server" },
      { type: "edge", id: "request", fromId: "client", toId: "server", relation: "request" },
    ],
  },
  narrationSegments: [{
    id: "segment_1",
    order: 1,
    spokenText: "The client sends a request to the server.",
    subtitleText: "Client sends request",
    targetElementIds: ["client", "server", "request"],
    action: "trace",
    estimatedDurationMs: 3200,
    claimIds: ["claim_1"],
    sourceIds: ["source_one"],
  }],
};

test("recognises LessonV2 typed visuals", () => {
  assert.equal(isTypedVisual(typedScene), true);
  assert.equal(isTypedVisual({ visual: { elements: [] } }), false);
});

test("splits nodes and edges from a typed visual", () => {
  const parts = getVisualParts(typedScene.visual);
  assert.equal(parts.nodes.length, 2);
  assert.equal(parts.edges.length, 1);
});

test("maps a horizontal sequence to ordered positions", () => {
  const positions = buildLinearPositions(getVisualParts(typedScene.visual).nodes, "left_to_right");
  assert.ok(positions.client.x < positions.server.x);
  assert.equal(positions.client.y, positions.server.y);
});

test("maps a vertical hierarchy from root to leaf", () => {
  const positions = buildHierarchyPositions(
    [{ id: "root" }, { id: "branch" }, { id: "leaf" }],
    [{ fromId: "root", toId: "branch" }, { fromId: "branch", toId: "leaf" }],
    "top_to_bottom",
  );
  assert.ok(positions.root.y < positions.branch.y);
  assert.ok(positions.branch.y < positions.leaf.y);
});

test("reveals previous targets and activates the current segment", () => {
  const activity = getElementActivity([
    { targetElementIds: ["client"] },
    { targetElementIds: ["server", "request"] },
  ], 1);
  assert.deepEqual([...activity.revealedIds].sort(), ["client", "request", "server"]);
  assert.deepEqual([...activity.activeIds].sort(), ["request", "server"]);
});

test("uses narrationSegments as the canonical timeline", () => {
  const timeline = getSceneTimeline(typedScene);
  assert.equal(timeline[0].source, "typed");
  assert.equal(timeline[0].subtitleText, "Client sends request");
  assert.deepEqual(timeline[0].claimIds, ["claim_1"]);
  assert.deepEqual(timeline[0].sourceIds, ["source_one"]);
});

test("adapts legacy actions without changing old saved lessons", () => {
  const timeline = getSceneTimeline({
    narration: "The client contacts the server to retrieve the requested data.",
    actions: [{ type: "connect", fromElement: "client", toElement: "server", label: "Client sends the request to the server" }],
  });
  assert.equal(timeline[0].source, "legacy");
  assert.equal(timeline[0].action, "trace");
  assert.deepEqual(timeline[0].targetElementIds, ["client", "server"]);
});


test("places comparison subjects in two columns", () => {
  const positions = buildTwoColumnPositions([{ id: "supply" }, { id: "demand" }]);
  assert.ok(positions.supply.x < positions.demand.x);
  assert.equal(positions.supply.y, positions.demand.y);
});

test("places a concept root at the centre of a radial map", () => {
  const positions = buildRadialPositions([{ id: "cell" }, { id: "nucleus" }, { id: "membrane" }]);
  assert.deepEqual(positions.cell, { x: 50, y: 50 });
  assert.notDeepEqual(positions.nucleus, positions.membrane);
});

test("places cycle stages around a loop", () => {
  const positions = buildCyclePositions([{ id: "heart" }, { id: "body" }, { id: "lungs" }]);
  assert.equal(Object.keys(positions).length, 3);
  assert.notEqual(positions.heart.x, positions.body.x);
});
