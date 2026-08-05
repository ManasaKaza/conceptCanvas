import { AlertTriangle, CheckCircle2, ExternalLink, ShieldQuestion } from "lucide-react";
import { getCitationSources, getSectionVerificationState } from "../utils/grounding";

export function CitationMarks({ groundingReport, section, itemIndex = null }) {
  if (!groundingReport || groundingReport.mode === "off") return null;
  const sources = getCitationSources(groundingReport, section, itemIndex);
  const state = getSectionVerificationState(groundingReport, section, itemIndex);
  if (sources.length === 0 && state === "not_applicable") return null;

  return (
    <span className="cc-citation-marks">
      {sources.map((source) => (
        <a key={source.sourceId} href={source.url} target="_blank" rel="noreferrer" title={`${source.title} · ${source.publisher}`}>
          {source.number}
        </a>
      ))}
      {state === "unverified" && <span className="is-unverified">Unverified</span>}
      {state === "contradicted" && <span className="is-conflicting">Conflicting evidence</span>}
    </span>
  );
}

function GroundingReportPanel({ groundingReport, compact = false }) {
  if (!groundingReport || groundingReport.mode === "off") return null;

  const metrics = groundingReport.metrics || {};
  const sources = Array.isArray(groundingReport.sources) ? groundingReport.sources : [];
  const evidence = Array.isArray(groundingReport.evidence) ? groundingReport.evidence : [];
  const status = groundingReport.status;
  const StatusIcon = status === "pass" ? CheckCircle2 : status === "fail" ? AlertTriangle : ShieldQuestion;

  return (
    <details className="cc-grounding-panel">
      <summary>
        <span className={`cc-grounding-status is-${status}`}><StatusIcon size={15} />Sources {status}</span>
        <span>{metrics.coverageScore ?? 0}% claim coverage</span>
      </summary>

      <div className="mt-4 space-y-4">
        <div className="cc-grounding-metrics">
          <div><span>Supported</span><strong>{metrics.supportedClaims ?? 0}</strong></div>
          <div><span>Unverified</span><strong>{metrics.unverifiedClaims ?? 0}</strong></div>
          <div><span>Conflicts</span><strong>{metrics.contradictedClaims ?? 0}</strong></div>
          <div><span>Sources</span><strong>{sources.length}</strong></div>
        </div>

        {groundingReport.warnings?.length > 0 && (
          <ul className="cc-warning-list">
            {groundingReport.warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        )}

        {!compact && sources.length > 0 && (
          <ol className="cc-source-list">
            {sources.map((source, index) => (
              <li key={source.sourceId}>
                <a href={source.url} target="_blank" rel="noreferrer">
                  <span>{index + 1}</span>
                  <span className="min-w-0 flex-1">
                    <strong>{source.title}</strong>
                    <small>{source.publisher} · {source.authority}{source.locator ? ` · ${source.locator}` : ""}</small>
                  </span>
                  <ExternalLink size={14} />
                </a>
              </li>
            ))}
          </ol>
        )}

        {!compact && evidence.some((item) => item.stance === "contradicts") && (
          <div className="cc-conflict-block">
            <strong>Contradictory evidence</strong>
            {evidence.filter((item) => item.stance === "contradicts").map((item) => <p key={item.evidenceId}>{item.excerpt}</p>)}
          </div>
        )}
      </div>
    </details>
  );
}

export default GroundingReportPanel;
