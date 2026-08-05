import GroundingReportPanel, { CitationMarks } from "./GroundingReportPanel";

function getSourceLabel(source, modelUsed) {
  if (source === "groq") return modelUsed ? `Groq · ${modelUsed}` : "Groq";
  if (source === "gemini") return modelUsed ? `Gemini · ${modelUsed}` : "Gemini";
  return "Deterministic fallback";
}

function SectionTitle({ children }) {
  return <h4 className="cc-article-heading">{children}</h4>;
}

function ExplanationPanel({ explanation, source, modelUsed, groundingReport, embedded = false }) {
  if (!explanation) return null;

  const stepByStep = Array.isArray(explanation.stepByStep) ? explanation.stepByStep : [];
  const technicalDetails = Array.isArray(explanation.technicalDetails) ? explanation.technicalDetails : [];
  const commonConfusions = Array.isArray(explanation.commonConfusions) ? explanation.commonConfusions : [];
  const takeaways = Array.isArray(explanation.takeaways) ? explanation.takeaways : [];

  return (
    <article className={embedded ? "cc-article cc-article-embedded" : "cc-article"}>
      <header className="cc-article-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="cc-eyebrow">Written lesson</p>
          <span className="cc-source-label">{getSourceLabel(source, modelUsed)}</span>
        </div>
        <h2>{explanation.title || "Concept explanation"}</h2>
        <p className="cc-article-lead">
          {explanation.quickMeaning || "Here is a simple explanation."}
          <CitationMarks groundingReport={groundingReport} section="quickMeaning" />
        </p>
      </header>

      <div className="cc-article-body">
        {explanation.deepExplanation && (
          <section>
            <SectionTitle>Explanation</SectionTitle>
            <p className="whitespace-pre-line">
              {explanation.deepExplanation}
              <CitationMarks groundingReport={groundingReport} section="deepExplanation" />
            </p>
          </section>
        )}

        {stepByStep.length > 0 && (
          <section>
            <SectionTitle>Step by step</SectionTitle>
            <ol className="cc-article-steps">
              {stepByStep.map((step, index) => (
                <li key={`${step}-${index}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <p>
                    {step}
                    <CitationMarks groundingReport={groundingReport} section="stepByStep" itemIndex={index} />
                  </p>
                </li>
              ))}
            </ol>
          </section>
        )}

        <div className="cc-article-pair">
          <section>
            <SectionTitle>Analogy</SectionTitle>
            <p>
              {explanation.analogy || "No analogy available."}
              <CitationMarks groundingReport={groundingReport} section="analogy" />
            </p>
          </section>
          <section>
            <SectionTitle>Example</SectionTitle>
            <p>
              {explanation.realWorldExample || "No example available."}
              <CitationMarks groundingReport={groundingReport} section="realWorldExample" />
            </p>
          </section>
        </div>

        {technicalDetails.length > 0 && (
          <section>
            <SectionTitle>Technical details</SectionTitle>
            <ul className="cc-article-list">
              {technicalDetails.map((item, index) => (
                <li key={`${item}-${index}`}>
                  {item}
                  <CitationMarks groundingReport={groundingReport} section="technicalDetails" itemIndex={index} />
                </li>
              ))}
            </ul>
          </section>
        )}

        {commonConfusions.length > 0 && (
          <section className="cc-article-note">
            <SectionTitle>Common confusions</SectionTitle>
            <ul>
              {commonConfusions.map((item, index) => (
                <li key={`${item}-${index}`}>
                  {item}
                  <CitationMarks groundingReport={groundingReport} section="commonConfusions" itemIndex={index} />
                </li>
              ))}
            </ul>
          </section>
        )}

        {explanation.interviewAngle && (
          <section>
            <SectionTitle>Interview angle</SectionTitle>
            <p>
              {explanation.interviewAngle}
              <CitationMarks groundingReport={groundingReport} section="interviewAngle" />
            </p>
          </section>
        )}

        {explanation.summary && (
          <section className="cc-article-summary">
            <SectionTitle>In one paragraph</SectionTitle>
            <p>
              {explanation.summary}
              <CitationMarks groundingReport={groundingReport} section="summary" />
            </p>
          </section>
        )}

        {takeaways.length > 0 && (
          <section>
            <SectionTitle>Key takeaways</SectionTitle>
            <ul className="cc-takeaways">
              {takeaways.map((takeaway, index) => (
                <li key={`${takeaway}-${index}`}>
                  <span aria-hidden="true" />
                  <p>
                    {takeaway}
                    <CitationMarks groundingReport={groundingReport} section="takeaways" itemIndex={index} />
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}

        <GroundingReportPanel groundingReport={groundingReport} />
      </div>
    </article>
  );
}

export default ExplanationPanel;
