"""Small HTML building blocks. Every piece of user or model text goes through `esc`."""

from __future__ import annotations

from html import escape

import streamlit as st

CHECK_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#171717" '
    'stroke-width="2.6" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
)
CROSS_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C93A22" '
    'stroke-width="2.6" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>'
)


def esc(text: object) -> str:
    return escape(str(text), quote=True)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def with_marks(text: str) -> str:
    """Escape text, then highlight [N] and [CONFIRM] placeholders."""
    safe = esc(text)
    for mark in ("[N]", "[CONFIRM]"):
        safe = safe.replace(mark, f"<span class='rm-mark'>{mark}</span>")
    return safe


def eyebrow(text: str) -> str:
    return f"<span class='rm-eyebrow'>{esc(text)}</span>"


def hero(eyebrow_text: str, title_html: str, sub: str, ticks: tuple[str, ...]) -> None:
    items = "".join(f"<li>{CHECK_SVG}{esc(t)}</li>" for t in ticks)
    badge = f"<span class='rm-badge'><span class='dot'></span>{esc(eyebrow_text)}</span>"
    html(
        f"<section class='rm-hero'>{badge}<h1>{title_html}</h1>"
        f"<p>{esc(sub)}</p><ul class='rm-ticks'>{items}</ul></section>"
    )


def page_title(eyebrow_text: str, title_html: str, sub: str = "") -> None:
    sub_html = f"<p>{esc(sub)}</p>" if sub else ""
    html(f"<div class='rm-page-title'>{eyebrow(eyebrow_text)}<h1>{title_html}</h1>{sub_html}</div>")


def section_title(eyebrow_text: str, title_html: str) -> None:
    html(f"<div style='margin:72px 0 22px;text-align:center'>{eyebrow(eyebrow_text)}"
         f"<h2 style='margin:8px 0 0;font-size:clamp(30px,3.6vw,44px)'>{title_html}</h2></div>")


def label(text: str) -> None:
    html(f"<div class='rm-label' style='margin-bottom:6px'>{esc(text)}</div>")


def stat_tile(label_text: str, big: str, unit: str = "", sub: str = "", bar: float | None = None) -> str:
    unit_html = f"<span class='unit'>{esc(unit)}</span>" if unit else ""
    bar_html = (
        f"<span class='rm-bar' aria-hidden='true'><span style='width:{max(0, min(100, bar * 100)):.0f}%'>"
        "</span></span>" if bar is not None else ""
    )
    sub_html = f"<span class='sub'>{esc(sub)}</span>" if sub else ""
    return (
        f"<article class='rm-tile'><span class='rm-label'>{esc(label_text)}</span>"
        f"<span style='display:flex;align-items:baseline;gap:6px'><span class='big'>{esc(big)}</span>"
        f"{unit_html}</span>{bar_html}{sub_html}</article>"
    )


def dark_card(label_text: str, title: str, body: str) -> str:
    return (
        f"<article class='rm-dark'><span class='rm-label'>{esc(label_text)}</span>"
        f"<h3>{esc(title)}</h3><p>{esc(body)}</p></article>"
    )


def pill(text: str, kind: str = "") -> str:
    return f"<span class='rm-pill {esc(kind)}'>{esc(text)}</span>"


def chips(items: list[str], kind: str = "mono") -> str:
    return "<div class='rm-chips'>" + "".join(pill(i, kind) for i in items) + "</div>"
