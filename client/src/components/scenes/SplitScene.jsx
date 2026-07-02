import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function SplitScene({ scene }) {
    const elements = getSceneElements(scene);
    const rootElement = elements[0] || "decision";
    const branches = elements.slice(1);

    return (
        <div className="rounded-2xl border border-rose-100 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-rose-600">
                        Split scene
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">{scene.title}</h4>
                </div>

                <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-900">
                    Animated
                </span>
            </div>

            <div className="rounded-2xl border border-dashed border-rose-200 bg-rose-50/40 p-5">
                <div className="flex flex-col items-center">
                    <div className="animate-split-root rounded-2xl border border-rose-300 bg-white px-5 py-3 text-center text-sm font-bold text-rose-950 shadow-sm">
                        {formatElementName(rootElement)}
                    </div>

                    <div className="animate-split-line h-8 w-px bg-rose-300" />

                    <div className="animate-split-branches flex w-full max-w-md items-start justify-center gap-4">
                        {(branches.length > 0 ? branches : ["path_a", "path_b"]).map(
                            (branch, index) => (
                                <div
                                    key={`${branch}-${index}`}
                                    className="flex flex-col items-center gap-2"
                                >
                                    <div className="h-6 w-px bg-rose-300" />

                                    <div
                                        className={`rounded-2xl border px-4 py-3 text-center text-sm font-semibold shadow-sm ${index === 0
                                                ? "border-green-200 bg-green-50 text-green-900"
                                                : "border-red-200 bg-red-50 text-red-900"
                                            }`}
                                    >
                                        {formatElementName(branch)}
                                    </div>
                                </div>
                            ),
                        )}
                    </div>
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

export default SplitScene;