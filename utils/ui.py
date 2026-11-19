"""Shared look and feel for AgriLab Hub."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: #17372A; letter-spacing: -0.01em; }
.block-container { padding-top: 2rem; max-width: 1100px; }
.fl-hero { background: #17372A; padding: 2rem 2rem 1.8rem 2rem; border-radius: 6px; margin-bottom: 1.5rem; }
.fl-hero h1 { color: #F3F7F5 !important; margin: 0 0 .4rem 0; font-size: 2.3rem; }
.fl-hero p { color: #C9DDD3; margin: 0; font-size: 1.05rem; max-width: 650px; line-height: 1.5; }
.fl-card { border: 1px solid #D5E2DB; border-left: 5px solid #1B7F79; padding: 1rem 1.1rem; border-radius: 4px; background: #FFFFFF; min-height: 165px; margin-bottom: .4rem; }
.fl-card h3 { margin: 0 0 .3rem 0; font-size: 1.2rem; }
.fl-card p { margin: .4rem 0 0 0; color: #3B4A42; font-size: .93rem; line-height: 1.45; }
.fl-badge { display: inline-block; font-size: .75rem; font-weight: 600; padding: .1rem .5rem; border-radius: 3px; }
.fl-ready { background: #DDF0E6; color: #14543A; }
.fl-soon { background: #F6E7C8; color: #7A5210; }
.fl-note { background: #F3F7F5; border-left: 4px solid #1B7F79; padding: .8rem 1rem; border-radius: 4px; font-size: .92rem; color: #2B3A32; }
@media (max-width: 640px) { .fl-hero h1 { font-size: 1.7rem; } .fl-card { min-height: 0; } }
</style>
"""


def setup(title: str, icon: str = "🌿"):
    st.set_page_config(page_title=f"{title} | AgriLab Hub", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(f'<div class="fl-hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def card(title: str, body: str, status=None) -> str:
    badge = ""
    if status == "ready":
        badge = '<span class="fl-badge fl-ready">Ready</span>'
    elif status == "soon":
        badge = '<span class="fl-badge fl-soon">Coming soon</span>'
    return f'<div class="fl-card"><h3>{title}</h3>{badge}<p>{body}</p></div>'


def note(text: str):
    st.markdown(f'<div class="fl-note">{text}</div>', unsafe_allow_html=True)


def coming_soon(message: str, sections: dict, per_row: int = 3):
    note(message)
    st.write("")
    items = list(sections.items())
    for i in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for col, (name, lines) in zip(cols, items[i:i + per_row]):
            with col:
                st.markdown(f"**{name}**")
                for line in lines:
                    st.markdown(f"- {line}")
