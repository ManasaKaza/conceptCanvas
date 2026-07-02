import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function FallbackScene({ scene }) {
    const elements = getSceneElements(scene);

    return (
        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                        {scene.sceneType || "unknown"}
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">
                        {scene.title || "Untitled scene"}
                    </h4>
                </div>

                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">
                    Preview
                </span>
            </div>

            <p className="text-sm leading-6 text-gray-600">
                {scene.narration || "No narration available."}
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
                {elements.length > 0 ? (
                    elements.map((element, index) => (
                        <span
                            key={`${element}-${index}`}
                            className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-900"
                        >
                            {formatElementName(element)}
                        </span>
                    ))
                ) : (
                    <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                        no visual elements
                    </span>
                )}
            </div>

            <div className="mt-4 rounded-xl bg-gray-50 p-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
                    Subtitles
                </p>

                <p className="text-sm text-gray-700">{getSubtitleText(scene)}</p>
            </div>
        </div>
    );
}

export default FallbackScene;