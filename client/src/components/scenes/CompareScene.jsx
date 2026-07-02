import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function splitElements(elements) {
    const middleIndex = Math.ceil(elements.length / 2);

    return {
        left: elements.slice(0, middleIndex),
        right: elements.slice(middleIndex),
    };
}

function CompareScene({ scene }) {
    const elements = getSceneElements(scene);
    const { left, right } = splitElements(elements);

    return (
        <div className="rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
                        Compare scene
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">{scene.title}</h4>
                </div>

                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">
                    Animated
                </span>
            </div>

            <div className="rounded-2xl border border-dashed border-emerald-200 bg-emerald-50/40 p-5">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="animate-compare-left rounded-2xl border border-emerald-200 bg-white p-4 shadow-sm">
                        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-emerald-700">
                            Side A
                        </p>

                        <div className="space-y-2">
                            {(left.length > 0 ? left : ["before"]).map((element, index) => (
                                <div
                                    key={`${element}-${index}`}
                                    className="rounded-xl bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-950"
                                >
                                    {formatElementName(element)}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="animate-compare-right rounded-2xl border border-blue-200 bg-white p-4 shadow-sm">
                        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-blue-700">
                            Side B
                        </p>

                        <div className="space-y-2">
                            {(right.length > 0 ? right : ["after"]).map((element, index) => (
                                <div
                                    key={`${element}-${index}`}
                                    className="rounded-xl bg-blue-50 px-3 py-2 text-sm font-medium text-blue-950"
                                >
                                    {formatElementName(element)}
                                </div>
                            ))}
                        </div>
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

export default CompareScene;