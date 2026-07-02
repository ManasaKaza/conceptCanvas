function LoadingSteps({ steps, activeStep, onCancel }) {
    return (
        <div className="mb-8 rounded-3xl bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                    <p className="text-sm font-semibold text-gray-500">
                        Creating your explanation...
                    </p>

                    <p className="mt-1 text-sm text-gray-400">
                        This may take a few seconds when AI generation is enabled.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-900">
                        Step {Math.min(activeStep + 1, steps.length)} of {steps.length}
                    </span>

                    <button
                        onClick={onCancel}
                        className="rounded-full border border-red-100 bg-red-50 px-3 py-1 text-xs font-semibold text-red-600 hover:bg-red-100"
                    >
                        Cancel
                    </button>
                </div>
            </div>

            <div className="space-y-3">
                {steps.map((step, index) => {
                    const isCompleted = index < activeStep;
                    const isActive = index === activeStep;

                    return (
                        <div
                            key={step}
                            className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition-all ${isActive
                                    ? "border-blue-100 bg-blue-50"
                                    : isCompleted
                                        ? "border-green-100 bg-green-50"
                                        : "border-gray-100 bg-gray-50"
                                }`}
                        >
                            <div
                                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${isCompleted
                                        ? "bg-green-700 text-white"
                                        : isActive
                                            ? "bg-blue-900 text-white"
                                            : "bg-gray-200 text-gray-500"
                                    }`}
                            >
                                {isCompleted ? "✓" : isActive ? "…" : index + 1}
                            </div>

                            <span
                                className={`text-sm ${isActive
                                        ? "font-semibold text-blue-900"
                                        : isCompleted
                                            ? "text-green-700"
                                            : "text-gray-500"
                                    }`}
                            >
                                {step}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default LoadingSteps;