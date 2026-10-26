"""Personal Resume Orchestrator.

    parse resume ─┐                ┌─ match evidence ─┐
                  ├─ (parallel) ──>┤                  ├─> feedback ─> gate ─> score
    read the job ─┘                └─ review writing ─┘
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from . import agents
from .agents import Models
from .gate import run_gate
from .ingest import ExtractedText, IngestError, validate_inputs
from .llm import StructuredLLM
from .readability import check_readability
from .schemas import Analysis, FeedbackPlan
from .scoring import SCORING_VERSION, alignment_score, keyword_coverage

logger = logging.getLogger(__name__)

STEPS = ("Read your resume", "Read the job", "Match your evidence", "Review your writing",
         "Write your plan", "Check for made-up facts")

ProgressFn = Callable[[str, int, int], None]


def _noop(step: str, done: int, total: int) -> None:
    return None


def run_analysis(
    llm: StructuredLLM,
    models: Models,
    resume: ExtractedText,
    jd_text: str,
    target_role: str = "",
    on_progress: ProgressFn = _noop,
) -> Analysis:
    """Run every agent and return one validated Analysis. Raises on bad input or AI failure."""
    validate_inputs(resume.text, jd_text)
    started = time.perf_counter()
    total = len(STEPS)

    with ThreadPoolExecutor(max_workers=2) as pool:
        on_progress(STEPS[0], 0, total)
        parsed_f = pool.submit(agents.parse_resume, llm, models, resume.text)
        job_f = pool.submit(agents.analyze_jd, llm, models, jd_text, target_role)
        parsed, job = parsed_f.result(), job_f.result()
        on_progress(STEPS[2], 2, total)

        if not job.requirements:
            raise IngestError("We couldn't find any requirements in that job description.")

        matches_f = pool.submit(agents.match_evidence, llm, models, resume.text, job)
        quality_f = pool.submit(agents.review_quality, llm, models, resume.text)
        matches, quality = matches_f.result(), quality_f.result()
        on_progress(STEPS[4], 4, total)

    plan = agents.write_feedback(llm, models, resume.text, job, matches, quality)
    on_progress(STEPS[5], 5, total)

    gated = run_gate(resume.text, job, plan.edits, matches)
    coverage = keyword_coverage(job, resume.text)
    analysis = Analysis(
        resume=parsed,
        job=job,
        matches=gated.matches,
        quality=quality,
        plan=FeedbackPlan(actions=plan.actions, edits=gated.edits),
        readability=check_readability(resume.text, resume.source, resume.page_count),
        score=alignment_score(job, gated.matches),
        keyword_coverage=coverage.ratio,
        keywords_found=list(coverage.found),
        keywords_missing=list(coverage.missing),
        scoring_version=SCORING_VERSION,
        gate_notes=gated.notes,
    )
    on_progress("Done", total, total)
    logger.info(
        "analysis status=ok requirements=%d score=%d ms=%d",
        len(job.requirements), analysis.score, (time.perf_counter() - started) * 1000,
    )
    return analysis


def apply_edits(resume_text: str, accepted: list[tuple[str, str]]) -> str:
    """Return a new resume text with each accepted (original, proposed) pair swapped in.

    Matching ignores differences in spacing and line breaks, since PDFs wrap lines.
    """
    updated = resume_text
    for original, proposed in accepted:
        words = original.split()
        if not words:
            continue
        pattern = r"\s+".join(re.escape(w) for w in words)
        updated = re.sub(pattern, lambda _m, p=proposed: p, updated, count=1)
    return updated
