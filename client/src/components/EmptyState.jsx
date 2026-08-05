function EmptyState() {
  return (
    <section className="cc-empty-state">
      <div className="cc-canvas-preview" aria-hidden="true">
        <div className="cc-preview-node cc-preview-node-a">Question</div>
        <span className="cc-preview-line cc-preview-line-a" />
        <div className="cc-preview-node cc-preview-node-b">Visual idea</div>
        <span className="cc-preview-line cc-preview-line-b" />
        <div className="cc-preview-node cc-preview-node-c">Clear lesson</div>
      </div>

      <div className="max-w-xl">
        <p className="cc-eyebrow">Ready when you are</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-[-0.035em] text-gray-950 sm:text-3xl">
          Ask a question and watch the idea take shape.
        </h2>
        <p className="mt-3 text-sm leading-7 text-gray-500 sm:text-base">
          ConceptCanvas chooses the teaching structure, builds the visual lesson,
          and keeps narration aligned with what is on screen.
        </p>
      </div>
    </section>
  );
}

export default EmptyState;
