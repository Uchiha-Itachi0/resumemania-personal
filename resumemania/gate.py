"""Validation gate: deterministic checks on model output before a student sees it.

- Rewrites may not add numbers the resume never had. New numbers become [N].
- Rewrites may not add JD keywords the resume never showed. They get a [CONFIRM] flag.
- Rewrites must point at a real bullet. Edits for text not in the resume are dropped.
- Evidence quotes that are not in the resume are removed, and the match downgraded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .schemas import EditSuggestion, EvidenceMatch, JobRequirements, MatchStatus
from .scoring import contains_term

NUMBER_RE = re.compile(r"\d[\d,.]*\+?%?")
FLAG_NEW_NUMBER = "New number replaced with [N]. Add the real figure."
FLAG_NEW_SKILL = "Mentions {term}, which your resume doesn't show yet. [CONFIRM] it's true."


@dataclass(frozen=True)
class GateResult:
    edits: list[EditSuggestion]
    matches: list[EvidenceMatch]
    notes: list[str] = field(default_factory=list)


def run_gate(
    resume_text: str,
    job: JobRequirements,
    edits: list[EditSuggestion],
    matches: list[EvidenceMatch],
) -> GateResult:
    notes: list[str] = []
    checked_edits: list[EditSuggestion] = []
    for edit in edits:
        if not _appears_in(resume_text, edit.original_text):
            notes.append(f"Dropped a rewrite for text that isn't in your resume: {edit.original_text[:60]!r}")
            continue
        checked_edits.append(_check_edit(resume_text, job, edit))
    checked_matches = [_check_match(resume_text, m, notes) for m in matches]
    return GateResult(edits=checked_edits, matches=checked_matches, notes=notes)


def _check_edit(resume_text: str, job: JobRequirements, edit: EditSuggestion) -> EditSuggestion:
    flags = list(edit.flags)
    known_numbers = set(_numbers(resume_text))

    def replace_number(m: re.Match[str]) -> str:
        return m.group(0) if _normalise_number(m.group(0)) in known_numbers else "[N]"

    proposed = NUMBER_RE.sub(replace_number, edit.proposed_text)
    if proposed != edit.proposed_text:
        flags.append(FLAG_NEW_NUMBER)

    for term in _jd_terms(job):
        if contains_term(proposed, term) and not contains_term(resume_text, term):
            flags.append(FLAG_NEW_SKILL.format(term=term))

    return edit.model_copy(update={"proposed_text": proposed, "flags": flags})


def _check_match(resume_text: str, match: EvidenceMatch, notes: list[str]) -> EvidenceMatch:
    real = [q for q in match.evidence if _appears_in(resume_text, q)]
    if len(real) == len(match.evidence):
        return match
    notes.append(f"Removed evidence for {match.requirement_id} that wasn't quoted from your resume.")
    status = match.status
    if not real and status != MatchStatus.MISSING:
        status = MatchStatus.MISSING
    return match.model_copy(update={"evidence": real, "status": status})


def _appears_in(haystack: str, needle: str) -> bool:
    return _squash(needle) in _squash(haystack) if needle.strip() else False


def _squash(text: str) -> str:
    text = re.sub(r"^[\s•\-*▪●◦]+", "", text.strip())
    return re.sub(r"\s+", " ", text).lower()


def _numbers(text: str) -> list[str]:
    return [_normalise_number(n) for n in NUMBER_RE.findall(text)]


def _normalise_number(raw: str) -> str:
    return raw.rstrip(".,").replace(",", "")


def _jd_terms(job: JobRequirements) -> list[str]:
    return sorted({k.strip() for r in job.requirements for k in r.keywords if k.strip()})
