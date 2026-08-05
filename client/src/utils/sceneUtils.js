export function formatElementName(name) {
  if (!name || typeof name !== "string") return "visual element";
  return name.replaceAll("_", " ");
}

export function getSafeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function getSceneElements(scene) {
  return getSafeArray(scene?.visualElements);
}

export function getSubtitleText(scene) {
  const subtitleLines = getSafeArray(scene?.subtitleLines);
  return subtitleLines.length ? subtitleLines.join(" · ") : scene?.narration || "No subtitles available.";
}

function getLegacyActionLabel(scene, action) {
  if (action?.label?.trim()) return action.label.trim();
  if (action?.type === "show" && action.target) return `Showing ${formatElementName(action.target)}`;
  if (action?.type === "highlight" && action.target) return `Focus on ${formatElementName(action.target)}`;
  if (action?.type === "connect" && action.fromElement && action.toElement) {
    return `${formatElementName(action.fromElement)} connects to ${formatElementName(action.toElement)}`;
  }
  return scene?.narration || "Understanding this part of the lesson.";
}

export function getSceneTimeline(scene) {
  const narrationSegments = getSafeArray(scene?.narrationSegments);
  if (narrationSegments.length) {
    return narrationSegments.map((segment, index) => ({
      id: segment.id || `segment_${index + 1}`,
      order: segment.order || index + 1,
      spokenText: segment.spokenText || scene?.narration || "",
      subtitleText: segment.subtitleText || segment.spokenText || scene?.narration || "",
      targetElementIds: getSafeArray(segment.targetElementIds),
      action: segment.action || "highlight",
      estimatedDurationMs: segment.estimatedDurationMs || 3500,
      claimIds: getSafeArray(segment.claimIds),
      sourceIds: getSafeArray(segment.sourceIds),
      source: "typed",
    }));
  }

  const actions = getSafeArray(scene?.actions);
  if (actions.length) {
    return actions.map((action, index) => {
      const text = getLegacyActionLabel(scene, action);
      return {
        id: `legacy_segment_${index + 1}`,
        order: index + 1,
        spokenText: text.split(/\s+/).length >= 6 ? text : scene?.narration || text,
        subtitleText: text,
        targetElementIds: [action.target, action.fromElement, action.toElement].filter(Boolean),
        action:
          action.type === "connect" || action.type === "move"
            ? "trace"
            : action.type === "wait"
              ? "pause"
              : action.type === "show"
                ? "reveal"
                : "highlight",
        estimatedDurationMs: 3000,
        claimIds: [],
        sourceIds: [],
        source: "legacy",
      };
    });
  }

  return [{
    id: "legacy_segment_1",
    order: 1,
    spokenText: scene?.narration || "This scene introduces the current idea.",
    subtitleText: scene?.narration || "Current lesson scene",
    targetElementIds: getSceneElements(scene),
    action: "reveal",
    estimatedDurationMs: 3500,
    claimIds: [],
    sourceIds: [],
    source: "legacy",
  }];
}
