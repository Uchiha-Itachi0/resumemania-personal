"""Deterministic scoring. The model judges evidence; plain code computes the numbers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import EvidenceMatch, JobRequirements, MatchStatus, Priority

SCORING_VERSION = "v1"
PRIORITY_WEIGHT = {Priority.MUST: 2.0, Priority.NICE: 1.0}
STATUS_CREDIT = {MatchStatus.MATCHED: 1.0, MatchStatus.PARTIAL: 0.5, MatchStatus.MISSING: 0.0}


@dataclass(frozen=True)
class KeywordCoverage:
    ratio: float
    found: tuple[str, ...]
    missing: tuple[str, ...]


def alignment_score(job: JobRequirements, matches: list[EvidenceMatch]) -> int:
    """Weighted share of requirements evidenced. Must-haves count double.

    A requirement the matcher skipped counts as missing.
    """
    if not job.requirements:
        return 0
    by_id = {m.requirement_id: m for m in matches}
    total = 0.0
    earned = 0.0
    for requirement in job.requirements:
        weight = PRIORITY_WEIGHT[requirement.priority]
        match = by_id.get(requirement.id)
        status = match.status if match else MatchStatus.MISSING
        total += weight
        earned += weight * STATUS_CREDIT[status]
    return round(100 * earned / total)


def keyword_coverage(job: JobRequirements, resume_text: str) -> KeywordCoverage:
    """Unique JD keywords that appear in the resume. Repeats earn nothing extra."""
    keywords = _unique_keywords(job)
    if not keywords:
        return KeywordCoverage(ratio=0.0, found=(), missing=())
    found = tuple(k for k in keywords if contains_term(resume_text, k))
    missing = tuple(k for k in keywords if k not in found)
    return KeywordCoverage(ratio=len(found) / len(keywords), found=found, missing=missing)


def contains_term(text: str, term: str) -> bool:
    """Case-insensitive whole-term match that also works for terms like C++ or .NET."""
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term.strip()) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _unique_keywords(job: JobRequirements) -> list[str]:
    seen: dict[str, str] = {}
    for requirement in job.requirements:
        for keyword in requirement.keywords:
            key = keyword.strip().lower()
            if key and key not in seen:
                seen[key] = keyword.strip()
    return list(seen.values())


def score_band(score: int) -> str:
    if score >= 75:
        return "Strong fit"
    if score >= 50:
        return "Good start"
    return "Needs work"
