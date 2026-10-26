"""Every user-facing string in one place.

House rules (VMA Playbook): outcome first, short words, specific numbers, "you" over "we",
no em dashes, no AI filler words, and ONE call to action worded the same everywhere.
"""

CTA = "Check my resume"
CTA_AGAIN = "Check my new version"

APP_NAME = "ResumeMania"

HERO_EYEBROW = "Free resume coach. Private, on your laptop."
HERO_TITLE = "<span class='g1'>Do you</span> <span class='g2'>want a resume</span> that <em>fits the job?</em>"
HERO_SUB = (
    "Paste the job post and your resume. See what matches, what's missing "
    "and what to fix, in about 10 seconds."
)
HERO_TICKS = ("No account needed", "Stays on your laptop", "Never makes up facts")

JOB_LABEL = "01 · The job"
JOB_ROLE = "Role you're applying for (optional)"
JOB_ROLE_HINT = "e.g. Data Analyst Intern"
JOB_TEXT = "Job description"
JOB_TEXT_HINT = "Paste the full job post: duties, must-haves and nice-to-haves."

RESUME_LABEL = "02 · Your resume"
RESUME_UPLOAD = "Upload"
RESUME_PASTE = "Paste"
RESUME_SAVED = "Saved"
RESUME_UPLOAD_HELP = "PDF, DOCX or TXT, up to {mb} MB."
RESUME_PASTE_HINT = "Paste your resume text here."
RESUME_NAME = "Name this resume"
RESUME_NAME_HINT = "e.g. Main resume"
RESUME_PICK = "Pick a saved resume"

SAMPLE_BUTTON = "Fill in a sample"
SAMPLE_DONE = "Sample job and resume added. Press Check my resume."

HOW_EYEBROW = "How it works"
HOW_TAGS = ("Ready in 5 seconds", "Ready in 10 seconds", "Only your facts")
HOW_TITLE = "Three steps to a resume that <em>fits.</em>"
HOW_STEPS = (
    ("Paste the job", "We turn the post into a checklist of must-haves and nice-to-haves."),
    ("Add your resume", "We find the line in your resume that proves each one."),
    ("Fix what's missing", "Get rewrites built only from your facts. You approve every word."),
)

FAQ = (
    ("Is my resume private?",
     "Yes. It's saved only on your laptop. The text is sent to Google Gemini to be read, "
     "using your own API key."),
    ("Will it add skills I don't have?",
     "No. Rewrites only use facts already in your resume. Missing numbers show as [N] "
     "for you to fill in."),
    ("Is the score my chance of getting hired?",
     "No. It's an estimate of how well your resume shows what the job asks for."),
)

SETUP_TITLE = "Add your Gemini key to start"
SETUP_BODY = "It takes about 2 minutes, and the key stays on your laptop."
SETUP_STEPS = (
    "Get a free key at <code>aistudio.google.com/apikey</code>",
    "Copy <code>.env.example</code> to <code>.env</code> and paste it after <code>GEMINI_API_KEY=</code>",
    "Stop the app and run <code>streamlit run app.py</code> again",
)

RUNNING = "Checking your resume"
RUN_DONE = "Done. Your report is ready."
ERR_NEED_RESUME = "Add your resume first: upload a file, paste the text or pick a saved one."

RESULT_EYEBROW = "Resume check · {role}"
RESULT_TITLE = "You show <em>{score}%</em> of what this job asks for."
RESULT_SUB = "An estimate of fit, not a hiring chance. Based on {n} requirements."
NO_REPORT_TITLE = "No report <em>yet.</em>"
NO_REPORT_SUB = "Check your resume against a job and your report shows up here."

TILE_FIT = "Fit estimate"
TILE_KEYWORDS = "Keywords found"
TILE_MUSTS = "Must-haves shown"
TILE_FIRST = "Do this first"

TAB_PLAN = "Your plan"
TAB_REQS = "Requirements"
TAB_EDITS = "Rewrites"
TAB_WRITING = "Writing"
TAB_ATS = "ATS check"

STATUS_TEXT = {"matched": "Shown", "partial": "Partly shown", "missing": "Not shown yet"}
STATUS_CLASS = {"matched": "good", "partial": "part", "missing": "miss"}
NEED_TEXT = {"must": "Must have", "nice": "Nice to have"}
SEVERITY_TEXT = {"high": "High impact", "medium": "Medium", "low": "Small fix"}

MISSING_KEYWORDS_TITLE = "Keywords not in your resume yet"
MISSING_KEYWORDS_NOTE = (
    "Only add one if it's true. Missing here doesn't mean you lack the skill, "
    "just that your resume doesn't show it."
)
STRENGTHS_TITLE = "Already working"
NO_EVIDENCE = "Nothing in your resume shows this yet."

EDITS_INTRO = (
    "Each rewrite uses only facts from your resume. Fill in every <span class='rm-mark'>[N]</span> "
    "and <span class='rm-mark'>[CONFIRM]</span> before you save."
)
EDIT_USE = "Use this rewrite"
EDIT_AFTER = "Rewrite (edit freely)"
EDITS_NONE = "No rewrites this time. Your bullets read well for this job."
CONFIRM_TRUE = "Everything in the rewrites I'm using is true."
SAVE_VERSION = "Save as new version"
SAVED_VERSION = "Saved as version {n}. Check it against the same job to see what changed."
ERR_PLACEHOLDERS = "Fill in every [N] and [CONFIRM] in the rewrites you're using first."
ERR_NONE_PICKED = "Turn on at least one rewrite to save a new version."

DOWNLOAD_REPORT = "Download report"
DOWNLOAD_RESUME = "Download resume (.docx)"
GATE_NOTES = "What we removed to keep this honest"

HISTORY_TITLE = "Your resumes, <em>version by version.</em>"
HISTORY_SUB = "Every check you've run. Saved only on this laptop."
HISTORY_EMPTY = "No resumes yet. Check one against a job to start your history."
HISTORY_OPEN = "Open"
HISTORY_DELETE = "Delete this resume"
HISTORY_DELETE_CONFIRM = "Yes, delete it and every report"
HISTORY_DELETED = "Deleted. Nothing about that resume is left on this laptop."
