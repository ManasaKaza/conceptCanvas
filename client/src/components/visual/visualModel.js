const SUPPORTED_TYPED_DIAGRAMS = new Set([
  "sequence",
  "flow",
  "hierarchy",
  "stack",
  "tree",
  "comparison",
  "timeline",
  "architecture",
  "state_transition",
  "cycle",
  "cause_effect",
  "concept_map",
  "formula",
  "code_execution",
  "spatial",
]);

export function getVisualParts(visual) {
  const elements = Array.isArray(visual?.elements) ? visual.elements : [];

  return {
    nodes: elements.filter((element) => element?.type === "node"),
    edges: elements.filter((element) => element?.type === "edge"),
    groups: elements.filter((element) => element?.type === "group"),
    annotations: elements.filter((element) => element?.type === "annotation"),
  };
}

export function isTypedVisual(scene) {
  const visual = scene?.visual;
  return Boolean(
    visual?.schemaVersion === "2.0" &&
      Array.isArray(visual?.elements) &&
      visual.elements.length >= 2,
  );
}

export function isSupportedTypedVisual(scene) {
  return isTypedVisual(scene) && SUPPORTED_TYPED_DIAGRAMS.has(scene.visual.diagramType);
}

export function getElementActivity(timeline, activeIndex) {
  const revealedIds = new Set();
  const activeIds = new Set();

  timeline.slice(0, activeIndex + 1).forEach((segment, index) => {
    const targets = Array.isArray(segment?.targetElementIds)
      ? segment.targetElementIds
      : [];

    targets.forEach((targetId) => revealedIds.add(targetId));

    if (index === activeIndex) {
      targets.forEach((targetId) => activeIds.add(targetId));
    }
  });

  return { revealedIds, activeIds };
}

export function getNodeState(nodeId, revealedIds, activeIds) {
  if (activeIds.has(nodeId)) return "active";
  if (revealedIds.has(nodeId)) return "revealed";
  return "dimmed";
}

export function getEdgeState(edge, revealedIds, activeIds) {
  if (activeIds.has(edge.id)) return "active";
  if (
    revealedIds.has(edge.id) ||
    (revealedIds.has(edge.fromId) && revealedIds.has(edge.toId))
  ) {
    return "revealed";
  }
  return "dimmed";
}

export function buildLinearPositions(nodes, orientation = "left_to_right") {
  const count = Math.max(1, nodes.length);

  return Object.fromEntries(
    nodes.map((node, index) => {
      const progress = count === 1 ? 0.5 : index / (count - 1);
      const position =
        orientation === "top_to_bottom"
          ? { x: 50, y: 17 + progress * 66 }
          : { x: 14 + progress * 72, y: 46 };

      return [node.id, position];
    }),
  );
}


export function buildTwoColumnPositions(nodes) {
  const left = nodes[0];
  const right = nodes[1];
  const positions = {};
  if (left) positions[left.id] = { x: 25, y: 48 };
  if (right) positions[right.id] = { x: 75, y: 48 };
  nodes.slice(2).forEach((node, index) => {
    positions[node.id] = { x: index % 2 === 0 ? 25 : 75, y: 72 + Math.floor(index / 2) * 12 };
  });
  return positions;
}

export function buildRadialPositions(nodes) {
  if (!nodes.length) return {};
  const positions = { [nodes[0].id]: { x: 50, y: 50 } };
  const children = nodes.slice(1);
  children.forEach((node, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / Math.max(1, children.length);
    positions[node.id] = {
      x: 50 + Math.cos(angle) * 32,
      y: 50 + Math.sin(angle) * 32,
    };
  });
  return positions;
}

export function buildCyclePositions(nodes) {
  const positions = {};
  nodes.forEach((node, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / Math.max(1, nodes.length);
    positions[node.id] = {
      x: 50 + Math.cos(angle) * 32,
      y: 50 + Math.sin(angle) * 32,
    };
  });
  return positions;
}

function getIncomingCounts(nodes, edges) {
  const incoming = Object.fromEntries(nodes.map((node) => [node.id, 0]));
  edges.forEach((edge) => {
    if (edge.toId in incoming) incoming[edge.toId] += 1;
  });
  return incoming;
}

export function buildHierarchyPositions(nodes, edges, orientation = "top_to_bottom") {
  if (nodes.length <= 3) {
    return buildLinearPositions(nodes, orientation);
  }

  const incoming = getIncomingCounts(nodes, edges);
  const childrenByNode = Object.fromEntries(nodes.map((node) => [node.id, []]));
  edges.forEach((edge) => {
    if (childrenByNode[edge.fromId] && incoming[edge.toId] !== undefined) {
      childrenByNode[edge.fromId].push(edge.toId);
    }
  });

  const roots = nodes.filter((node) => incoming[node.id] === 0);
  const levels = [];
  const seen = new Set();
  let frontier = roots.length ? roots.map((node) => node.id) : [nodes[0].id];

  while (frontier.length && seen.size < nodes.length) {
    const level = frontier.filter((nodeId) => !seen.has(nodeId));
    if (!level.length) break;
    levels.push(level);
    level.forEach((nodeId) => seen.add(nodeId));
    frontier = level.flatMap((nodeId) => childrenByNode[nodeId] || []);
  }

  const unplaced = nodes.filter((node) => !seen.has(node.id)).map((node) => node.id);
  if (unplaced.length) levels.push(unplaced);

  const positions = {};
  levels.forEach((level, levelIndex) => {
    level.forEach((nodeId, itemIndex) => {
      const levelProgress = levels.length === 1 ? 0.5 : levelIndex / (levels.length - 1);
      const itemProgress = level.length === 1 ? 0.5 : itemIndex / (level.length - 1);
      positions[nodeId] =
        orientation === "left_to_right"
          ? { x: 15 + levelProgress * 70, y: 23 + itemProgress * 54 }
          : { x: 18 + itemProgress * 64, y: 16 + levelProgress * 68 };
    });
  });

  return positions;
}

export function getRelationLabel(relation) {
  const labels = {
    flows_to: "flows to",
    request: "request",
    response: "response",
    calls: "calls",
    returns: "returns",
    reads: "reads",
    writes: "writes",
    contains: "contains",
    routes_to: "routes to",
    transforms: "transforms",
    compares: "compares",
    depends_on: "depends on",
    causes: "causes",
    precedes: "precedes",
    part_of: "part of",
    changes_into: "changes into",
    activates: "activates",
    inhibits: "inhibits",
    supports: "supports",
    contrasts: "contrasts",
    located_in: "located in",
    increases: "increases",
    decreases: "decreases",
  };
  return labels[relation] || "connects";
}
