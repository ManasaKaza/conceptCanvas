function PromptCard({ prompt, onClick, disabled = false }) {
    return (
        <button
            onClick={() => onClick(prompt)}
            disabled={disabled}
            className={`rounded-2xl border px-4 py-3 text-left text-sm transition ${disabled
                    ? "cursor-not-allowed border-gray-100 bg-gray-100 text-gray-400"
                    : "border-gray-200 bg-gray-50 text-gray-700 hover:border-blue-300 hover:bg-blue-50"
                }`}
        >
            {prompt}
        </button>
    );
}

export default PromptCard;