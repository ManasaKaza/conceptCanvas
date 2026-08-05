import { BookOpen, Plus, Trash2, X } from "lucide-react";

function BrandMark() {
  return (
    <div className="cc-brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  );
}

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
      "Untitled lesson"
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
          className="fixed inset-0 z-30 bg-black/35 backdrop-blur-[1px] md:hidden"
        />
      )}

      <aside
        className={`cc-sidebar fixed left-0 top-0 z-40 flex h-screen w-[17rem] flex-col transition-transform duration-300 md:sticky md:z-auto md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 pb-4 pt-5">
          <div className="flex items-center gap-3">
            <BrandMark />
            <div>
              <h1 className="text-[0.98rem] font-semibold tracking-[-0.02em] text-gray-950">
                ConceptCanvas
              </h1>
              <p className="mt-0.5 text-xs text-gray-500">Visual learning studio</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="cc-icon-button md:hidden"
            aria-label="Close menu"
          >
            <X size={17} />
          </button>
        </div>

        <div className="px-4">
          <button
            type="button"
            onClick={handleNewChatClick}
            disabled={disabled}
            className="cc-primary-button w-full justify-center"
          >
            <Plus size={16} />
            New lesson
          </button>
        </div>

        <div className="mt-7 flex min-h-0 flex-1 flex-col">
          <div className="flex items-center justify-between px-5">
            <p className="cc-eyebrow">Recent lessons</p>
            {history.length > 0 && (
              <button
                type="button"
                onClick={onClearAllHistory}
                disabled={disabled}
                className="text-xs font-medium text-gray-400 transition hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Clear
              </button>
            )}
          </div>

          <div className="mt-3 min-h-0 flex-1 overflow-y-auto px-3 pb-5">
            {history.length === 0 ? (
              <div className="px-2 py-8 text-center">
                <BookOpen className="mx-auto text-gray-300" size={22} />
                <p className="mt-3 text-sm text-gray-400">Your lessons will appear here.</p>
              </div>
            ) : (
              <div className="space-y-1">
                {history.map((item) => {
                  const isActive = item.id === activeConversationId;
                  const title = getConversationTitle(item);
                  const questionCount = getQuestionCount(item);

                  return (
                    <div
                      key={item.id}
                      className={`group relative rounded-lg transition ${
                        isActive ? "bg-[var(--cc-accent-soft)]" : "hover:bg-[var(--cc-hover)]"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => handleSelectHistory(item)}
                        className="w-full px-3 py-2.5 pr-9 text-left"
                      >
                        <span className={`line-clamp-2 text-sm leading-5 ${isActive ? "font-semibold text-gray-950" : "font-medium text-gray-700"}`}>
                          {title}
                        </span>
                        <span className="mt-1 block text-xs text-gray-400">
                          {questionCount} {questionCount === 1 ? "question" : "questions"}
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => onDeleteHistoryItem(item.id)}
                        disabled={disabled}
                        className="cc-history-delete absolute right-2 top-2.5"
                        aria-label={`Delete ${title}`}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
