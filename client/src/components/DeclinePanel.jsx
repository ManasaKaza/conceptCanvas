function DeclinePanel({ message, suggestions, onSuggestionClick, disabled = false }) {
    return (
        <section className="rounded-3xl border border-orange-100 bg-orange-50 p-6 shadow-sm">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-orange-700">
                Better as a concept question
            </p>

            <h3 className="text-2xl font-bold text-gray-950">
                This is outside ConceptCanvas&apos;s MVP scope.
            </h3>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-700">
                {message}
            </p>

            <div className="mt-6">
                <p className="mb-3 text-sm font-semibold text-gray-600">
                    Try asking one of these instead:
                </p>

                <div className="flex flex-wrap gap-3">
                    {suggestions.map((suggestion) => (
                        <button
                            key={suggestion}
                            onClick={() => onSuggestionClick(suggestion)}
                            disabled={disabled}
                            className={`rounded-full border px-4 py-2 text-sm font-medium ${disabled
                                    ? "cursor-not-allowed border-gray-100 bg-gray-100 text-gray-400"
                                    : "border-orange-200 bg-white text-orange-800 hover:bg-orange-100"
                                }`}
                        >
                            {suggestion}
                        </button>
                    ))}
                </div>
            </div>
        </section>
    );
}

export default DeclinePanel;