function getSourceLabel(source, modelUsed) {
    if (source === "groq") {
        return modelUsed
            ? `AI generated · Groq · ${modelUsed}`
            : "AI generated · Groq";
    }

    if (source === "gemini") {
        return modelUsed
            ? `AI generated · Gemini · ${modelUsed}`
            : "AI generated · Gemini";
    }

    return "Demo fallback explanation";
}

function SectionTitle({ children }) {
    return (
        <h4 className="mb-3 text-sm font-bold uppercase tracking-wide text-gray-500">
            {children}
        </h4>
    );
}

function ExplanationPanel({ explanation, source, modelUsed }) {
    if (!explanation) {
        return null;
    }

    const stepByStep = Array.isArray(explanation.stepByStep)
        ? explanation.stepByStep
        : [];

    const technicalDetails = Array.isArray(explanation.technicalDetails)
        ? explanation.technicalDetails
        : [];

    const commonConfusions = Array.isArray(explanation.commonConfusions)
        ? explanation.commonConfusions
        : [];

    const takeaways = Array.isArray(explanation.takeaways)
        ? explanation.takeaways
        : [];

    return (
        <section className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-5 flex flex-col gap-3 border-b border-gray-100 pb-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
                        Text Explanation
                    </p>

                    <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${source === "fallback"
                            ? "bg-amber-50 text-amber-800"
                            : "bg-green-50 text-green-800"
                            }`}
                    >
                        {getSourceLabel(source, modelUsed)}
                    </span>
                </div>

                <div>
                    <h3 className="text-2xl font-bold tracking-tight text-gray-950">
                        {explanation.title || "Concept Explanation"}
                    </h3>

                    <p className="mt-3 rounded-2xl bg-blue-50/70 p-4 text-sm leading-7 text-blue-950">
                        {explanation.quickMeaning || "Here is a simple explanation."}
                    </p>
                </div>
            </div>

            <div className="space-y-6">
                {explanation.deepExplanation && (
                    <div className="rounded-2xl border border-blue-100 bg-white p-4">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-blue-700">
                            Deep Explanation
                        </p>

                        <p className="whitespace-pre-line text-sm leading-7 text-gray-700">
                            {explanation.deepExplanation}
                        </p>
                    </div>
                )}

                {stepByStep.length > 0 && (
                    <div>
                        <SectionTitle>Step-by-step</SectionTitle>

                        <div className="space-y-3">
                            {stepByStep.map((step, index) => (
                                <div
                                    key={`${step}-${index}`}
                                    className="flex gap-3 rounded-2xl border border-gray-100 bg-gray-50 p-4"
                                >
                                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-900 text-xs font-bold text-white">
                                        {index + 1}
                                    </div>

                                    <p className="text-sm leading-6 text-gray-700">{step}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-400">
                            Analogy
                        </p>

                        <p className="text-sm leading-6 text-gray-700">
                            {explanation.analogy || "No analogy available."}
                        </p>
                    </div>

                    <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-400">
                            Real-world example
                        </p>

                        <p className="text-sm leading-6 text-gray-700">
                            {explanation.realWorldExample || "No example available."}
                        </p>
                    </div>
                </div>

                {technicalDetails.length > 0 && (
                    <div>
                        <SectionTitle>Technical details</SectionTitle>

                        <div className="space-y-2">
                            {technicalDetails.map((item, index) => (
                                <div
                                    key={`${item}-${index}`}
                                    className="rounded-2xl bg-gray-50 px-4 py-3 text-sm leading-6 text-gray-700"
                                >
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {commonConfusions.length > 0 && (
                    <div>
                        <SectionTitle>Common confusions</SectionTitle>

                        <div className="space-y-2">
                            {commonConfusions.map((item, index) => (
                                <div
                                    key={`${item}-${index}`}
                                    className="rounded-2xl bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900"
                                >
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {explanation.interviewAngle && (
                    <div className="rounded-2xl bg-indigo-50 px-4 py-4">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-indigo-700">
                            Interview angle
                        </p>

                        <p className="text-sm leading-6 text-indigo-950">
                            {explanation.interviewAngle}
                        </p>
                    </div>
                )}

                {explanation.summary && (
                    <div className="rounded-2xl bg-blue-950 px-4 py-4 text-white">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-blue-200">
                            Summary
                        </p>

                        <p className="text-sm leading-6">{explanation.summary}</p>
                    </div>
                )}

                {takeaways.length > 0 && (
                    <div>
                        <SectionTitle>Key takeaways</SectionTitle>

                        <div className="space-y-2">
                            {takeaways.map((takeaway, index) => (
                                <div
                                    key={`${takeaway}-${index}`}
                                    className="rounded-2xl bg-green-50 px-4 py-3 text-sm font-medium leading-6 text-green-900"
                                >
                                    ✓ {takeaway}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}

export default ExplanationPanel;