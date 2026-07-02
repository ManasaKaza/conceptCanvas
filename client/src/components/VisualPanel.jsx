import VisualLessonPlayer from "./VisualLessonPlayer";

function VisualPanel({ storyboard, storyboardSource, storyboardModelUsed }) {
    const scenes = storyboard?.scenes || [];

    return (
        <section className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-start justify-between gap-3">
                <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
                        Visual Explanation
                    </p>

                    <h3 className="text-xl font-bold text-gray-950">
                        Whiteboard Explanation
                    </h3>

                    <p className="mt-1 text-sm leading-6 text-gray-500">
                        Watch the concept as an animated lesson with scene-by-scene visual
                        transitions.
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                        {storyboardSource === "gemini" && (
                            <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-800">
                                AI storyboard
                                {storyboardModelUsed ? ` · ${storyboardModelUsed}` : ""}
                            </span>
                        )}

                        {storyboardSource === "groq" && (
                            <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-800">
                                AI storyboard
                                {storyboardModelUsed ? ` · ${storyboardModelUsed}` : ""}
                            </span>
                        )}
                    </div>
                </div>

                <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-900">
                    {scenes.length} scenes
                </span>
            </div>

            <VisualLessonPlayer scenes={scenes} />
        </section>
    );
}

export default VisualPanel;