function ConversationPreview({
    turns = [],
    activeTurnId,
    onSelectTurn,
    onClearConversation,
}) {
    if (!Array.isArray(turns) || turns.length === 0) {
        return null;
    }

    return (
        <section className="mb-8 rounded-3xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
                        Questions in this thread
                    </p>

                    <h3 className="mt-1 text-lg font-bold text-gray-950">
                        Current learning thread
                    </h3>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-900">
                        {turns.length} questions
                    </span>

                    <button
                        onClick={onClearConversation}
                        className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-600 hover:bg-gray-50"
                    >
                        Clear
                    </button>
                </div>
            </div>

            <div className="max-h-[420px] space-y-3 overflow-y-auto pr-2">
                {turns.map((turn, index) => {
                    const isActive = turn.id === activeTurnId;

                    return (
                        <button
                            key={turn.id || `${turn.question}-${index}`}
                            onClick={() => onSelectTurn(turn.id)}
                            className={`w-full rounded-2xl border p-4 text-left transition ${isActive
                                    ? "border-blue-300 bg-blue-50 shadow-sm"
                                    : "border-gray-100 bg-gray-50 hover:border-blue-200 hover:bg-blue-50/60"
                                }`}
                        >
                            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-500">
                                Question {index + 1}
                            </p>

                            <p className="text-sm font-semibold leading-6 text-gray-800">
                                {turn.question}
                            </p>

                            <p className="mt-1 text-xs text-gray-500">
                                {turn.mode === "visual" ? "Text + Visual" : "Text only"}
                            </p>
                        </button>
                    );
                })}
            </div>
        </section>
    );
}

export default ConversationPreview;