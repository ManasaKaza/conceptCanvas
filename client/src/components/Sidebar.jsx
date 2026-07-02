function Sidebar({
    history,
    activeConversationId,
    onNewChat,
    onSelectHistory,
    onDeleteHistoryItem,
    onClearAllHistory,
    isOpen,
    onClose,
    disabled = false,
}) {
    function handleNewChatClick() {
        if (disabled) return;

        onNewChat();
        onClose?.();
    }

    function handleSelectHistory(item) {
        if (disabled) return;

        onSelectHistory(item);
        onClose?.();
    }

    function getConversationTitle(item) {
        return (
            item.title ||
            item.first_question ||
            item.firstQuestion ||
            item.question ||
            "Untitled conversation"
        );
    }

    function getQuestionCount(item) {
        return item.question_count || item.questionCount || item.turns?.length || 0;
    }

    return (
        <>
            {isOpen && (
                <button
                    aria-label="Close sidebar overlay"
                    onClick={onClose}
                    className="fixed inset-0 z-30 bg-black/30 md:hidden"
                />
            )}

            <aside
                className={`fixed left-0 top-0 z-40 h-screen w-72 border-r border-gray-200 bg-white p-5 transition-transform duration-300 md:static md:z-auto md:block md:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"
                    }`}
            >
                <div className="mb-6 flex items-start justify-between gap-3">
                    <div>
                        <h1 className="text-xl font-bold text-blue-900">ConceptCanvas</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            AI visual learning tutor
                        </p>
                    </div>

                    <button
                        onClick={onClose}
                        className="rounded-lg border border-gray-200 px-2 py-1 text-sm text-gray-500 md:hidden"
                    >
                        ✕
                    </button>
                </div>

                <button
                    onClick={handleNewChatClick}
                    className={`mb-6 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white ${disabled
                            ? "cursor-not-allowed bg-gray-400"
                            : "bg-blue-900 hover:bg-blue-800"
                        }`}
                >
                    + New Chat
                </button>

                <div>
                    <div className="mb-3 flex items-center justify-between gap-2">
                        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                            History
                        </h2>

                        {history.length > 0 && (
                            <button
                                onClick={onClearAllHistory}
                                disabled={disabled}
                                className={`text-xs font-semibold ${disabled
                                        ? "cursor-not-allowed text-gray-400"
                                        : "text-red-500 hover:text-red-600"
                                    }`}
                            >
                                Clear all
                            </button>
                        )}
                    </div>

                    {history.length === 0 ? (
                        <p className="text-sm text-gray-400">No conversations yet.</p>
                    ) : (
                        <div className="max-h-[calc(100vh-190px)] space-y-2 overflow-y-auto pr-1">
                            {history.map((item) => {
                                const isActive = item.id === activeConversationId;
                                const title = getConversationTitle(item);
                                const questionCount = getQuestionCount(item);

                                return (
                                    <div
                                        key={item.id}
                                        className={`group rounded-xl border p-2 transition ${isActive
                                                ? "border-blue-300 bg-blue-50 shadow-sm"
                                                : "border-gray-100 bg-gray-50 hover:bg-gray-100"
                                            }`}
                                    >
                                        <button
                                            onClick={() => handleSelectHistory(item)}
                                            className="w-full text-left"
                                        >
                                            <span
                                                className={`line-clamp-2 text-sm font-semibold ${isActive ? "text-blue-950" : "text-gray-800"
                                                    }`}
                                            >
                                                {title}
                                            </span>

                                            <span
                                                className={`mt-1 block text-xs ${isActive ? "text-blue-700" : "text-gray-500"
                                                    }`}
                                            >
                                                {questionCount}{" "}
                                                {questionCount === 1 ? "question" : "questions"}
                                            </span>

                                            {item.lastQuestion && item.lastQuestion !== title && (
                                                <span className="mt-1 block line-clamp-1 text-xs text-gray-400">
                                                    Last: {item.lastQuestion}
                                                </span>
                                            )}
                                        </button>

                                        <button
                                            onClick={() => onDeleteHistoryItem(item.id)}
                                            disabled={disabled}
                                            className={`mt-2 hidden text-xs font-semibold group-hover:block ${disabled
                                                    ? "cursor-not-allowed text-gray-400"
                                                    : "text-red-500 hover:text-red-600"
                                                }`}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </aside>
        </>
    );
}

export default Sidebar;