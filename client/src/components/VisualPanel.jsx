import { AlertTriangle, CheckCircle2, ChevronDown, Info, ShieldCheck } from "lucide-react";
import VisualLessonPlayer from "./VisualLessonPlayer";
import GroundingReportPanel from "./GroundingReportPanel";

function humanize(value) {
  return value ? value.replaceAll("_", " ") : "Not available";
}

function VisualPanel({
  storyboard,
  storyboardSource,
  storyboardModelUsed,
  storyboardValidation,
  qualityReport,
  groundingReport,
}) {
  const scenes = storyboard?.scenes || [];
  const planningProfile = storyboard?.planningProfile;
  const usedFallback = storyboardValidation?.fallbackUsed;
  const issues = storyboardValidation?.issues || [];
  const qualityStatus = qualityReport?.status || "warn";
  const qualityScore = qualityReport?.overallScore;
  const qualityMetrics = qualityReport?.metrics;
  const qualityIssues = qualityReport?.issues || [];
  const repair = qualityReport?.repair;
  const groundingStatus = groundingReport?.status;
  const lessonKey = scenes.map((scene) => `${scene?.id || ""}:${scene?.title || ""}:${scene?.narration || ""}`).join("|");
  const isVerified = qualityStatus === "pass" && groundingStatus !== "fail";
  const StatusIcon = isVerified ? CheckCircle2 : AlertTriangle;

  return (
    <section className="cc-visual-workspace">
      <div className="cc-lesson-heading">
        <div>
          <p className="cc-eyebrow">Visual lesson</p>
          <h2>Interactive explanation</h2>
        </div>
        <div className={`cc-release-status ${isVerified ? "is-pass" : "is-warn"}`}>
          <StatusIcon size={15} />
          {isVerified ? "Quality checks passed" : "Review recommended"}
        </div>
      </div>

      <div className="cc-visual-workspace-grid">
        <VisualLessonPlayer key={lessonKey} scenes={scenes} groundingReport={groundingReport} />

        <aside className="cc-lesson-inspector">
          <section>
            <p className="cc-eyebrow">Lesson approach</p>
            <h3>{humanize(planningProfile?.primaryArchetype)}</h3>
            <p className="mt-2 text-sm leading-6 text-gray-500">
              {planningProfile?.rationale || "The lesson uses the visual structure that best matches the concept."}
            </p>
          </section>

          <div className="cc-inspector-facts">
            <div><span>Subject</span><strong>{humanize(planningProfile?.subjectDomain)}</strong></div>
            <div><span>Scenes</span><strong>{scenes.length}</strong></div>
            <div><span>Quality</span><strong>{Number.isFinite(qualityScore) ? `${qualityScore}/100` : humanize(qualityStatus)}</strong></div>
          </div>

          {planningProfile?.limitations?.length > 0 && (
            <div className="cc-inspector-warning">
              <Info size={16} />
              <div>{planningProfile.limitations.map((limitation) => <p key={limitation}>{limitation}</p>)}</div>
            </div>
          )}

          <GroundingReportPanel groundingReport={groundingReport} compact />

          <details className="cc-diagnostics">
            <summary>
              <span><ShieldCheck size={16} />Lesson diagnostics</span>
              <ChevronDown size={16} />
            </summary>
            <div className="space-y-4 pt-4">
              <div className="cc-diagnostic-row"><span>Generation</span><strong>{humanize(storyboardSource)}{storyboardModelUsed ? ` · ${storyboardModelUsed}` : ""}</strong></div>
              <div className="cc-diagnostic-row"><span>Scene count</span><strong>{storyboardValidation?.exactSceneCount ? "Verified" : "Mismatch"}</strong></div>
              <div className="cc-diagnostic-row"><span>Fallback</span><strong>{usedFallback ? "Used" : "Not used"}</strong></div>
              {repair?.attempted && <div className="cc-diagnostic-row"><span>Repair</span><strong>{humanize(repair.strategy)}</strong></div>}

              {qualityMetrics && (
                <div className="cc-diagnostic-scores">
                  {[
                    ["Structure", qualityMetrics.structureScore],
                    ["Visual", qualityMetrics.visualSpecificityScore],
                    ["Narration", qualityMetrics.narrationAlignmentScore],
                    ["Risk", qualityMetrics.technicalRiskScore],
                  ].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
                </div>
              )}

              {(issues.length > 0 || qualityIssues.length > 0) && (
                <ul className="cc-diagnostic-issues">
                  {issues.slice(0, 6).map((issue) => <li key={issue}>{issue}</li>)}
                  {qualityIssues.slice(0, 6).map((issue, index) => <li key={`${issue.code}-${index}`}>{issue.message}</li>)}
                </ul>
              )}
            </div>
          </details>
        </aside>
      </div>
    </section>
  );
}

export default VisualPanel;
