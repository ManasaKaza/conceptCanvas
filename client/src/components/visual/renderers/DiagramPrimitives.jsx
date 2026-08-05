import {
  Box,
  Braces,
  CircleUserRound,
  Database,
  FileCode2,
  Globe2,
  HardDrive,
  Layers3,
  Network,
  PackageOpen,
  Server,
  Workflow,
} from "lucide-react";
import { getEdgeState, getNodeState, getRelationLabel } from "../visualModel";

const ICONS = {
  actor: CircleUserRound,
  client: Globe2,
  server: Server,
  service: Network,
  cache: HardDrive,
  database: Database,
  process: Workflow,
  decision: Workflow,
  data: PackageOpen,
  packet: PackageOpen,
  stack_frame: Layers3,
  tree_node: Network,
  bucket: Box,
  queue: Layers3,
  code: FileCode2,
  output: Braces,
  entity: Box,
  event: Workflow,
  state: Workflow,
  component: PackageOpen,
  category: Network,
  organism: CircleUserRound,
  place: Globe2,
  quantity: Braces,
  formula: Braces,
  example: PackageOpen,
  generic: Box,
};

export function DiagramNode({ node, position, revealedIds, activeIds }) {
  const state = getNodeState(node.id, revealedIds, activeIds);
  const Icon = ICONS[node.nodeKind] || Box;

  return (
    <div
      className={`cc-diagram-node is-${state}`}
      style={{ left: `${position.x}%`, top: `${position.y}%` }}
      data-element-id={node.id}
    >
      <Icon size={18} aria-hidden="true" />
      <p>{node.label}</p>
      {node.detail ? <small>{node.detail}</small> : null}
    </div>
  );
}

function getEdgeCoordinates(fromPosition, toPosition) {
  const dx = toPosition.x - fromPosition.x;
  const dy = toPosition.y - fromPosition.y;
  const length = Math.sqrt(dx * dx + dy * dy) || 1;
  const xPadding = (dx / length) * 8;
  const yPadding = (dy / length) * 8;
  return {
    x1: fromPosition.x + xPadding,
    y1: fromPosition.y + yPadding,
    x2: toPosition.x - xPadding,
    y2: toPosition.y - yPadding,
    labelX: (fromPosition.x + toPosition.x) / 2,
    labelY: (fromPosition.y + toPosition.y) / 2,
  };
}

export function DiagramEdges({ edges, positions, revealedIds, activeIds, markerId }) {
  const edgeLayouts = edges.map((edge) => {
    const fromPosition = positions[edge.fromId];
    const toPosition = positions[edge.toId];
    if (!fromPosition || !toPosition) return null;
    return { edge, coordinates: getEdgeCoordinates(fromPosition, toPosition), state: getEdgeState(edge, revealedIds, activeIds) };
  }).filter(Boolean);

  return (
    <>
      <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <marker id={markerId} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L0,7 L7,3.5 z" className="cc-arrow-fill" />
          </marker>
        </defs>
        {edgeLayouts.map(({ edge, coordinates, state }) => (
          <line
            key={edge.id}
            x1={coordinates.x1}
            y1={coordinates.y1}
            x2={coordinates.x2}
            y2={coordinates.y2}
            vectorEffect="non-scaling-stroke"
            strokeWidth={state === "active" ? 3 : 2}
            strokeDasharray={edge.relation === "response" || edge.relation === "returns" ? "7 5" : undefined}
            markerEnd={edge.directed === false ? undefined : `url(#${markerId})`}
            className={`cc-diagram-edge is-${state}`}
          />
        ))}
      </svg>

      {edgeLayouts.map(({ edge, coordinates, state }) => (
        <div
          key={`${edge.id}-label`}
          className={`cc-edge-label is-${state}`}
          style={{ left: `${coordinates.labelX}%`, top: `${coordinates.labelY}%` }}
        >
          {edge.label || getRelationLabel(edge.relation)}
        </div>
      ))}
    </>
  );
}
