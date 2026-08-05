function ConversationPreview({ turns = [], activeTurnId, onSelectTurn, onClearConversation }) {
  if (!Array.isArray(turns) || turns.length === 0) return null;

  return (
    <section className="cc-thread-rail" aria-label="Questions in this learning thread">
      <div className="flex items-center justify-between gap-3 px-1">
        <p className="cc-eyebrow">Learning thread · {turns.length}</p>
        <button type="button" onClick={onClearConversation} className="cc-text-button">
          Clear thread
        </button>
      </div>

      <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
        {turns.map((turn, index) => {
          const isActive = turn.id === activeTurnId;
          return (
            <button
              type="button"
              key={turn.id || `${turn.question}-${index}`}
              onClick={() => onSelectTurn(turn.id)}
              aria-current={isActive ? "step" : undefined}
              className={`cc-thread-item ${isActive ? "is-active" : ""}`}
            >
              <span className="cc-thread-number">{String(index + 1).padStart(2, "0")}</span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium text-gray-800">{turn.question}</span>
                <span className="mt-0.5 block text-xs text-gray-400">
                  {turn.mode === "visual" ? "Visual lesson" : "Text lesson"}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export default ConversationPreview;
