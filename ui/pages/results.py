"""Report: score, plan, requirement matrix, rewrite editor, writing notes, ATS checks."""

from __future__ import annotations

import streamlit as st

from resumemania.ingest import ExtractedText
from resumemania.pipeline import apply_edits
from resumemania.report import build_markdown_report, build_resume_docx
from resumemania.schemas import Analysis, MatchStatus, Priority
from resumemania.scoring import score_band
from resumemania.storage import StoredReport
from ui import copy, state
from ui.components import (
    CHECK_SVG,
    CROSS_SVG,
    chips,
    dark_card,
    esc,
    html,
    page_title,
    pill,
    stat_tile,
    with_marks,
)
from ui.run import run_and_open

PLACEHOLDERS = ("[N]", "[CONFIRM]")


def _header(report: StoredReport) -> None:
    a = report.analysis
    role = report.summary.target_role or a.job.role_title or "this job"
    page_title(
        copy.RESULT_EYEBROW.format(role=role),
        copy.RESULT_TITLE.format(score=a.score),
        copy.RESULT_SUB.format(n=len(a.job.requirements)),
    )
    html("<div style='height:22px'></div>")

    musts = [r for r in a.job.requirements if r.priority == Priority.MUST]
    musts_shown = sum(1 for r in musts if (m := a.match_for(r.id)) and m.status == MatchStatus.MATCHED)
    total_keywords = len(a.keywords_found) + len(a.keywords_missing)
    first = a.plan.actions[0] if a.plan.actions else None

    cols = st.columns(4, gap="small")
    tiles = [
        stat_tile(copy.TILE_FIT, f"{a.score}%", sub=score_band(a.score), bar=a.score / 100),
        stat_tile(copy.TILE_KEYWORDS, str(len(a.keywords_found)), f"of {total_keywords}",
                  bar=a.keyword_coverage),
        stat_tile(copy.TILE_MUSTS, str(musts_shown), f"of {len(musts)}",
                  sub="Partly shown ones count half in the score."),
        dark_card(copy.TILE_FIRST, first.title, first.detail) if first
        else dark_card(copy.TILE_FIRST, "Keep it up", "No urgent fixes for this job."),
    ]
    for col, tile in zip(cols, tiles, strict=True):
        with col:
            html(tile)


def _plan_tab(a: Analysis) -> None:
    left, right = st.columns([3, 2], gap="large")
    with left:
        rows = "".join(
            f"<div class='rm-action'><span class='rm-num'>{i}</span><div>"
            f"<div class='t'>{esc(act.title)} {pill(copy.SEVERITY_TEXT[act.priority.value], _sev_class(act.priority.value))}</div>"
            f"<div class='d'>{esc(act.detail)}</div></div></div>"
            for i, act in enumerate(a.plan.actions, 1)
        )
        html(f"<div>{rows}</div>")
    with right:
        if a.quality.strengths:
            html(f"<div class='rm-label' style='margin-bottom:8px'>{copy.STRENGTHS_TITLE}</div>")
            html("".join(f"<div class='rm-check'>{CHECK_SVG}<span>{esc(s)}</span></div>"
                         for s in a.quality.strengths))
        if a.keywords_missing:
            html(f"<div class='rm-label' style='margin:22px 0 10px'>{copy.MISSING_KEYWORDS_TITLE}</div>")
            html(chips(a.keywords_missing))
            html(f"<p class='rm-muted' style='margin-top:10px'>{copy.MISSING_KEYWORDS_NOTE}</p>")


def _sev_class(severity: str) -> str:
    return {"high": "miss", "medium": "part", "low": ""}[severity]


def _requirements_tab(a: Analysis) -> None:
    options = ["All", *copy.STATUS_TEXT.values()]
    pick = st.segmented_control("Show", options, default="All", label_visibility="collapsed")
    wanted = {v: k for k, v in copy.STATUS_TEXT.items()}.get(pick or "All")
    rows = []
    for req in a.job.requirements:
        match = a.match_for(req.id)
        status = match.status.value if match else MatchStatus.MISSING.value
        if wanted and status != wanted:
            continue
        evidence = (
            "".join(f"<div class='ev'>“{esc(q)}”</div>" for q in match.evidence)
            if match and match.evidence else f"<div class='note'>{copy.NO_EVIDENCE}</div>"
        )
        note = f"<div class='note'>{esc(match.note)}</div>" if match and match.note else ""
        rows.append(
            f"<div class='rm-row'><span class='id'>{esc(req.id)}</span><span class='req'>{esc(req.text)}</span>"
            f"<span class='pills'>{pill(copy.NEED_TEXT[req.priority.value], 'mono')}"
            f"{pill(copy.STATUS_TEXT[status], copy.STATUS_CLASS[status])}</span>{evidence}{note}</div>"
        )
    with st.container(border=True):
        html("".join(rows) or "<p class='rm-muted'>Nothing here.</p>")


