export function formatElementName(name) {
    if (!name || typeof name !== "string") {
        return "visual element";
    }

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

    if (subtitleLines.length === 0) {
        return scene?.narration || "No subtitles available.";
    }

    return subtitleLines.join(" · ");
}