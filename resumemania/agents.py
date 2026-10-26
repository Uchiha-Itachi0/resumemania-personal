"""The five AI agents. Each is one focused call with its own prompt and output schema."""

from __future__ import annotations

import json
from dataclasses import dataclass

from . import prompts
from .llm import StructuredLLM
from .schemas import (
    EvidenceMatch,
    FeedbackPlan,
    JobRequirements,
    MatchResult,
    ParsedResume,
    QualityReview,
)


@dataclass(frozen=True)
class Models:
    fast: str
    smart: str


def parse_resume(llm: StructuredLLM, models: Models, resume_text: str) -> ParsedResume:
    """Resume Parser Agent: structure the resume without rewording it."""
    return llm.generate(
        model=models.fast,
        system=prompts.RESUME_PARSER_SYSTEM,
        prompt=prompts.fence("resume", resume_text),
        schema=ParsedResume,
        step="Read your resume",
    )


def analyze_jd(
    llm: StructuredLLM, models: Models, jd_text: str, target_role: str = ""
) -> JobRequirements:
    """JD Analysis Agent: turn the job post into a checklist."""
    role_line = f"Target role chosen by the student: {target_role.strip()}\n" if target_role.strip() else ""
    job = llm.generate(
        model=models.fast,
        system=prompts.JD_ANALYZER_SYSTEM,
        prompt=role_line + prompts.fence("job", jd_text),
        schema=JobRequirements,
        step="Read the job",
    )
    return _with_unique_ids(job)


def match_evidence(
    llm: StructuredLLM,
    models: Models,
    resume_text: str,
    job: JobRequirements,
) -> list[EvidenceMatch]:
    """Keyword/Evidence Matching Agent: find proof for each requirement."""
    checklist = json.dumps(
        [{"id": r.id, "text": r.text, "priority": r.priority.value, "keywords": r.keywords}
         for r in job.requirements],
        indent=1,
    )
    result = llm.generate(
        model=models.smart,
        system=prompts.MATCHER_SYSTEM,
        prompt=f"Requirements:\n{checklist}\n\n{prompts.fence('resume', resume_text)}",
        schema=MatchResult,
        step="Match your evidence",
    )
    known = {r.id for r in job.requirements}
    return [m for m in result.matches if m.requirement_id in known]


def review_quality(llm: StructuredLLM, models: Models, resume_text: str) -> QualityReview:
    """Resume Quality Agent: clarity, impact and consistency."""
    return llm.generate(
        model=models.smart,
        system=prompts.QUALITY_SYSTEM,
        prompt=prompts.fence("resume", resume_text),
        schema=QualityReview,
        step="Review your writing",
    )


def write_feedback(
    llm: StructuredLLM,
    models: Models,
    resume_text: str,
    job: JobRequirements,
    matches: list[EvidenceMatch],
    quality: QualityReview,
) -> FeedbackPlan:
    """Feedback Agent: a ranked plan plus rewrites built only from the student's facts."""
    gaps = [
        {"id": m.requirement_id, "status": m.status.value, "note": m.note}
        for m in matches
        if m.status.value != "matched"
    ]
    findings = [f.model_dump(mode="json") for f in quality.findings]
    context = json.dumps(
        {"role": job.role_title, "gaps": gaps, "writing_findings": findings}, indent=1
    )
    return llm.generate(
        model=models.smart,
        system=prompts.FEEDBACK_SYSTEM,
        prompt=f"Findings so far:\n{context}\n\n{prompts.fence('resume', resume_text)}",
        schema=FeedbackPlan,
        step="Write your plan",
    )


def _with_unique_ids(job: JobRequirements) -> JobRequirements:
    """Models sometimes repeat ids. Renumber so every requirement is addressable."""
    ids = [r.id for r in job.requirements]
    if len(set(ids)) == len(ids) and all(ids):
        return job
    renumbered = [r.model_copy(update={"id": f"R{i}"}) for i, r in enumerate(job.requirements, 1)]
    return job.model_copy(update={"requirements": renumbered})
