import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function HighlightScene({ scene }) {
    const elements = getSceneElements(scene);
    const mainElement = elements[0] || "main_concept";
    const supportingElements = elements.slice(1);

    return (
        <div className="rounded-2xl border border-amber-100 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">
                        Highlight scene
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">{scene.title}</h4>
                </div>

                <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
                    Animated
                </span>
            </div>

            <div className="rounded-2xl border border-dashed border-amber-200 bg-amber-50/40 p-5">
                <div className="flex min-h-48 flex-col items-center justify-center gap-4">
                    <div className="relative">
                        <div className="animate-highlight-pulse absolute -inset-3 rounded-3xl border-4 border-amber-300" />

                        <div className="relative rounded-3xl border-2 border-amber-400 bg-white px-6 py-4 text-center text-sm font-bold text-amber-950 shadow-sm">
                            {formatElementName(mainElement)}
                        </div>
                    </div>

                    {supportingElements.length > 0 && (
                        <div className="mt-3 flex flex-wrap justify-center gap-2">
                            {supportingElements.map((element, index) => (
                                <span
                                    key={`${element}-${index}`}
                                    className="animate-highlight-chip rounded-full border border-amber-200 bg-white px-3 py-1 text-xs font-medium text-amber-900 shadow-sm"
                                    style={{ animationDelay: `${index * 180}ms` }}
                                >
                                    {formatElementName(element)}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <p className="mt-4 text-sm leading-6 text-gray-600">{scene.narration}</p>

            <div className="mt-4 rounded-xl bg-gray-50 p-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
                    Subtitles
                </p>

                <p className="text-sm text-gray-700">{getSubtitleText(scene)}</p>
            </div>
        </div>
    );
}

export default HighlightScene;