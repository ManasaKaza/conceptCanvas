function FollowUpChips({ followUps, onFollowUpClick, disabled = false }) {
    return (
        <section>
            <div className="rounded-3xl bg-white p-5 shadow-sm">
                <p className="mb-3 text-sm font-semibold text-gray-500">
                    You might also want to know:
                </p>

                <div className="flex flex-wrap gap-3">
                    {followUps.map((item) => (
                        <button
                            key={item}
                            onClick={() => onFollowUpClick(item)}
                            disabled={disabled}
                            className={`rounded-full border px-4 py-2 text-sm font-medium ${disabled
                                    ? "cursor-not-allowed border-gray-100 bg-gray-100 text-gray-400"
                                    : "border-blue-200 bg-blue-50 text-blue-900 hover:bg-blue-100"
                                }`}
                        >
                            {item}
                        </button>
                    ))}
                </div>
            </div>
        </section>
    );
}

export default FollowUpChips;