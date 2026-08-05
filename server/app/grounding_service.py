from __future__ import annotations

import os
import re
from dataclasses import dataclass

from app.grounding_provider import GroundingProvider, build_grounding_provider
from app.models import GroundingReport


@dataclass(frozen=True)
class ExtractedClaim:
    claim_id: str
    section: str
    item_index: int | None
    text: str
    kind: str


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
YEAR_PATTERN = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2}|21\d{2})\b")
NUMBER_PATTERN = re.compile(r"(?:\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\b|[=<>±×÷])")


def _split_sentences(value: str) -> list[str]:
    cleaned = " ".join(value.split())
    if not cleaned:
        return []
    pieces = [part.strip() for part in SENTENCE_SPLIT.split(cleaned) if part.strip()]
    return pieces or [cleaned]


def _claim_kind(text: str, section: str) -> str:
    lowered = text.lower()
    if section == "analogy":
        return "analogy"
    if section == "realWorldExample":
        return "example"
    if section == "interviewAngle":
        return "instructional"
    if NUMBER_PATTERN.search(text):
        return "quantitative"
    if YEAR_PATTERN.search(text) or any(word in lowered for word in ("century", "war", "revolution", "founded")):
        return "historical"
    if any(word in lowered for word in ("causes", "caused", "leads to", "results in", "because")):
        return "causal"
    if any(word in lowered for word in ("whereas", "compared with", "versus", "unlike", "difference")):
        return "comparative"
    if any(word in lowered for word in ("first", "then", "next", "returns", "sends", "converts", "checks", "calls")):
        return "mechanism"
    if any(word in lowered for word in (" is a ", " means ", " refers to ", " are ")):
        return "definition"
    return "other"


def extract_claims(explanation: dict, max_claims: int | None = None) -> list[ExtractedClaim]:
    limit = max_claims or int(os.getenv("GROUNDING_MAX_CLAIMS", "18"))
    scalar_sections = (
        "quickMeaning",
        "deepExplanation",
        "realWorldExample",
        "analogy",
        "summary",
    )
    list_sections = (
        "stepByStep",
        "technicalDetails",
        "commonConfusions",
        "takeaways",
    )

    raw_claims: list[tuple[str, int | None, str]] = []
    for section in scalar_sections:
        value = explanation.get(section)
        if isinstance(value, str):
            for sentence in _split_sentences(value):
                raw_claims.append((section, None, sentence))
    for section in list_sections:
        value = explanation.get(section)
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, str):
                continue
            for sentence in _split_sentences(item):
                raw_claims.append((section, index, sentence))

    claims: list[ExtractedClaim] = []
    seen: set[str] = set()
    for section, item_index, text in raw_claims:
        normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
        if len(text) < 8 or normalized in seen:
            continue
        seen.add(normalized)
        claims.append(
            ExtractedClaim(
                claim_id=f"claim_{len(claims) + 1}",
                section=section,
                item_index=item_index,
                text=text[:700],
                kind=_claim_kind(text, section),
            )
        )
        if len(claims) >= limit:
            break
    return claims


def _empty_metrics(total: int, not_applicable: int = 0) -> dict:
    verifiable = max(0, total - not_applicable)
    return {
        "totalClaims": total,
        "verifiableClaims": verifiable,
        "supportedClaims": 0,
        "contradictedClaims": 0,
        "unverifiedClaims": verifiable,
        "notApplicableClaims": not_applicable,
        "coverageScore": 0,
    }


