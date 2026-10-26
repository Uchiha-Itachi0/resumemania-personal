"""Typed data passed between agents. Every LLM output is validated against these."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING = "missing"


class Priority(str, Enum):
    MUST = "must"
    NICE = "nice"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------- Resume Parser Agent ----------


class ResumeItem(BaseModel):
    title: str = Field(description="Role, project or degree name")
    organisation: str = Field(default="", description="Company, college or client")
    dates: str = Field(default="")
    bullets: list[str] = Field(default_factory=list, description="Bullets copied word for word")


class ParsedResume(BaseModel):
    name: str = Field(default="")
    summary: str = Field(default="")
    skills: list[str] = Field(default_factory=list)
    experience: list[ResumeItem] = Field(default_factory=list)
    projects: list[ResumeItem] = Field(default_factory=list)
    education: list[ResumeItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(
        default_factory=list, description="Common sections not found, e.g. Projects"
    )
    low_confidence_notes: list[str] = Field(
        default_factory=list, description="Parts that were hard to read"
    )

    def all_bullets(self) -> list[str]:
        items = [*self.experience, *self.projects, *self.education]
        return [bullet for item in items for bullet in item.bullets]


# ---------- JD Analysis Agent ----------


class Requirement(BaseModel):
    id: str = Field(description="Short id like R1, R2")
    text: str = Field(description="The requirement in plain words")
    priority: Priority
    keywords: list[str] = Field(default_factory=list, description="Terms a recruiter scans for")


class JobRequirements(BaseModel):
    role_title: str = Field(default="")
    requirements: list[Requirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


# ---------- Keyword / Evidence Matching Agent ----------


class EvidenceMatch(BaseModel):
    requirement_id: str
    status: MatchStatus
    evidence: list[str] = Field(
        default_factory=list, description="Exact quotes from the resume that show this"
    )
    where: str = Field(default="", description="Section the evidence sits in")
    note: str = Field(default="", description="One short line on why this status")


class MatchResult(BaseModel):
    matches: list[EvidenceMatch] = Field(default_factory=list)


# ---------- Resume Quality Agent ----------


class QualityFinding(BaseModel):
    issue: str = Field(description="Short label, e.g. Vague bullet")
    severity: Severity
    location: str = Field(default="", description="Section or bullet it applies to")
    quote: str = Field(default="", description="Exact text from the resume, if any")
    why_it_matters: str = Field(default="")


class QualityReview(BaseModel):
    findings: list[QualityFinding] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)


# ---------- Feedback Agent ----------


class EditSuggestion(BaseModel):
    original_text: str = Field(description="Exact bullet from the resume")
    proposed_text: str = Field(description="Rewrite using only facts already in the resume")
    rationale: str = Field(description="Why this edit helps, in one line")
    requirement_ids: list[str] = Field(default_factory=list)
    flags: list[str] = Field(
        default_factory=list, description="Set by the validation gate, not the model"
    )


class Action(BaseModel):
    title: str
    detail: str
    priority: Severity
    requirement_ids: list[str] = Field(default_factory=list)


class FeedbackPlan(BaseModel):
    actions: list[Action] = Field(default_factory=list)
    edits: list[EditSuggestion] = Field(default_factory=list)


# ---------- Deterministic checks ----------


class ReadabilityCheck(BaseModel):
    label: str
    passed: bool
    detail: str


class Analysis(BaseModel):
    """Everything one run produces. Saved to SQLite as JSON."""

    resume: ParsedResume
    job: JobRequirements
    matches: list[EvidenceMatch]
    quality: QualityReview
    plan: FeedbackPlan
    readability: list[ReadabilityCheck]
    score: int = Field(ge=0, le=100)
    keyword_coverage: float = Field(ge=0.0, le=1.0)
    keywords_found: list[str] = Field(default_factory=list)
    keywords_missing: list[str] = Field(default_factory=list)
    scoring_version: str
    gate_notes: list[str] = Field(default_factory=list)

    def requirement(self, requirement_id: str) -> Requirement | None:
        return next((r for r in self.job.requirements if r.id == requirement_id), None)

    def match_for(self, requirement_id: str) -> EvidenceMatch | None:
        return next((m for m in self.matches if m.requirement_id == requirement_id), None)
