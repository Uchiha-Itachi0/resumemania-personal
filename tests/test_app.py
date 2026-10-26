"""End-to-end UI tests with Streamlit's AppTest. The AI is replaced by FakeLLM."""

from __future__ import annotations

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import ui.state as ui_state
from ui import copy

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = 30


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RESUMEMANIA_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr("resumemania.config.PROJECT_ROOT", tmp_path)  # ignore a real .env
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def _all_markdown(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def _button(at: AppTest, text: str):
    return next(b for b in at.button if b.label == text)


def test_home_without_key_shows_setup_and_disables_cta(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    assert not at.exception
    md = _all_markdown(at)
    assert copy.SETUP_TITLE in md
    assert "fits the job" in md
    assert _button(at, copy.CTA).disabled


def test_full_flow_sample_to_report_to_new_version(monkeypatch, fake_llm):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ui_state, "llm", lambda: fake_llm)

    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    _button(at, copy.SAMPLE_BUTTON).click().run()
    assert copy.SAMPLE_DONE in [s.value for s in at.success]

    _button(at, copy.CTA).click().run()
    assert not at.exception, at.exception
    md = _all_markdown(at)
    assert "of what this job asks for" in md
    assert "Strong SQL" in md
    assert "Not shown yet" in md

    # Turn on the rewrite. It still has [N], so saving must be blocked.
    at.toggle[0].set_value(True).run()
    at.checkbox[0].check().run()
    _button(at, copy.SAVE_VERSION).click().run()
    assert copy.ERR_PLACEHOLDERS in [e.value for e in at.error]

    # Fill in the number and save.
    at.text_area[0].set_value("Built a Power BI dashboard tracking sales for 12 stores.").run()
    _button(at, copy.SAVE_VERSION).click().run()
    assert any("Saved as version 2" in s.value for s in at.success)
    assert any(b.label == copy.CTA_AGAIN for b in at.button)


def test_short_job_description_is_rejected_before_saving(monkeypatch, fake_llm, resume_text):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ui_state, "llm", lambda: fake_llm)
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    at.text_area(key=ui_state.JD_TEXT).set_value("Hiring interns").run()
    at.text_area(key=ui_state.PASTED_RESUME).set_value(resume_text).run()
    _button(at, copy.CTA).click().run()
    assert any("full job description" in e.value for e in at.error)
    assert ui_state.storage().list_resumes() == []
    assert fake_llm.calls == []


def test_missing_resume_shows_error(monkeypatch, fake_llm, jd_text):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ui_state, "llm", lambda: fake_llm)
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    at.text_area(key=ui_state.JD_TEXT).set_value(jd_text).run()
    _button(at, copy.CTA).click().run()
    assert copy.ERR_NEED_RESUME in [e.value for e in at.error]


def test_history_lists_and_deletes(monkeypatch, fake_llm):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ui_state, "llm", lambda: fake_llm)
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    _button(at, copy.SAMPLE_BUTTON).click().run()
    _button(at, copy.CTA).click().run()

    at.switch_page("ui/pages/history.py").run()
    assert not at.exception
    assert "Sample: Priya" in _all_markdown(at)
    _button(at, copy.HISTORY_DELETE_CONFIRM).click().run()
    assert copy.HISTORY_DELETED in [s.value for s in at.success]
    assert ui_state.storage().list_resumes() == []


def test_report_page_without_report_points_home(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    at.switch_page("ui/pages/results.py").run()
    assert "No report" in _all_markdown(at)


def test_failed_check_saves_nothing(monkeypatch):
    from resumemania.llm import FakeLLM, LLMError
    from resumemania.schemas import ParsedResume

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    failing = FakeLLM({ParsedResume: LLMError("Your Gemini API key was rejected.")})
    monkeypatch.setattr(ui_state, "llm", lambda: failing)
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    _button(at, copy.SAMPLE_BUTTON).click().run()
    _button(at, copy.CTA).click().run()
    assert any("key was rejected" in e.value for e in at.error)
    assert ui_state.storage().list_resumes() == []
