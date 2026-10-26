"""ATS readability checks. Pure functions, no AI."""

from __future__ import annotations

import re

from .schemas import ReadabilityCheck

STANDARD_HEADINGS = ("education", "experience", "skills", "projects")
MIN_WORDS = 250
MAX_WORDS = 900
MAX_PDF_PAGES = 2
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
BULLET_RE = re.compile(r"^\s*([•\-*▪●◦]|\d+[.)])\s+", re.MULTILINE)
# PDF text extraction often drops bullet symbols, so a line that opens with an action verb
# also counts as a bullet.
ACTION_VERBS = (
    "built", "designed", "developed", "led", "shipped", "created", "implemented", "improved",
    "reduced", "increased", "managed", "analysed", "analyzed", "automated", "delivered", "wrote",
    "made", "worked", "helped", "cleaned", "launched", "owned", "optimised", "optimized",
    "migrated", "deployed", "trained", "researched", "integrated", "cut", "grew", "ran",
)
VERB_LINE_RE = re.compile(rf"^\s*({'|'.join(ACTION_VERBS)})\b", re.MULTILINE | re.IGNORECASE)


def check_readability(text: str, source: str, page_count: int) -> list[ReadabilityCheck]:
    lower = text.lower()
    words = len(text.split())
    found_headings = [h for h in STANDARD_HEADINGS if re.search(rf"^\s*{h}\b", lower, re.MULTILINE)]
    missing_headings = [h.title() for h in STANDARD_HEADINGS if h not in found_headings]

    checks = [
        ReadabilityCheck(
            label="Text can be read",
            passed=words >= 80,
            detail=f"We read {words} words."
            if words >= 80
            else "Very little text came out. ATS tools may see a blank page.",
        ),
        ReadabilityCheck(
            label="Standard section headings",
            passed=not missing_headings,
            detail="Found Education, Experience, Skills and Projects."
            if not missing_headings
            else f"Not found: {', '.join(missing_headings)}. Use plain headings ATS tools know.",
        ),
        ReadabilityCheck(
            label="Email and phone",
            passed=bool(EMAIL_RE.search(text)) and bool(PHONE_RE.search(text)),
            detail="Both found." if EMAIL_RE.search(text) and PHONE_RE.search(text)
            else "Add an email and phone number as plain text near the top.",
        ),
        ReadabilityCheck(
            label="Length",
            passed=MIN_WORDS <= words <= MAX_WORDS,
            detail=_length_detail(words),
        ),
        ReadabilityCheck(
            label="Bullet points",
            passed=_bullet_count(text) >= 3,
            detail="Bullets found." if _bullet_count(text) >= 3
            else "Few bullets found. Short bullets are easier to scan than paragraphs.",
        ),
    ]
    if source == "pdf":
        checks.append(
            ReadabilityCheck(
                label="Page count",
                passed=page_count <= MAX_PDF_PAGES,
                detail=f"{page_count} page(s)." if page_count <= MAX_PDF_PAGES
                else f"{page_count} pages. Students usually keep it to 1 or 2.",
            )
        )
    return checks


def _bullet_count(text: str) -> int:
    return len(BULLET_RE.findall(text)) + len(VERB_LINE_RE.findall(text))


def _length_detail(words: int) -> str:
    if words < MIN_WORDS:
        return f"{words} words. Most student resumes have {MIN_WORDS} to {MAX_WORDS}."
    if words > MAX_WORDS:
        return f"{words} words. Cut to under {MAX_WORDS} so the best parts stand out."
    return f"{words} words. A good length."
