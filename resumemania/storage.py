"""Local SQLite storage. Everything stays on the student's own computer."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .schemas import Analysis

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY,
    resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    change_summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE (resume_id, version_number)
);
CREATE TABLE IF NOT EXISTS job_analyses (
    id INTEGER PRIMARY KEY,
    target_role TEXT NOT NULL DEFAULT '',
    job_description TEXT NOT NULL,
    requirements_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback_reports (
    id INTEGER PRIMARY KEY,
    resume_version_id INTEGER NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
    job_analysis_id INTEGER NOT NULL REFERENCES job_analyses(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    keyword_coverage REAL NOT NULL,
    analysis_json TEXT NOT NULL,
    scoring_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edit_suggestions (
    id INTEGER PRIMARY KEY,
    feedback_report_id INTEGER NOT NULL REFERENCES feedback_reports(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    proposed_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    student_approved INTEGER NOT NULL
);
"""


@dataclass(frozen=True)
class ResumeVersion:
    id: int
    resume_id: int
    version_number: int
    content: str
    source: str
    page_count: int
    change_summary: str
    created_at: str


@dataclass(frozen=True)
class ReportSummary:
    id: int
    resume_id: int
    resume_label: str
    version_number: int
    target_role: str
    score: int
    keyword_coverage: float
    created_at: str


@dataclass(frozen=True)
class StoredReport:
    summary: ReportSummary
    analysis: Analysis
    resume_version_id: int
    job_description: str


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Storage:
    """Repository over one SQLite file. Opens a short-lived connection per call."""

    def __init__(self, db_path: Path):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------- resumes ----------

    def create_resume(self, label: str, content: str, source: str, page_count: int = 1) -> ResumeVersion:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO resumes (label, created_at) VALUES (?, ?)", (label.strip() or "My resume", _now())
            )
            return self._insert_version(conn, cur.lastrowid, content, source, page_count, "First upload")

    def add_version(self, resume_id: int, content: str, change_summary: str,
                    source: str = "edited", page_count: int = 1) -> ResumeVersion:
        with self._connect() as conn:
            return self._insert_version(conn, resume_id, content, source, page_count, change_summary)

    def _insert_version(self, conn: sqlite3.Connection, resume_id: int, content: str,
                        source: str, page_count: int, change_summary: str) -> ResumeVersion:
        row = conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 FROM resume_versions WHERE resume_id = ?",
            (resume_id,),
        ).fetchone()
        number = int(row[0])
        created = _now()
        cur = conn.execute(
            "INSERT INTO resume_versions (resume_id, version_number, content, source, page_count,"
            " change_summary, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (resume_id, number, content, source, page_count, change_summary, created),
        )
        return ResumeVersion(cur.lastrowid, resume_id, number, content, source, page_count,
                             change_summary, created)

    def list_resumes(self) -> list[tuple[int, str, int]]:
        """(resume_id, label, latest version number), newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT r.id, r.label, MAX(v.version_number) AS latest FROM resumes r"
                " JOIN resume_versions v ON v.resume_id = r.id GROUP BY r.id ORDER BY r.id DESC"
            ).fetchall()
        return [(row["id"], row["label"], row["latest"]) for row in rows]

    def list_versions(self, resume_id: int) -> list[ResumeVersion]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM resume_versions WHERE resume_id = ? ORDER BY version_number DESC",
                (resume_id,),
            ).fetchall()
        return [ResumeVersion(**dict(row)) for row in rows]

    def latest_version(self, resume_id: int) -> ResumeVersion | None:
        versions = self.list_versions(resume_id)
        return versions[0] if versions else None

    def get_version(self, version_id: int) -> ResumeVersion | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM resume_versions WHERE id = ?", (version_id,)).fetchone()
        return ResumeVersion(**dict(row)) if row else None

    def delete_resume(self, resume_id: int) -> None:
        """Delete a resume, every version and every report built on it."""
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM job_analyses WHERE id IN (SELECT f.job_analysis_id FROM feedback_reports f"
                " JOIN resume_versions v ON v.id = f.resume_version_id WHERE v.resume_id = ?)",
                (resume_id,),
            )
            conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))

    # ---------- reports ----------

    def save_report(self, resume_version_id: int, job_description: str,
                    target_role: str, analysis: Analysis) -> int:
        with self._connect() as conn:
            job_id = conn.execute(
                "INSERT INTO job_analyses (target_role, job_description, requirements_json, created_at)"
                " VALUES (?, ?, ?, ?)",
                (target_role, job_description, analysis.job.model_dump_json(), _now()),
            ).lastrowid
            report_id = conn.execute(
                "INSERT INTO feedback_reports (resume_version_id, job_analysis_id, score,"
                " keyword_coverage, analysis_json, scoring_version, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (resume_version_id, job_id, analysis.score, analysis.keyword_coverage,
                 analysis.model_dump_json(), analysis.scoring_version, _now()),
            ).lastrowid
        return int(report_id)

    def save_edit_decisions(self, report_id: int, decisions: list[tuple[str, str, str, bool]]) -> None:
        """Replace the stored decisions for a report. Each is (original, proposed, rationale, approved)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM edit_suggestions WHERE feedback_report_id = ?", (report_id,))
            conn.executemany(
                "INSERT INTO edit_suggestions (feedback_report_id, original_text, proposed_text,"
                " rationale, student_approved) VALUES (?, ?, ?, ?, ?)",
                [(report_id, o, p, r, int(a)) for o, p, r, a in decisions],
            )

    def list_reports(self, resume_id: int | None = None) -> list[ReportSummary]:
        query = _REPORT_SELECT + (" WHERE v.resume_id = ?" if resume_id is not None else "")
        params: tuple[int, ...] = (resume_id,) if resume_id is not None else ()
        with self._connect() as conn:
            rows = conn.execute(query + " ORDER BY f.id DESC", params).fetchall()
        return [_summary(row) for row in rows]

    def get_report(self, report_id: int) -> StoredReport | None:
        with self._connect() as conn:
            row = conn.execute(
                _REPORT_SELECT.replace("SELECT ", "SELECT f.analysis_json, f.resume_version_id,"
                                       " j.job_description, ", 1) + " WHERE f.id = ?",
                (report_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredReport(
            summary=_summary(row),
            analysis=Analysis.model_validate_json(row["analysis_json"]),
            resume_version_id=row["resume_version_id"],
            job_description=row["job_description"],
        )


_REPORT_SELECT = (
    "SELECT f.id, v.resume_id, r.label, v.version_number, j.target_role, f.score,"
    " f.keyword_coverage, f.created_at FROM feedback_reports f"
    " JOIN resume_versions v ON v.id = f.resume_version_id"
    " JOIN resumes r ON r.id = v.resume_id"
    " JOIN job_analyses j ON j.id = f.job_analysis_id"
)


def _summary(row: sqlite3.Row) -> ReportSummary:
    return ReportSummary(
        id=row["id"], resume_id=row["resume_id"], resume_label=row["label"],
        version_number=row["version_number"], target_role=row["target_role"],
        score=row["score"], keyword_coverage=row["keyword_coverage"], created_at=row["created_at"],
    )
