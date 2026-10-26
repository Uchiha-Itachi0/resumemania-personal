"""My resumes: every version and every check, with delete."""

from __future__ import annotations

import streamlit as st

from ui import copy, state
from ui.components import esc, html, page_title, pill


def _resume_card(resume_id: int, name: str, latest: int) -> None:
    store = state.storage()
    reports = store.list_reports(resume_id)
    with st.container(border=True):
        best = max((r.score for r in reports), default=None)
        best_html = pill(f"Best fit {best}%", "good") if best is not None else ""
        html(
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap'>"
            f"<h3 style='margin:0;font-size:24px'>{esc(name)}</h3>"
            f"<span style='display:flex;gap:6px'>{pill(f'{latest} version(s)', 'mono')}{best_html}</span></div>"
        )
        if not reports:
            st.caption("No checks yet for this resume.")
        for r in reports:
            cols = st.columns([3, 1, 1, 1], vertical_alignment="center")
            role = r.target_role or "Untitled job"
            cols[0].markdown(f"**{role}**  \nVersion {r.version_number} · {r.created_at[:10]}")
            cols[1].metric("Fit", f"{r.score}%", label_visibility="collapsed")
            cols[2].caption(f"Keywords {round(r.keyword_coverage * 100)}%")
            if cols[3].button(copy.HISTORY_OPEN, key=f"open_{r.id}", use_container_width=True):
                st.session_state[state.REPORT_ID] = r.id
                st.switch_page("ui/pages/results.py")

        with st.expander(copy.HISTORY_DELETE):
            st.caption("This removes every version and report for this resume from your laptop.")
            if st.button(copy.HISTORY_DELETE_CONFIRM, key=f"del_{resume_id}"):
                store.delete_resume(resume_id)
                if st.session_state.get(state.REPORT_ID) in {r.id for r in reports}:
                    st.session_state.pop(state.REPORT_ID, None)
                state.flash(copy.HISTORY_DELETED)
                st.rerun()


def render() -> None:
    state.show_flash()
    page_title("My resumes", copy.HISTORY_TITLE, copy.HISTORY_SUB)
    html("<div style='height:22px'></div>")
    resumes = state.storage().list_resumes()
    if not resumes:
        st.info(copy.HISTORY_EMPTY)
        if st.button(copy.CTA, type="primary"):
            st.switch_page("ui/pages/home.py")
        return
    for resume_id, name, latest in resumes:
        _resume_card(resume_id, name, latest)


render()