def ground_explanation(
    *,
    question: str,
    explanation: dict,
    mode: str,
    provider: GroundingProvider | None = None,
) -> dict | None:
    if mode == "off":
        return None

    claims = extract_claims(explanation)
    non_verifiable_kinds = {"analogy", "instructional"}
    provider_configuration_failed = False
    if provider is None:
        try:
            provider = build_grounding_provider()
        except Exception:
            provider = None
            provider_configuration_failed = True
    provider_name = getattr(provider, "name", "unavailable") if provider else "unavailable"

    if provider is None:
        claim_payloads = []
        not_applicable = 0
        for claim in claims:
            not_applicable_claim = claim.kind in non_verifiable_kinds
            not_applicable += int(not_applicable_claim)
            claim_payloads.append({
                "claimId": claim.claim_id,
                "section": claim.section,
                "itemIndex": claim.item_index,
                "text": claim.text,
                "kind": claim.kind,
                "status": "not_applicable" if not_applicable_claim else "unverified",
                "confidence": 0.0,
                "sourceIds": [],
                "evidenceIds": [],
            })
        report = {
            "schemaVersion": "1.0",
            "mode": mode,
            "status": "unavailable",
            "provider": provider_name,
            "metrics": _empty_metrics(len(claims), not_applicable),
            "claims": claim_payloads,
            "sources": [],
            "evidence": [],
            "warnings": [
                "The grounding provider configuration could not be loaded."
                if provider_configuration_failed
                else "Grounding was requested, but no trusted evidence provider is configured."
            ],
        }
        return GroundingReport.model_validate(report).model_dump(mode="json")

    source_map: dict[str, dict] = {}
    evidence_payloads: list[dict] = []
    claim_payloads: list[dict] = []
    supported = contradicted = unverified = not_applicable = 0
    provider_errors = 0

    verifiable_claims = [
        claim for claim in claims if claim.kind not in non_verifiable_kinds
    ]
    batch_results: dict[str, list] | None = None
    batch_method = getattr(provider, "find_evidence_batch", None)
    if callable(batch_method) and verifiable_claims:
        try:
            batch_results = batch_method(
                claims=[
                    {"claimId": claim.claim_id, "text": claim.text}
                    for claim in verifiable_claims
                ],
                question=question,
                max_results=3,
            )
            if not isinstance(batch_results, dict):
                batch_results = None
        except Exception:
            batch_results = None
            provider_errors += 1

    for claim in claims:
        if claim.kind in non_verifiable_kinds:
            not_applicable += 1
            claim_payloads.append({
                "claimId": claim.claim_id,
                "section": claim.section,
                "itemIndex": claim.item_index,
                "text": claim.text,
                "kind": claim.kind,
                "status": "not_applicable",
                "confidence": 1.0,
                "sourceIds": [],
                "evidenceIds": [],
            })
            continue

        if batch_results is not None and claim.claim_id in batch_results:
            candidates = batch_results.get(claim.claim_id, [])
        else:
            try:
                candidates = provider.find_evidence(
                    claim=claim.text,
                    question=question,
                    max_results=3,
                )
            except Exception:
                candidates = []
                provider_errors += 1

        supportive = [item for item in candidates if item.stance == "supports" and item.confidence >= 0.64]
        contradictory = [item for item in candidates if item.stance == "contradicts" and item.confidence >= 0.7]
        if contradictory and (not supportive or contradictory[0].confidence >= supportive[0].confidence):
            selected = contradictory[:2]
            status = "contradicted"
            contradicted += 1
        elif supportive:
            selected = supportive[:3]
            status = "supported"
            supported += 1
        else:
            selected = []
            status = "unverified"
            unverified += 1

        source_ids: list[str] = []
        evidence_ids: list[str] = []
        for candidate in selected:
            source_map.setdefault(candidate.source_id, {
                "sourceId": candidate.source_id,
                "title": candidate.title,
                "publisher": candidate.publisher,
                "url": candidate.url,
                "authority": candidate.authority,
                "publishedAt": candidate.published_at,
                "locator": candidate.locator,
            })
            evidence_id = f"evidence_{len(evidence_payloads) + 1}"
            evidence_payloads.append({
                "evidenceId": evidence_id,
                "claimId": claim.claim_id,
                "sourceId": candidate.source_id,
                "stance": candidate.stance,
                "excerpt": candidate.excerpt,
                "locator": candidate.locator,
                "confidence": candidate.confidence,
            })
            if candidate.source_id not in source_ids:
                source_ids.append(candidate.source_id)
            evidence_ids.append(evidence_id)

        confidence = max((item.confidence for item in selected), default=0.0)
        claim_payloads.append({
            "claimId": claim.claim_id,
            "section": claim.section,
            "itemIndex": claim.item_index,
            "text": claim.text,
            "kind": claim.kind,
            "status": status,
            "confidence": confidence,
            "sourceIds": source_ids,
            "evidenceIds": evidence_ids,
        })

    verifiable = supported + contradicted + unverified
    coverage = round((supported / verifiable) * 100) if verifiable else 100
    if contradicted:
        status = "fail"
    elif mode == "required" and coverage < 80:
        status = "fail"
    elif unverified or coverage < 90:
        status = "warn"
    else:
        status = "pass"

    warnings: list[str] = []
    if unverified:
        warnings.append(f"{unverified} factual claim(s) could not be verified by the configured provider.")
    if contradicted:
        warnings.append(f"{contradicted} claim(s) have contradictory evidence and require correction or review.")
    if provider_errors:
        warnings.append(f"The evidence provider failed for {provider_errors} claim(s).")
    if mode == "required" and coverage < 80:
        warnings.append("Required grounding coverage was not met.")

    report = {
        "schemaVersion": "1.0",
        "mode": mode,
        "status": status,
        "provider": provider_name,
        "metrics": {
            "totalClaims": len(claims),
            "verifiableClaims": verifiable,
            "supportedClaims": supported,
            "contradictedClaims": contradicted,
            "unverifiedClaims": unverified,
            "notApplicableClaims": not_applicable,
            "coverageScore": coverage,
        },
        "claims": claim_payloads,
        "sources": list(source_map.values()),
        "evidence": evidence_payloads,
        "warnings": warnings,
    }
    return GroundingReport.model_validate(report).model_dump(mode="json")


def _match_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in {
            "the", "and", "for", "with", "that", "this", "from", "into", "then",
            "when", "while", "your", "you", "are", "was", "were", "has", "have",
        }
    }


def attach_grounding_to_storyboard(
    storyboard: dict | None,
    grounding_report: dict | None,
) -> dict | None:
    if not isinstance(storyboard, dict) or not isinstance(grounding_report, dict):
        return storyboard

    claims = grounding_report.get("claims", [])
    claim_records = [
        {
            **claim,
            "tokens": _match_tokens(str(claim.get("text", ""))),
        }
        for claim in claims
        if isinstance(claim, dict)
    ]

    for scene in storyboard.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        scene_context = f"{scene.get('title', '')} {scene.get('narration', '')}"
        for segment in scene.get("narrationSegments", []):
            if not isinstance(segment, dict):
                continue
            segment_text = f"{segment.get('spokenText', '')} {segment.get('subtitleText', '')} {scene_context}"
            segment_tokens = _match_tokens(segment_text)
            matches: list[tuple[float, dict]] = []
            for claim in claim_records:
                claim_tokens = claim["tokens"]
                if not claim_tokens:
                    continue
                score = len(segment_tokens & claim_tokens) / len(claim_tokens)
                if score >= 0.22:
                    matches.append((score, claim))
            matches.sort(key=lambda item: item[0], reverse=True)
            selected = [item[1] for item in matches[:2]]
            segment["claimIds"] = [claim["claimId"] for claim in selected]
            segment["sourceIds"] = list(dict.fromkeys(
                source_id
                for claim in selected
                for source_id in claim.get("sourceIds", [])
            ))[:6]
    return storyboard
