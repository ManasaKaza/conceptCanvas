from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class EvidenceCandidate:
    source_id: str
    title: str
    publisher: str
    url: str
    authority: str
    stance: str
    excerpt: str
    confidence: float
    locator: str | None = None
    published_at: str | None = None


class GroundingProvider(Protocol):
    name: str

    def find_evidence(
        self,
        *,
        claim: str,
        question: str,
        max_results: int = 3,
    ) -> list[EvidenceCandidate]: ...

    def find_evidence_batch(
        self,
        *,
        claims: list[dict],
        question: str,
        max_results: int = 3,
    ) -> dict[str, list[EvidenceCandidate]]: ...


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "for",
    "from", "has", "have", "how", "in", "into", "is", "it", "its", "of",
    "on", "or", "that", "the", "their", "then", "this", "to", "was", "were",
    "what", "when", "which", "while", "with", "you", "your",
}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in STOP_WORDS
    }


def _stable_source_id(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"source_web_{digest}"


def _normalize_candidate(raw: dict) -> EvidenceCandidate | None:
    try:
        url = str(raw["url"]).strip()
        if not url.startswith("https://"):
            return None
        stance = str(raw.get("stance", "supports")).lower()
        if stance not in {"supports", "contradicts"}:
            return None
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
        source_id = str(raw.get("sourceId") or _stable_source_id(url)).lower()
        source_id = re.sub(r"[^a-z0-9_]", "_", source_id)
        if not source_id.startswith("source_"):
            source_id = _stable_source_id(url)
        title = str(raw["title"]).strip()
        publisher = str(raw["publisher"]).strip()
        if len(title) < 3 or len(publisher) < 2:
            return None
        authority = str(raw.get("authority", "reference")).lower()
        if authority not in {"primary", "official", "academic", "reference", "curated"}:
            authority = "reference"
        return EvidenceCandidate(
            source_id=source_id,
            title=title,
            publisher=publisher,
            url=url,
            authority=authority,
            stance=stance,
            excerpt=str(raw["excerpt"]).strip(),
            confidence=confidence,
            locator=str(raw["locator"]).strip() if raw.get("locator") else None,
            published_at=str(raw["publishedAt"]).strip() if raw.get("publishedAt") else None,
        )
    except (KeyError, TypeError, ValueError):
        return None


class CatalogGroundingProvider:
    name = "catalog"

    def __init__(self, catalog_path: str | Path):
        self.catalog_path = Path(catalog_path)
        payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        self.documents = payload.get("documents", [])

    def find_evidence(
        self,
        *,
        claim: str,
        question: str,
        max_results: int = 3,
    ) -> list[EvidenceCandidate]:
        claim_tokens = _tokens(claim)
        context_tokens = claim_tokens | _tokens(question)
        if not claim_tokens:
            return []

        candidates: list[tuple[float, EvidenceCandidate]] = []
        for document in self.documents:
            for statement in document.get("statements", []):
                text = str(statement.get("text", ""))
                statement_tokens = _tokens(text)
                keyword_tokens = _tokens(" ".join(statement.get("keywords", [])))
                searchable = statement_tokens | keyword_tokens | _tokens(str(document.get("title", "")))
                if not searchable:
                    continue

                claim_coverage = len(claim_tokens & searchable) / max(1, len(claim_tokens))
                context_overlap = len(context_tokens & searchable) / max(1, len(searchable))
                score = min(1.0, (claim_coverage * 0.82) + (context_overlap * 0.18))
                minimum = float(statement.get("minimumScore", 0.42))
                if score < minimum:
                    continue

                raw = {
                    "sourceId": document.get("sourceId"),
                    "title": document.get("title"),
                    "publisher": document.get("publisher"),
                    "url": document.get("url"),
                    "authority": document.get("authority", "reference"),
                    "publishedAt": document.get("publishedAt"),
                    "stance": statement.get("stance", "supports"),
                    "excerpt": text,
                    "locator": statement.get("locator") or document.get("locator"),
                    "confidence": round(min(0.99, max(score, float(statement.get("confidence", 0.0)))), 3),
                }
                candidate = _normalize_candidate(raw)
                if candidate:
                    candidates.append((candidate.confidence, candidate))

        candidates.sort(key=lambda item: item[0], reverse=True)
        unique: list[EvidenceCandidate] = []
        seen: set[tuple[str, str]] = set()
        for _, candidate in candidates:
            key = (candidate.source_id, candidate.excerpt)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
            if len(unique) >= max_results:
                break
        return unique

    def find_evidence_batch(
        self,
        *,
        claims: list[dict],
        question: str,
        max_results: int = 3,
    ) -> dict[str, list[EvidenceCandidate]]:
        return {
            str(claim["claimId"]): self.find_evidence(
                claim=str(claim["text"]),
                question=question,
                max_results=max_results,
            )
            for claim in claims
        }


class HttpGroundingProvider:
    """Adapter for a trusted internal retrieval-and-verification service.

    The remote service must return evidence candidates, not merely search links.
    ConceptCanvas never fetches arbitrary result URLs itself, avoiding an SSRF path.
    """

    name = "http"

    def __init__(self, endpoint: str, api_key: str | None = None, timeout_seconds: float = 8.0):
        parsed = urlparse(endpoint)
        is_https = parsed.scheme == "https"
        is_local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if not is_https and not is_local_http:
            raise ValueError("GROUNDING_API_URL must use HTTPS or an explicit localhost address")
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def find_evidence(
        self,
        *,
        claim: str,
        question: str,
        max_results: int = 3,
    ) -> list[EvidenceCandidate]:
        result = self.find_evidence_batch(
            claims=[{"claimId": "claim_1", "text": claim}],
            question=question,
            max_results=max_results,
        )
        return result.get("claim_1", [])

    def find_evidence_batch(
        self,
        *,
        claims: list[dict],
        question: str,
        max_results: int = 3,
    ) -> dict[str, list[EvidenceCandidate]]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = httpx.post(
            self.endpoint,
            headers=headers,
            json={"claims": claims, "question": question, "maxResults": max_results},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        grouped: dict[str, list[EvidenceCandidate]] = {
            str(claim["claimId"]): [] for claim in claims
        }
        if not isinstance(payload, dict):
            return grouped

        results_by_claim = payload.get("resultsByClaim")
        if isinstance(results_by_claim, dict):
            for claim_id, results in results_by_claim.items():
                if claim_id not in grouped or not isinstance(results, list):
                    continue
                normalized = [_normalize_candidate(item) for item in results if isinstance(item, dict)]
                grouped[claim_id] = [item for item in normalized if item is not None][:max_results]
            return grouped

        results = payload.get("results", [])
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                claim_id = str(item.get("claimId", ""))
                if claim_id not in grouped:
                    continue
                normalized = _normalize_candidate(item)
                if normalized and len(grouped[claim_id]) < max_results:
                    grouped[claim_id].append(normalized)
        return grouped



class HybridGroundingProvider:
    name = "hybrid"

    def __init__(self, providers: list[GroundingProvider]):
        self.providers = providers

    def find_evidence(
        self,
        *,
        claim: str,
        question: str,
        max_results: int = 3,
    ) -> list[EvidenceCandidate]:
        results: list[EvidenceCandidate] = []
        seen: set[tuple[str, str]] = set()
        for provider in self.providers:
            try:
                provider_results = provider.find_evidence(
                    claim=claim,
                    question=question,
                    max_results=max_results,
                )
            except Exception:
                continue
            for candidate in provider_results:
                key = (candidate.source_id, candidate.excerpt)
                if key in seen:
                    continue
                seen.add(key)
                results.append(candidate)
        results.sort(key=lambda item: item.confidence, reverse=True)
        return results[:max_results]

    def find_evidence_batch(
        self,
        *,
        claims: list[dict],
        question: str,
        max_results: int = 3,
    ) -> dict[str, list[EvidenceCandidate]]:
        combined: dict[str, list[EvidenceCandidate]] = {
            str(claim["claimId"]): [] for claim in claims
        }
        for provider in self.providers:
            try:
                batch_method = getattr(provider, "find_evidence_batch", None)
                if callable(batch_method):
                    provider_results = batch_method(
                        claims=claims,
                        question=question,
                        max_results=max_results,
                    )
                else:
                    provider_results = {
                        str(claim["claimId"]): provider.find_evidence(
                            claim=str(claim["text"]),
                            question=question,
                            max_results=max_results,
                        )
                        for claim in claims
                    }
            except Exception:
                continue

            for claim_id, candidates in provider_results.items():
                existing = combined.setdefault(claim_id, [])
                seen = {(item.source_id, item.excerpt) for item in existing}
                for candidate in candidates:
                    key = (candidate.source_id, candidate.excerpt)
                    if key not in seen:
                        existing.append(candidate)
                        seen.add(key)
                existing.sort(key=lambda item: item.confidence, reverse=True)
                combined[claim_id] = existing[:max_results]
        return combined


def build_grounding_provider() -> GroundingProvider | None:
    provider_name = os.getenv("GROUNDING_PROVIDER", "catalog").strip().lower()
    catalog_path_value = os.getenv(
        "GROUNDING_CATALOG_PATH",
        str(Path(__file__).parents[1] / "grounding" / "source_catalog.json"),
    )
    catalog_path = Path(catalog_path_value)
    if not catalog_path.is_absolute():
        catalog_path = Path(__file__).parents[1] / catalog_path

    catalog = None
    if catalog_path.exists():
        catalog = CatalogGroundingProvider(catalog_path)

    if provider_name in {"disabled", "none", "off"}:
        return None
    if provider_name == "catalog":
        return catalog
    if provider_name == "http":
        endpoint = os.getenv("GROUNDING_API_URL", "").strip()
        if not endpoint:
            return None
        return HttpGroundingProvider(endpoint, os.getenv("GROUNDING_API_KEY"))
    if provider_name == "hybrid":
        providers: list[GroundingProvider] = []
        if catalog:
            providers.append(catalog)
        endpoint = os.getenv("GROUNDING_API_URL", "").strip()
        if endpoint:
            providers.append(HttpGroundingProvider(endpoint, os.getenv("GROUNDING_API_KEY")))
        return HybridGroundingProvider(providers) if providers else None
    raise ValueError(f"Unsupported grounding provider: {provider_name}")
