"""Run an analysis with live progress, save it, and open the report."""

from __future__ import annotations

import logging
from collections.abc import Callable

import streamlit as st

from resumemania.config import MissingApiKeyError
from resumemania.ingest import ExtractedText, IngestError
from resumemania.llm import LLMError
from resumemania.pipeline import STEPS, run_analysis
from resumemania.storage import ResumeVersion

from . import copy, state

logger = logging.getLogger(__name__)


def run_and_open(
    resume: ExtractedText,
    save_version: Callable[[], ResumeVersion],
    jd_text: str,
    target_role: str,
) -> None:
    """Analyse a resume against a JD. Only on success: save the version and report, open it."""
    with st.status(copy.RUNNING, expanded=True) as status:
        bar = st.progress(0.0)

        def on_progress(step: str, done: int, total: int) -> None:
            bar.progress(done / total)
            if step in STEPS:
                status.update(label=f"{copy.RUNNING}: {step.lower()}")
                st.write(f"{step}…")

        try:
            analysis = run_analysis(state.llm(), state.models(), resume, jd_text, target_role, on_progress)
        except (IngestError, LLMError, MissingApiKeyError) as exc:
            status.update(label=str(exc), state="error")
            st.error(str(exc))
            return
        except Exception:
            logger.exception("analysis failed")
            status.update(label="Something went wrong", state="error")
            st.error("Something went wrong on our side. Try again, and check the terminal for details.")
            return
        status.update(label=copy.RUN_DONE, state="complete")

    version = save_version()
    report_id = state.storage().save_report(version.id, jd_text, target_role, analysis)
    st.session_state[state.REPORT_ID] = report_id
    state.flash(copy.RUN_DONE)
    st.switch_page("ui/pages/results.py")
