import {
    formatElementName,
    getSceneElements,
    getSubtitleText,
} from "../../utils/sceneUtils";

function TimelineScene({ scene }) {
    const elements = getSceneElements(scene);
    const timelineItems = elements.length > 0 ? elements : ["start", "middle", "end"];

    return (
        <div className="rounded-2xl border border-sky-100 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-sky-600">
                        Timeline scene
                    </p>

                    <h4 className="mt-1 font-semibold text-gray-950">{scene.title}</h4>
                </div>

                <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-900">
                    Animated
                </span>
            </div>

            <div className="rounded-2xl border border-dashed border-sky-200 bg-sky-50/40 p-5">
                <div className="relative mx-auto max-w-xl">
                    <div className="animate-timeline-line absolute left-4 top-0 h-full w-1 rounded-full bg-sky-300 md:left-0 md:right-0 md:top-6 md:mx-auto md:h-1 md:w-full" />

                    <div className="relative flex flex-col gap-5 md:flex-row md:justify-between md:gap-3">
                        {timelineItems.map((item, index) => (
                            <div
                                key={`${item}-${index}`}
                                className="animate-timeline-item relative flex items-center gap-3 md:flex-col md:items-center"
                                style={{ animationDelay: `${index * 220}ms` }}
                            >
                                <div className="z-10 flex h-9 w-9 items-center justify-center rounded-full border-2 border-sky-300 bg-white text-sm font-bold text-sky-900 shadow-sm">
                                    {index + 1}
                                </div>

                                <div className="rounded-2xl border border-sky-100 bg-white px-4 py-3 text-sm font-semibold text-sky-950 shadow-sm md:min-w-28 md:text-center">
                                    {formatElementName(item)}
                                </div>
                            </div>
                        ))}
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

export default TimelineScene;