import streamlit as st
from utils.ui import setup, hero, card, note

setup("Home")
hero("AgriLab Hub",
     "Forecasting, calculations, literature search and laboratory references for agricultural "
     "and environmental research, in one place. Free for students and researchers.")

MODULES = [
    ("Forecasting Tools", "Upload your data, pick a model and get validated results, graphs and an Excel report. "
     "Nine models are ready today.", "ready", "pages/1_Forecasting_Tools.py"),
    ("Scientific Calculator", "Soil, fertilizer, laboratory and irrigation calculations. Every result shows its "
     "formula, steps and assumptions.", "ready", "2_Scientific_Calculator.py"),
    ("Research Library", "Search millions of papers through OpenAlex and Crossref, or jump to Google Scholar, "
     "ResearchGate and other sources.", "ready", "3_Research_Library.py"),
    ("Laboratory Analysis", "Soil and water procedures with chemicals, equipment, steps and quality control, "
     "each checked against its published method.", "soon", "4_Laboratory_Analysis.py"),
    ("Agricultural Tools", "Irrigation, fertilizer, machinery, climate, GIS and post-harvest tools for "
     "agricultural engineering.", "soon", "5_Agricultural_Tools.py"),
]

for row in (MODULES[:3], MODULES[3:]):
    cols = st.columns(3)
    for col, (title, body, status, path) in zip(cols, row):
        with col:
            st.markdown(card(title, body, status), unsafe_allow_html=True)
            st.page_link(path, label=f"Open {title}")

with cols[2]:
    note("<b>How your results are produced.</b> Models are scored on data they did not train on. "
         "The platform never adjusts results to raise R². Uploaded files are used only in your session "
         "and are not saved by this app.")
