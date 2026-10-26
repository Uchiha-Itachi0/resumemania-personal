"""Design tokens and global CSS, matched to vibemyad.com.

Type: Inter (headings, tight tracking), Instrument Serif italic (one accent word per heading),
Plus Jakarta Sans (body and buttons), Geist Mono (small uppercase labels).
Color: white page, warm sand panels, ink text, lime pill CTA, graphite secondary buttons,
red signal tags for time-to-result.
"""

from __future__ import annotations

import streamlit as st

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800"
    "&family=Plus+Jakarta+Sans:wght@400;500;600;700"
    "&family=Instrument+Serif:ital@0;1"
    "&family=Geist+Mono:wght@400;500&display=swap"
)

CSS = """
<style>
@import url('__FONTS__');
:root{
  --page:#FFFFFF;--sand:#F7F6F3;--sand-2:#EFEDE8;--plate:#FBFAF8;
  --ink:#171717;--black:#0A0A0A;--body:#57554F;--meta:#6E6B64;--faint:#8F8C85;--mute:#A9A59D;--ghost:#C4C1B9;
  --line:#E4E1DA;--field:#DAD6CE;
  --graphite:#171717;--graphite-card:#1F1F1D;--graphite-line:#2E2D2A;--g-body:#A4A39C;--g-tag:#CFCBC3;
  --lime:#C7F24E;--lime-hover:#B8E85C;--lime-deep:#A8CE2E;--lime-wash:#F1F4EA;
  --signal:#C93A22;--ok:#1F7A45;--ok-bg:#E7F4EC;--warn:#8A5A00;--warn-bg:#FBF0DC;
  --agent:#2C4BD6;--agent-bg:#ECEFFD;
  --display:'Inter',ui-sans-serif,system-ui,sans-serif;
  --sans:'Plus Jakarta Sans',ui-sans-serif,system-ui,sans-serif;
  --serif:'Instrument Serif',Georgia,serif;
  --mono:'Geist Mono',ui-monospace,monospace;
}
.stApp{background:var(--page);color:var(--ink)}
.block-container{max-width:1120px;padding-top:2.5rem;padding-bottom:5rem}
#MainMenu,footer,[data-testid="stStatusWidget"],.stDeployButton,[data-testid="stAppDeployButton"]{display:none!important}
header[data-testid="stHeader"]{background:rgba(255,255,255,.85);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}

h1,h2,h3{font-family:var(--display)!important;font-weight:700!important;letter-spacing:-.045em;color:var(--ink)}
h1 em,h2 em,h3 em{font-family:var(--serif)!important;font-style:italic;font-weight:400;letter-spacing:-.01em}

/* Buttons: lime pill says yes, graphite pill is the secondary action */
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{
  min-height:48px;border-radius:999px;font-family:var(--sans);font-weight:700;font-size:15px;
  border:1px solid var(--line);background:var(--page);color:var(--ink);padding:0 22px;transition:background .15s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--field);background:var(--sand);color:var(--ink)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{
  min-height:56px;font-size:17px;background:var(--lime);color:var(--black);border:none}
.stButton>button[kind="primary"]:hover{background:var(--lime-hover);color:var(--black)}
.stButton>button[kind="primary"]:disabled{background:var(--sand-2);color:var(--faint)}
.stButton>button[kind="tertiary"]{background:var(--graphite);color:#fff;border:none}
.stButton>button[kind="tertiary"]:hover{background:#000;color:#fff}
.stButton>button:focus-visible{outline:3px solid var(--ink);outline-offset:2px}

/* Inputs */
.stTextArea textarea,.stTextInput input{background:var(--page);font-size:15px;color:var(--ink)}
[data-baseweb="textarea"],[data-baseweb="input"]{border-radius:14px!important;border-color:var(--field)!important;background:var(--page)!important}
[data-testid="stFileUploaderDropzone"]{background:var(--plate);border:1px dashed var(--field);border-radius:16px}
label p{font-weight:600;color:var(--ink)}

/* Cards: st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"]{background:var(--page);border-color:var(--line)!important;border-radius:24px}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{height:44px;padding:0 14px;font-size:15px;color:var(--meta)}
.stTabs [aria-selected="true"]{color:var(--ink);font-weight:700}
.stTabs [data-baseweb="tab-highlight"]{background:var(--ink);height:2px}

/* Expanders */
[data-testid="stExpander"] details{background:var(--page);border:1px solid var(--line);border-radius:16px}

/* ---------- custom components ---------- */
.rm-eyebrow{font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;color:var(--meta);text-transform:uppercase}
.rm-badge{display:inline-flex;align-items:center;gap:10px;height:40px;padding:0 18px;border:1px solid var(--line);
  border-radius:999px;background:var(--page);font-size:15px;color:var(--meta)}
.rm-badge .dot{width:10px;height:10px;border-radius:999px;border:2px solid var(--ink);background:var(--lime)}
.rm-hero{display:flex;flex-direction:column;align-items:center;text-align:center;gap:22px;padding:32px 0 12px}
.rm-hero h1{margin:0;max-width:820px;font-size:clamp(40px,5.6vw,68px)!important;line-height:1.02!important;letter-spacing:-.05em}
.rm-hero h1 .g1{color:var(--ghost)}.rm-hero h1 .g2{color:var(--faint)}
.rm-hero p{margin:0;max-width:540px;font-size:20px;line-height:1.5;color:var(--faint)}
.rm-ticks{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 22px;margin:0;padding:0;list-style:none;font-size:14px;color:var(--meta)}
.rm-ticks li{display:inline-flex;align-items:center;gap:6px}
.rm-page-title h1{margin:8px 0 6px;font-size:clamp(32px,4vw,48px)!important;line-height:1.05!important}
.rm-page-title p{margin:0;font-size:17px;color:var(--meta)}
.rm-label{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--meta);text-transform:uppercase}
.rm-num{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;flex:none;border-radius:999px;
  background:var(--ink);color:#fff;font-size:12.5px;font-weight:700;font-family:var(--sans)}
.rm-tag{display:inline-flex;align-items:center;height:30px;padding:0 10px;background:var(--signal);color:#fff;
  font-size:14px;font-weight:600;border-radius:3px;align-self:flex-start;white-space:nowrap}

.rm-tile{background:var(--page);border:1px solid var(--line);border-radius:24px;padding:22px;display:flex;flex-direction:column;gap:10px;height:100%}
.rm-tile .big{font-family:var(--display);font-size:52px;line-height:1;font-weight:800;letter-spacing:-.05em}
.rm-tile .unit{font-size:15px;color:var(--meta)}
.rm-tile .sub{font-size:14px;color:var(--body)}
.rm-step{background:var(--sand);border-radius:24px;padding:24px;display:flex;flex-direction:column;gap:12px;height:100%}
.rm-step .t{font-family:var(--display);font-size:22px;font-weight:700;letter-spacing:-.03em;color:var(--ink)}
.rm-step .b{font-size:15.5px;color:var(--body)}
.rm-bar{height:8px;border-radius:999px;background:var(--sand-2);overflow:hidden}
.rm-bar>span{display:block;height:8px;border-radius:999px;background:var(--lime-deep)}
.rm-dark{background:var(--graphite);color:#fff;border-radius:24px;padding:22px;display:flex;flex-direction:column;gap:10px;height:100%}
.rm-dark .rm-label{color:var(--g-body)}
.rm-dark h3{color:#fff;margin:0;font-size:22px;letter-spacing:-.03em}
.rm-dark p{margin:0;color:var(--g-body);font-size:15px}
.rm-dark ol{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:12px;font-size:15px;color:var(--g-tag)}
.rm-dark ol li{display:flex;gap:10px;align-items:flex-start}
.rm-dark .rm-num{background:var(--lime);color:var(--black)}
.rm-dark code{background:var(--graphite-card);color:var(--lime);padding:1px 6px;border-radius:6px;font-family:var(--mono);font-size:13px}

.rm-pill{display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 10px;border-radius:999px;font-size:12.5px;font-weight:600;white-space:nowrap;border:1px solid var(--line);background:var(--page);color:var(--ink)}
.rm-pill.good{background:var(--ok-bg);border-color:transparent;color:var(--ok)}
.rm-pill.part{background:var(--warn-bg);border-color:transparent;color:var(--warn)}
.rm-pill.miss{background:#FBE9E5;border-color:transparent;color:var(--signal)}
.rm-pill.mono{font-family:var(--mono);font-size:11.5px;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--meta)}
.rm-chips{display:flex;flex-wrap:wrap;gap:8px}

.rm-row{display:grid;grid-template-columns:44px minmax(0,1fr) auto;gap:6px 14px;padding:16px 4px;border-top:1px solid var(--line);align-items:start}
.rm-row:first-child{border-top:none}
.rm-row .id{font-family:var(--mono);font-size:12px;color:var(--faint);padding-top:3px}
.rm-row .req{font-weight:700;font-size:16px}
.rm-row .pills{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.rm-row .ev{grid-column:2 / 4;font-family:var(--serif);font-style:italic;font-size:18px;line-height:1.35;color:var(--ink)}
.rm-row .note{grid-column:2 / 4;font-size:14px;color:var(--meta)}
@media (max-width:640px){.rm-row{grid-template-columns:36px minmax(0,1fr)}.rm-row .pills{grid-column:2;justify-content:flex-start}}

.rm-quote{font-family:var(--serif);font-style:italic;font-size:19px;line-height:1.4;color:var(--ink);background:var(--sand);border-radius:14px;padding:12px 16px}
.rm-before{font-size:15px;color:var(--faint);text-decoration:line-through;text-decoration-color:var(--ghost)}
.rm-flag{font-size:14px;background:var(--warn-bg);color:#5F3D00;border-radius:12px;padding:8px 12px}
.rm-mark{font-family:var(--mono);font-style:normal;font-size:12px;background:var(--lime);color:var(--black);padding:1px 6px;border-radius:6px}
.rm-action{display:flex;gap:14px;padding:16px 0;border-top:1px solid var(--line)}
.rm-action:first-child{border-top:none}
.rm-action .t{font-weight:700;font-size:16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.rm-action .d{font-size:15px;color:var(--body);margin-top:2px}
.rm-check{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid var(--line);font-size:15px}
.rm-check:first-child{border-top:none}
.rm-check .d{color:var(--meta);font-size:14px}
.rm-muted{color:var(--meta);font-size:14px}
[data-testid="stHeaderActionElements"]{display:none}
</style>
""".replace("__FONTS__", FONTS_URL)


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
