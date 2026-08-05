import { formatElementName } from "../../utils/sceneUtils";

function collectSceneElements(scene) {
  const visualElements = Array.isArray(scene?.visualElements)
    ? scene.visualElements
    : [];
  const actionElements = Array.isArray(scene?.actions)
    ? scene.actions.flatMap((action) => [
        action.target,
        action.fromElement,
        action.toElement,
      ])
    : [];

  return [...new Set([...visualElements, ...actionElements].filter(Boolean))];
}

function getPosition(index, total) {
  const layouts = {
    1: [{ x: 50, y: 43 }],
    2: [
      { x: 28, y: 43 },
      { x: 72, y: 43 },
    ],
    3: [
      { x: 18, y: 43 },
      { x: 50, y: 28 },
      { x: 82, y: 43 },
    ],
    4: [
      { x: 16, y: 33 },
      { x: 38, y: 58 },
      { x: 64, y: 33 },
      { x: 86, y: 58 },
    ],
  };

  const fallback = [
    { x: 12, y: 42 },
    { x: 30, y: 26 },
    { x: 48, y: 58 },
    { x: 66, y: 26 },
    { x: 84, y: 58 },
  ];

  return (layouts[total] || fallback)[index] || fallback[index % fallback.length];
}

function LegacyVisualCanvas({ scene, activeMomentIndex, subtitle }) {
  const elements = collectSceneElements(scene);
  const actions = Array.isArray(scene?.actions) ? scene.actions : [];
  const completedActions = actions.slice(0, activeMomentIndex + 1);
  const activeAction = actions[activeMomentIndex];
  const visibleIds = new Set();

  completedActions.forEach((action) => {
    [action.target, action.fromElement, action.toElement]
      .filter(Boolean)
      .forEach((id) => visibleIds.add(id));
  });

  const activeIds = new Set(
    [activeAction?.target, activeAction?.fromElement, activeAction?.toElement].filter(
      Boolean,
    ),
  );
  const positions = Object.fromEntries(
    elements.map((element, index) => [element, getPosition(index, elements.length)]),
  );

  return (
    <div className="relative min-h-[400px] overflow-hidden rounded-[1.75rem] border border-gray-200 bg-gradient-to-br from-gray-50 via-white to-indigo-50">
      <div className="absolute left-5 top-5 z-30 rounded-full bg-white/90 px-3 py-1 text-xs font-bold uppercase tracking-wide text-gray-600 shadow-sm">
        Legacy lesson visual
      </div>

      <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
        <defs>
          <marker id="legacy-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L7,3 z" className="fill-indigo-600" />
          </marker>
        </defs>
        {completedActions.map((action, index) => {
          if (!["connect", "move"].includes(action.type)) return null;
          const from = positions[action.fromElement];
          const to = positions[action.toElement];
          if (!from || !to) return null;
          return (
            <line
              key={`${action.fromElement}-${action.toElement}-${index}`}
              x1={`${from.x}%`}
              y1={`${from.y}%`}
              x2={`${to.x}%`}
              y2={`${to.y}%`}
              strokeWidth={index === activeMomentIndex ? 4 : 2.5}
              className={index === activeMomentIndex ? "stroke-indigo-600" : "stroke-indigo-300"}
              strokeDasharray={action.type === "move" ? "8 6" : undefined}
              markerEnd="url(#legacy-arrow)"
            />
          );
        })}
      </svg>

      {elements.map((element) => {
        const position = positions[element];
        const visible = visibleIds.has(element);
        const active = activeIds.has(element);
        return (
          <div
            key={element}
            className={`absolute z-20 w-36 -translate-x-1/2 -translate-y-1/2 rounded-2xl border bg-white px-4 py-3 text-center text-sm font-bold shadow-sm transition-all duration-500 sm:w-44 ${
              visible ? "scale-100 opacity-100" : "scale-95 opacity-25"
            } ${
              active
                ? "border-indigo-500 text-indigo-950 ring-4 ring-indigo-100"
                : "border-gray-100 text-gray-600"
            }`}
            style={{ left: `${position.x}%`, top: `${position.y}%` }}
          >
            {formatElementName(element)}
          </div>
        );
      })}

      <div className="absolute bottom-4 left-1/2 z-30 w-[92%] -translate-x-1/2 rounded-2xl bg-slate-950/92 px-5 py-4 text-center text-white shadow-xl">
        <p className="text-xs font-bold uppercase tracking-wide text-indigo-300">Live subtitle</p>
        <p className="mt-1 text-sm font-semibold leading-6 sm:text-base">{subtitle}</p>
      </div>
    </div>
  );
}

export default LegacyVisualCanvas;
