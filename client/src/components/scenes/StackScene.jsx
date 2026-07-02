import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function StackScene({ scene }) {
    const elements = getSceneElements(scene);

    return (
        <div className="rounded-2xl border border-purple-100 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-purple-500">
                        Stack scene
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">{scene.title}</h4>
                </div>

                <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-900">
                    Animated
                </span>
            </div>

            <div className="rounded-2xl border border-dashed border-purple-200 bg-purple-50/40 p-5">
                <div className="mx-auto flex max-w-sm flex-col-reverse items-stretch gap-2">
                    {elements.map((element, index) => (
                        <div
                            key={`${element}-${index}`}
                            className="animate-stack-item rounded-xl border border-purple-200 bg-white px-4 py-3 text-center text-sm font-semibold text-purple-950 shadow-sm"
                            style={{ animationDelay: `${index * 250}ms` }}
                        >
                            {formatElementName(element)}
                        </div>
                    ))}
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

export default StackScene;