"""ResumeMania Personal. Run with:  streamlit run app.py"""

from __future__ import annotations

import streamlit as st

from ui import copy
from ui.theme import apply_theme

st.set_page_config(page_title=f"{copy.APP_NAME}: does your resume fit the job?",
                   page_icon=":material/description:", layout="wide", initial_sidebar_state="collapsed")
apply_theme()

pages = [
    st.Page("ui/pages/home.py", title=copy.CTA, default=True),
    st.Page("ui/pages/results.py", title="My report", url_path="report"),
    st.Page("ui/pages/history.py", title="My resumes", url_path="resumes"),
]
st.navigation(pages, position="top").run()
