function EmptyState() {
    return (
        <section className="rounded-3xl border border-dashed border-blue-200 bg-white p-8 text-center shadow-sm">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-3xl bg-blue-50 text-2xl">
                ✨
            </div>

            <h3 className="text-2xl font-bold tracking-tight text-gray-950">
                Ask a concept. Get a clear explanation.
            </h3>

            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-gray-500">
                ConceptCanvas turns concept-based questions into structured text,
                storyboard scenes, visual cards, narration, subtitles, and follow-ups.
            </p>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl bg-blue-50/70 p-4 text-left">
                    <p className="font-semibold text-blue-950">Text explanation</p>
                    <p className="mt-1 text-sm leading-6 text-blue-900/80">
                        Get a simple meaning, steps, analogy, example, and takeaways.
                    </p>
                </div>

                <div className="rounded-2xl bg-green-50/70 p-4 text-left">
                    <p className="font-semibold text-green-950">Visual mode</p>
                    <p className="mt-1 text-sm leading-6 text-green-900/80">
                        Convert ideas into storyboard scenes and whiteboard-style visuals.
                    </p>
                </div>

                <div className="rounded-2xl bg-indigo-50/70 p-4 text-left">
                    <p className="font-semibold text-indigo-950">Learning player</p>
                    <p className="mt-1 text-sm leading-6 text-indigo-900/80">
                        Use narration, subtitles, progress, replay, and follow-up questions.
                    </p>
                </div>
            </div>
        </section>
    );
}

export default EmptyState;