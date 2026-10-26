"""Home: the promise, the two inputs, one button."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from resumemania.ingest import ExtractedText, IngestError, extract_text, from_paste, validate_inputs
from ui import copy, state
from ui.components import esc, hero, html, label, section_title
from ui.run import run_and_open

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def _setup_card() -> None:
    steps = "".join(
        f"<li><span class='rm-num'>{i}</span><span>{step}</span></li>"
        for i, step in enumerate(copy.SETUP_STEPS, 1)
    )
    html(
        f"<article class='rm-dark' style='margin:28px 0'><span class='rm-label'>Setup</span>"
        f"<h3>{copy.SETUP_TITLE}</h3><p>{copy.SETUP_BODY}</p><ol>{steps}</ol></article>"
    )


def _fill_sample() -> None:
    st.session_state[state.JD_TEXT] = (SAMPLES / "jd_data_analyst_intern.txt").read_text()
    st.session_state[state.ROLE] = "Data Analyst Intern"
    st.session_state[state.PASTED_RESUME] = (SAMPLES / "resume_priya.txt").read_text()
    st.session_state[state.RESUME_NAME] = "Sample: Priya"
    state.flash(copy.SAMPLE_DONE)


def _job_inputs() -> tuple[str, str]:
    label(copy.JOB_LABEL)
    role = st.text_input(copy.JOB_ROLE, placeholder=copy.JOB_ROLE_HINT, key=state.ROLE)
    jd = st.text_area(copy.JOB_TEXT, placeholder=copy.JOB_TEXT_HINT, height=300, key=state.JD_TEXT)
    return role, jd


def _resume_inputs():
    """Returns a callable that turns the chosen input into a saved ResumeVersion, or None."""
    label(copy.RESUME_LABEL)
    store = state.storage()
    saved = store.list_resumes()
    tab_names = [copy.RESUME_PASTE, copy.RESUME_UPLOAD] + ([copy.RESUME_SAVED] if saved else [])
    tabs = st.tabs(tab_names)
    max_mb = state.settings().max_upload_mb

    with tabs[0]:
        pasted = st.text_area(copy.RESUME_PASTE_HINT, height=222, key=state.PASTED_RESUME,
                              label_visibility="collapsed", placeholder=copy.RESUME_PASTE_HINT)
    with tabs[1]:
        upload = st.file_uploader(copy.RESUME_UPLOAD, type=["pdf", "docx", "txt"],
                                  help=copy.RESUME_UPLOAD_HELP.format(mb=max_mb),
                                  label_visibility="collapsed")
        st.caption(copy.RESUME_UPLOAD_HELP.format(mb=max_mb))
    picked = None
    if saved:
        with tabs[2]:
            options = {f"{name} · version {latest}": rid for rid, name, latest in saved}
            choice = st.selectbox(copy.RESUME_PICK, list(options), index=None)
            picked = options.get(choice) if choice else None
    name = st.text_input(copy.RESUME_NAME, placeholder=copy.RESUME_NAME_HINT, key=state.RESUME_NAME)

    def resolve():
        """(text to check, function that saves it). Saving waits until inputs pass checks."""
        # Priority: a saved pick, then an upload, then pasted text.
        if picked is not None:
            version = store.latest_version(picked)
            if version is None:
                return None
            text = ExtractedText(version.content, version.source, version.page_count)
            return text, lambda: version
        if upload is not None:
            extracted = extract_text(upload.name, upload.getvalue(), max_mb)
        elif pasted.strip():
            extracted = from_paste(pasted)
        else:
            return None
        default_name = Path(upload.name).stem if upload is not None else "My resume"
        return extracted, lambda: store.create_resume(
            name or default_name, extracted.text, extracted.source, extracted.page_count
        )

    return resolve


def _how_it_works() -> None:
    section_title(copy.HOW_EYEBROW, copy.HOW_TITLE)
    cols = st.columns(3, gap="medium")
    for col, (title, body), tag in zip(cols, copy.HOW_STEPS, copy.HOW_TAGS, strict=True):
        with col:
            html(
                f"<article class='rm-step'><span class='rm-tag'>{esc(tag)}</span>"
                f"<span class='t'>{esc(title)}</span><span class='b'>{esc(body)}</span></article>"
            )
    section_title("Questions", "Before you <em>start.</em>")
    for question, answer in copy.FAQ:
        with st.expander(question):
            st.write(answer)


def _start(resolve, jd: str, role: str) -> None:
    try:
        chosen = resolve()
        if chosen is None:
            st.error(copy.ERR_NEED_RESUME)
            return
        extracted, save = chosen
        validate_inputs(extracted.text, jd)
    except IngestError as exc:
        st.error(str(exc))
        return
    run_and_open(extracted, save, jd, role)


def render() -> None:
    state.show_flash()
    hero(copy.HERO_EYEBROW, copy.HERO_TITLE, copy.HERO_SUB, copy.HERO_TICKS)
    has_key = state.settings().has_api_key
    if not has_key:
        _setup_card()

    with st.container(border=True):
        left, right = st.columns(2, gap="large")
        with left:
            role, jd = _job_inputs()
        with right:
            resolve = _resume_inputs()
        go = st.button(copy.CTA, type="primary", use_container_width=True, disabled=not has_key)
        st.button(copy.SAMPLE_BUTTON, on_click=_fill_sample, type="tertiary")

    if go:
        _start(resolve, jd, role)

    _how_it_works()


render()
