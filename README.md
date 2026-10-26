# ResumeMania Personal

**Want a resume that fits the job you want?**

Paste a job post and your resume. In about 10 seconds you see what matches, what's missing and exactly what to fix. Every rewrite uses only facts already in your resume, so nothing is made up.

- No account needed
- Stays on your laptop (saved in a local SQLite file)
- Never makes up facts: invented numbers become `[N]`, unproven skills get a `[CONFIRM]` flag

## Start in 3 minutes

You need Python 3.10 or newer and a free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/Uchiha-Itachi0/resumemania-personal.git
cd resumemania-personal
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

Open `.env` and paste your key after `GEMINI_API_KEY=`. Then:

```bash
streamlit run app.py
```

The app opens at http://localhost:8501. Press **Fill in a sample** to try it before using your own resume.

## What you get

| Tab | What it shows |
|---|---|
| Your plan | 3 to 6 fixes, highest impact first, plus keywords your resume doesn't show yet |
| Requirements | Every requirement from the job, marked Shown, Partly shown or Not shown yet, with the exact line from your resume that proves it |
| Rewrites | Suggested bullet rewrites. You switch each one on, edit it, fill in `[N]`, confirm it's true, and save a new version |
| Writing | Vague bullets, missing results, weak verbs |
| ATS check | Headings, contact details, length, bullets and page count |

You can download the report as Markdown and your latest resume as a plain, ATS-friendly DOCX. **My resumes** keeps every version and every check, and lets you delete all of it.

## How it works

Five small AI agents each do one job, and plain Python does everything that must be exact.

```
 Resume Parser ─┐                 ┌─ Evidence Matcher ─┐
                ├── in parallel ─>┤                    ├─> Feedback ─> Validation gate ─> Score
 JD Analyzer ───┘                 └─ Quality Reviewer ─┘
```

| Step | Model | File |
|---|---|---|
| Read your resume, read the job | `GEMINI_MODEL_FAST` (default `gemini-3.5-flash-lite`) | `resumemania/agents.py` |
| Match evidence, review writing, write the plan | `GEMINI_MODEL_SMART` (default `gemini-3.5-flash-lite`) | `resumemania/agents.py` |
| Validation gate: strip invented numbers, flag unproven skills, drop fake quotes | No AI | `resumemania/gate.py` |
| Fit score and keyword coverage | No AI | `resumemania/scoring.py` |
| ATS readability | No AI | `resumemania/readability.py` |

**The score.** Must-have requirements count double. Shown = full credit, partly shown = half, not shown = none. It's an estimate of how well your resume shows what the job asks for. It is not a hiring chance. Keyword coverage counts each keyword once, so repeating words doesn't help.

**Speed and outages.** A full check takes about 10 seconds. Every AI call has a timeout. If a model is overloaded (Google returns 503 or 504), the app moves to the next model in `GEMINI_MODEL_FALLBACKS` and skips the busy one for 5 minutes, so a demand spike slows one step, not the whole run.

**Safety.** Resume and job text are wrapped in tags and the model is told never to follow instructions inside them. Every model reply is validated against a Pydantic schema and retried if it's malformed. Logs record step names and timings, never resume text.

## Project layout

```
app.py                  Streamlit entry point and navigation
resumemania/            The engine (no Streamlit imports, easy to reuse)
  config.py             Settings from .env
  schemas.py            Pydantic models passed between agents
  llm.py                Gemini client with structured output and retries, plus FakeLLM for tests
  prompts.py            One prompt per agent
  agents.py             The five agents
  pipeline.py           Orchestrator: runs the agents, the gate and scoring
  gate.py, scoring.py, readability.py, ingest.py, report.py, storage.py
ui/                     Streamlit pages, theme, components and all copy (ui/copy.py)
samples/                A sample resume and job description
tests/                  Unit, integration and end-to-end UI tests (no API key needed)
```

## Settings (`.env`)

| Variable | Default | What it does |
|---|---|---|
| `GEMINI_API_KEY` | (required) | Your Gemini key |
| `GEMINI_MODEL_FAST` | `gemini-3.5-flash-lite` | Model for reading the resume and job |
| `GEMINI_MODEL_SMART` | `gemini-3.5-flash-lite` | Model for matching, review and rewrites. Set `gemini-3.8-flash` for deeper answers once Google's capacity issues are fixed |
| `GEMINI_MODEL_FALLBACKS` | `gemini-3.5-flash` | Tried in order when a model is busy, rate limited or too slow |
| `GEMINI_TIMEOUT_SECONDS` | `45` | Give up on one AI call after this long and try the next model |
| `RESUMEMANIA_DB_PATH` | `data/resumemania.db` | Where your history is saved |
| `RESUMEMANIA_MAX_UPLOAD_MB` | `5` | Largest resume file you can upload |

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest --cov
ruff check .
```

The tests use a fake model, so they run offline in a few seconds.

## Troubleshooting

| You see | Do this |
|---|---|
| "Add your Gemini key to start" | Create `.env` from `.env.example`, add your key, restart the app |
| "Your Gemini API key was rejected" | Copy the key again from AI Studio. No quotes or spaces |
| "Gemini is busy" or a slow first check | Google is overloaded. Wait a minute, or set `GEMINI_MODEL_SMART=gemini-3.5-flash-lite` |
| "Model ... was not found" | Change `GEMINI_MODEL_FAST` or `GEMINI_MODEL_SMART` in `.env` to a model your key can use |
| "We could only read a little text" | Your PDF is probably a scan. Upload the DOCX or paste the text |

## Privacy

Your resume, versions and reports are saved only in `data/` on your laptop, which is git-ignored. To analyse it, the text is sent to Google Gemini using your own API key. Delete any resume and all its reports from **My resumes**.
