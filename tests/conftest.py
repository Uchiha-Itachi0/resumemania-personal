from __future__ import annotations

from pathlib import Path

import pytest

from resumemania.agents import Models
from resumemania.llm import FakeLLM
from resumemania.schemas import (
    Action,
    EditSuggestion,
    EvidenceMatch,
    FeedbackPlan,
    JobRequirements,
    MatchResult,
    MatchStatus,
    ParsedResume,
    Priority,
    QualityFinding,
    QualityReview,
    Requirement,
    ResumeItem,
    Severity,
)
from resumemania.storage import Storage

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def resume_text() -> str:
    return (SAMPLES / "resume_priya.txt").read_text()


@pytest.fixture
def jd_text() -> str:
    return (SAMPLES / "jd_data_analyst_intern.txt").read_text()


@pytest.fixture
def models() -> Models:
    return Models(fast="fake-fast", smart="fake-smart")


@pytest.fixture
def job() -> JobRequirements:
    return JobRequirements(
        role_title="Data Analyst Intern",
        requirements=[
            Requirement(id="R1", text="Strong SQL", priority=Priority.MUST, keywords=["SQL"]),
            Requirement(id="R2", text="Python for analysis", priority=Priority.MUST,
                        keywords=["Python", "Pandas", "NumPy"]),
            Requirement(id="R3", text="Dashboards in Power BI or Tableau", priority=Priority.MUST,
                        keywords=["Power BI", "Tableau"]),
            Requirement(id="R4", text="A/B testing", priority=Priority.NICE, keywords=["A/B testing"]),
        ],
    )


@pytest.fixture
def matches() -> list[EvidenceMatch]:
    return [
        EvidenceMatch(requirement_id="R1", status=MatchStatus.MATCHED,
                      evidence=["Made a project on movie ratings using SQL."], where="Projects"),
        EvidenceMatch(requirement_id="R2", status=MatchStatus.MATCHED,
                      evidence=["Cleaned customer data using Python and Pandas."], where="Experience"),
        EvidenceMatch(requirement_id="R3", status=MatchStatus.PARTIAL,
                      evidence=["Helped with a dashboard."], where="Experience"),
        EvidenceMatch(requirement_id="R4", status=MatchStatus.MISSING, evidence=[]),
    ]


@pytest.fixture
def fake_llm(job: JobRequirements, matches: list[EvidenceMatch]) -> FakeLLM:
    return FakeLLM({
        ParsedResume: ParsedResume(
            name="Priya Sharma",
            skills=["Python", "Pandas", "SQL"],
            experience=[ResumeItem(title="Data Analyst Intern", organisation="Shreeji Retail",
                                   bullets=["Helped with a dashboard."])],
        ),
        JobRequirements: job,
        MatchResult: MatchResult(matches=matches),
        QualityReview: QualityReview(
            findings=[QualityFinding(issue="Vague bullet", severity=Severity.HIGH,
                                     location="Experience", quote="Helped with a dashboard.",
                                     why_it_matters="It hides what you built.")],
            strengths=["Clear sections"],
        ),
        FeedbackPlan: FeedbackPlan(
            actions=[Action(title="Show your dashboard work", detail="Name the tool and the users.",
                            priority=Severity.HIGH, requirement_ids=["R3"])],
            edits=[EditSuggestion(
                original_text="Helped with a dashboard.",
                proposed_text="Built a Power BI dashboard tracking sales for 40 stores.",
                rationale="Names the tool and the scope.", requirement_ids=["R3"],
            )],
        ),
    })


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")