def _edits_tab(report: StoredReport) -> None:
    a = report.analysis
    if not a.plan.edits:
        st.info(copy.EDITS_NONE)
        return
    html(f"<p class='rm-muted' style='font-size:15px'>{copy.EDITS_INTRO}</p>")
    chosen: list[tuple[str, str, str, bool]] = []
    for i, edit in enumerate(a.plan.edits):
        with st.container(border=True):
            html(f"<div class='rm-label'>Before</div><div class='rm-before'>{esc(edit.original_text)}</div>")
            html(f"<div class='rm-label' style='margin-top:12px'>Suggested</div>"
                 f"<div class='rm-quote'>{with_marks(edit.proposed_text)}</div>")
            html(f"<p class='rm-muted' style='margin:8px 0 0'>Why: {esc(edit.rationale)}</p>")
            for flag in edit.flags:
                html(f"<div class='rm-flag' style='margin-top:8px'>{with_marks(flag)}</div>")
            use = st.toggle(copy.EDIT_USE, key=f"use_{report.summary.id}_{i}")
            text = edit.proposed_text
            if use:
                text = st.text_area(copy.EDIT_AFTER, value=edit.proposed_text, key=f"txt_{report.summary.id}_{i}")
            chosen.append((edit.original_text, text.strip(), edit.rationale, use))
    _save_version(report, chosen)


def _save_version(report: StoredReport, chosen: list[tuple[str, str, str, bool]]) -> None:
    store = state.storage()
    confirmed = st.checkbox(copy.CONFIRM_TRUE, key=f"confirm_{report.summary.id}")
    if not st.button(copy.SAVE_VERSION, type="primary", disabled=not confirmed):
        return
    accepted = [(o, p) for o, p, _, use in chosen if use]
    if not accepted:
        st.error(copy.ERR_NONE_PICKED)
        return
    if any(mark in p for _, p in accepted for mark in PLACEHOLDERS):
        st.error(copy.ERR_PLACEHOLDERS)
        return
    current = store.get_version(report.resume_version_id)
    if current is None:
        st.error("We couldn't find the resume this report used. It may have been deleted.")
        return
    store.save_edit_decisions(report.summary.id, chosen)
    new_version = store.add_version(
        current.resume_id, apply_edits(current.content, accepted),
        f"Used {len(accepted)} rewrite(s) from report {report.summary.id}",
    )
    st.session_state["new_version_id"] = new_version.id
    state.flash(copy.SAVED_VERSION.format(n=new_version.version_number))
    st.rerun()


def _writing_tab(a: Analysis) -> None:
    if not a.quality.findings:
        st.info("No writing issues found.")
    for finding in a.quality.findings:
        with st.container(border=True):
            sev = finding.severity.value
            html(f"<div style='display:flex;justify-content:space-between;gap:12px;align-items:center'>"
                 f"<strong style='font-size:16px'>{esc(finding.issue)}</strong>"
                 f"{pill(copy.SEVERITY_TEXT[sev], _sev_class(sev))}</div>")
            if finding.quote:
                html(f"<div class='rm-quote' style='margin-top:10px'>“{esc(finding.quote)}”</div>")
            html(f"<p class='rm-muted' style='margin:10px 0 0'>{esc(finding.location)}"
                 f"{' · ' if finding.location else ''}{esc(finding.why_it_matters)}</p>")


def _ats_tab(a: Analysis) -> None:
    rows = "".join(
        f"<div class='rm-check'>{CHECK_SVG if c.passed else CROSS_SVG}<div><strong>{esc(c.label)}</strong>"
        f"<div class='d'>{esc(c.detail)}</div></div></div>"
        for c in a.readability
    )
    with st.container(border=True):
        html(rows)
    if a.resume.low_confidence_notes:
        st.caption("Hard to read: " + "; ".join(a.resume.low_confidence_notes))


def _downloads(report: StoredReport) -> None:
    store = state.storage()
    version = store.get_version(report.resume_version_id)
    latest = store.latest_version(version.resume_id) if version else None
    role = report.summary.target_role
    cols = st.columns(3)
    with cols[0]:
        st.download_button(copy.DOWNLOAD_REPORT, build_markdown_report(report.analysis, role),
                           file_name="resume-check.md", mime="text/markdown", use_container_width=True)
    if latest:
        with cols[1]:
            st.download_button(copy.DOWNLOAD_RESUME, build_resume_docx(latest.content),
                               file_name=f"resume-v{latest.version_number}.docx",
                               use_container_width=True)


def _check_new_version(report: StoredReport) -> None:
    version_id = st.session_state.get("new_version_id")
    version = state.storage().get_version(version_id) if version_id else None
    if version is None:
        return
    if st.button(copy.CTA_AGAIN, type="primary"):
        st.session_state.pop("new_version_id", None)
        resume = ExtractedText(version.content, version.source, version.page_count)
        run_and_open(resume, lambda: version, report.job_description, report.summary.target_role)


def render() -> None:
    state.show_flash()
    report_id = st.session_state.get(state.REPORT_ID)
    report = state.storage().get_report(report_id) if report_id else None
    if report is None:
        page_title("Report", copy.NO_REPORT_TITLE, copy.NO_REPORT_SUB)
        if st.button(copy.CTA, type="primary"):
            st.switch_page("ui/pages/home.py")
        return

    _check_new_version(report)
    _header(report)
    html("<div style='height:28px'></div>")
    tabs = st.tabs([copy.TAB_PLAN, copy.TAB_REQS, copy.TAB_EDITS, copy.TAB_WRITING, copy.TAB_ATS])
    with tabs[0]:
        _plan_tab(report.analysis)
    with tabs[1]:
        _requirements_tab(report.analysis)
    with tabs[2]:
        _edits_tab(report)
    with tabs[3]:
        _writing_tab(report.analysis)
    with tabs[4]:
        _ats_tab(report.analysis)

    html("<div style='height:28px'></div>")
    _downloads(report)
    if report.analysis.gate_notes:
        with st.expander(copy.GATE_NOTES):
            for note in report.analysis.gate_notes:
                st.write(note)


render()
