"""
app.py
--------
Main entry point for the AI Digital Twin for Personalized mRNA Vaccine
Simulation Using Machine Learning and Medical Report Analysis.

Run with:
    streamlit run app.py

This file sets up the page config, professional healthcare-themed CSS,
sidebar navigation, and dispatches to the correct page module.
"""

import os
import sys

# Make sure this script's own directory is importable regardless of the
# working directory the app is launched from (defensive fix for
# environments where sys.path[0] isn't set up the way Streamlit expects).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Import each page's render function.
# NOTE: this package is deliberately named "app_pages" and NOT "pages" —
# Streamlit auto-treats any folder literally named "pages" next to the
# entrypoint script as its own native multipage-app directory, which can
# collide with a normal Python package import of the same name and cause
# "ModuleNotFoundError: No module named 'pages.xxx'". Keep it as
# app_pages to avoid that collision.
from app_pages.splash import render_splash
from app_pages.home import render_home
from app_pages.csv_upload import render_csv_upload
from app_pages.manual_entry import render_manual_entry
from app_pages.medical_report_upload import render_medical_report_upload
from app_pages.dashboard import render_dashboard
from app_pages.history import render_history


def configure_page():
    """Sets Streamlit page config and injects custom CSS for a
    professional healthcare theme."""
    try:
        st.set_page_config(
            page_title="Digital Twin - mRNA Vaccine Simulation",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Custom CSS for a clean, professional healthcare look
        st.markdown(
            """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

                html, body, [class*="css"] {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                }

                /* ---------- Palette ----------
                   Ink:      #0b3d59  (deep navy)
                   Primary:  #0b7285  (teal)
                   Primary+: #095a68  (hover)
                   Surface:  #ffffff
                   Backdrop: #f3f8fb
                   Border:   #e0e9ee
                   Muted:    #5b7280
                */

                /* Main app background */
                .stApp {
                    background: linear-gradient(180deg, #f3f8fb 0%, #eef4f8 100%);
                }

                /* Tighten default top padding a touch for a more app-like feel */
                .block-container {
                    padding-top: 2.2rem;
                    padding-bottom: 3rem;
                    max-width: 1200px;
                }

                /* ---------- Typography ---------- */
                h1 {
                    color: #0b3d59;
                    font-weight: 800;
                    letter-spacing: -0.01em;
                }
                h2, h3 {
                    color: #0b3d59;
                    font-weight: 700;
                }
                h4, h5 {
                    color: #0b3d59;
                    font-weight: 600;
                }
                .stApp p, .stApp li, .stMarkdown {
                    color: #33475a;
                }
                hr {
                    border: none;
                    border-top: 1px solid #e0e9ee;
                    margin: 1.6rem 0;
                }

                /* ---------- Metric cards ---------- */
                div[data-testid="stMetric"] {
                    background-color: #ffffff;
                    border: 1px solid #e0e9ee;
                    border-radius: 12px;
                    padding: 16px 14px;
                    box-shadow: 0 1px 2px rgba(11,61,89,0.06);
                    transition: box-shadow 0.15s ease;
                }
                div[data-testid="stMetric"]:hover {
                    box-shadow: 0 4px 12px rgba(11,61,89,0.10);
                }
                div[data-testid="stMetricLabel"] {
                    color: #5b7280 !important;
                    font-weight: 600;
                }
                div[data-testid="stMetricValue"] {
                    color: #0b3d59 !important;
                    font-weight: 800;
                }

                /* ---------- Buttons ---------- */
                .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
                    background: linear-gradient(135deg, #0b7285 0%, #095a68 100%);
                    color: white;
                    border-radius: 8px;
                    border: none;
                    font-weight: 600;
                    padding: 0.55rem 1.1rem;
                    box-shadow: 0 1px 3px rgba(9,90,104,0.25);
                    transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
                }
                .stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {
                    filter: brightness(1.08);
                    box-shadow: 0 4px 10px rgba(9,90,104,0.30);
                    color: white;
                }
                .stButton>button:active, .stFormSubmitButton>button:active {
                    transform: translateY(1px);
                }
                /* Ensure button label text (rendered as an inner <p>) stays white,
                   overriding the broader ".stApp p" muted-text rule below */
                .stButton>button p, .stDownloadButton>button p, .stFormSubmitButton>button p,
                .stButton>button div, .stDownloadButton>button div, .stFormSubmitButton>button div {
                    color: #ffffff !important;
                    font-weight: 600;
                }

                /* ---------- Inputs & forms ---------- */
                .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
                    border-radius: 8px !important;
                    border-color: #d6e4ea !important;
                }
                .stTextInput input:focus, .stNumberInput input:focus {
                    border-color: #0b7285 !important;
                    box-shadow: 0 0 0 1px #0b7285 !important;
                }
                div[data-testid="stForm"] {
                    background-color: #ffffff;
                    border: 1px solid #e0e9ee;
                    border-radius: 14px;
                    padding: 1.6rem 1.6rem 1rem 1.6rem;
                    box-shadow: 0 1px 4px rgba(11,61,89,0.05);
                }

                /* ---------- File uploader ---------- */
                [data-testid="stFileUploaderDropzone"] {
                    background-color: #f7fbfc;
                    border: 1.5px dashed #a9c6d3;
                    border-radius: 12px;
                }

                /* ---------- Alerts (info/success/warning/error) ---------- */
                div[data-testid="stAlert"] {
                    border-radius: 10px;
                    border: 1px solid transparent;
                }

                /* ---------- DataFrames / tables ---------- */
                div[data-testid="stDataFrame"] {
                    border: 1px solid #e0e9ee;
                    border-radius: 10px;
                    overflow: hidden;
                }

                /* ---------- Expanders ---------- */
                details[class*="streamlit-expander"], div[data-testid="stExpander"] {
                    border: 1px solid #e0e9ee !important;
                    border-radius: 10px !important;
                    background-color: #ffffff;
                }

                /* ---------- Tabs / horizontal radio pills (Dashboard view switch) ---------- */
                div[role="radiogroup"][aria-orientation="horizontal"] label {
                    background-color: #ffffff;
                    border: 1px solid #d6e4ea;
                    border-radius: 20px;
                    padding: 6px 16px;
                    margin-right: 6px;
                }

                /* ---------- Progress bars ---------- */
                div[data-testid="stProgress"] > div > div {
                    background-color: #0b7285;
                    border-radius: 6px;
                }

                /* ---------- Home page navigation cards ---------- */
                .nav-card {
                    background-color: #ffffff;
                    border: 1px solid #e0e9ee;
                    border-top: 4px solid var(--card-accent, #0b7285);
                    border-radius: 14px;
                    padding: 22px 20px 16px 20px;
                    height: 100%;
                    box-shadow: 0 1px 4px rgba(11,61,89,0.06);
                    transition: transform 0.15s ease, box-shadow 0.15s ease;
                }
                .nav-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 10px 22px rgba(11,61,89,0.16);
                }
                .nav-card .nav-card-title {
                    font-size: 1.08rem;
                    font-weight: 700;
                    color: #0b3d59;
                    margin-bottom: 6px;
                    margin-top: 4px;
                }
                .nav-card .nav-card-desc {
                    font-size: 0.89rem;
                    color: #5b7280;
                    line-height: 1.5;
                    min-height: 60px;
                }
                .nav-card .nav-card-step {
                    display: inline-block;
                    background-color: #e7f3f6;
                    color: #0b7285;
                    font-size: 0.72rem;
                    font-weight: 700;
                    letter-spacing: 0.03em;
                    border-radius: 20px;
                    padding: 3px 11px;
                    margin-bottom: 10px;
                }

                /* ---------- Home page "what this app does" feature grid ---------- */
                .feature-card {
                    background-color: #ffffff;
                    border: 1px solid #e0e9ee;
                    border-left: 4px solid var(--feature-accent, #0b7285);
                    border-radius: 12px;
                    padding: 18px 20px;
                    height: 100%;
                    box-shadow: 0 1px 3px rgba(11,61,89,0.05);
                    transition: box-shadow 0.15s ease;
                }
                .feature-card:hover {
                    box-shadow: 0 4px 14px rgba(11,61,89,0.10);
                }
                .feature-card .feature-label {
                    display: inline-block;
                    color: var(--feature-accent, #0b7285);
                    font-size: 0.7rem;
                    font-weight: 700;
                    letter-spacing: 0.07em;
                    text-transform: uppercase;
                    margin-bottom: 6px;
                }
                .feature-card .feature-title {
                    font-size: 1rem;
                    font-weight: 700;
                    color: #0b3d59;
                    margin-bottom: 5px;
                }
                .feature-card .feature-desc {
                    font-size: 0.86rem;
                    color: #5b7280;
                    line-height: 1.5;
                }

            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Error configuring page: {e}")


# The full set of pages the app can route to. All of them (including
# Dashboard) are reached via the cards on the Home page; the top bar only
# offers a way back Home plus Log Out.
ALL_PAGES = [
    "Home",
    "CSV Upload",
    "Manual Entry",
    "Medical Report Upload",
    "Dashboard",
    "History",
]


def render_topbar() -> str:
    """Renders a minimal top bar (no sidebar) and returns the currently
    active page name.

    st.session_state["active_page"] is the single source of truth for
    routing. The Home page's nav cards set it directly via their own
    callback (see app_pages/home.py's _go_to). This bar just offers a way
    back to Home so users are never stuck on a sub-page.
    """
    try:
        st.session_state.setdefault("active_page", "Home")

        bar_col1, bar_col2 = st.columns([7, 1])
        with bar_col1:
            st.markdown("##### Digital Twin — mRNA Vaccine Simulation Platform")
        with bar_col2:
            if st.session_state["active_page"] != "Home":
                if st.button("Home", use_container_width=True):
                    st.session_state["active_page"] = "Home"
                    st.rerun()
        st.markdown("---")

        return st.session_state["active_page"]
    except Exception as e:
        st.error(f"Error rendering top bar: {e}")
        return "Home"


def main():
    """Main application dispatcher."""
    try:
        configure_page()

        # No sidebar anywhere in the app — navigation happens via the
        # splash screen's button, the Home page's cards, and the top
        # bar's Home button.
        st.markdown(
            "<style>section[data-testid='stSidebar'] {display: none;}</style>",
            unsafe_allow_html=True,
        )

        # ---- Splash gate ----
        # The very first thing a user sees is the splash/landing page.
        # Clicking "Get Started" there advances app_stage to "app", which
        # goes straight into the app (no login required).
        st.session_state.setdefault("app_stage", "splash")
        if st.session_state["app_stage"] == "splash":
            render_splash()
            return

        selected_page = render_topbar()

        # Widgets drop their value when they aren't drawn on a run (e.g. the
        # language radio while the user is on the Home page). Re-assigning the
        # plain key keeps the chosen result language across page changes.
        st.session_state["result_lang"] = st.session_state.get("result_lang", "en")

        # ---- Clear stale per-page results on fresh navigation ----
        # Each of these pages keeps its last generated result in
        # session_state so it survives reruns caused by interacting with
        # the result itself (e.g. a PDF download button). But that same
        # persistence means if the user navigates away and back to the
        # SAME page, the old result would otherwise still show up before
        # they've generated a new one. Detect an actual page switch (not
        # just any rerun of the current page) and clear the arriving
        # page's stored result in that case only.
        PAGE_RESULT_KEYS = {
            "CSV Upload": ["csv_upload_batch_twins", "csv_upload_file_id"],
            "Manual Entry": ["manual_entry_twin", "manual_entry_record_id"],
            "Medical Report Upload": ["report_upload_twin", "report_upload_file_id", "report_upload_record_id"],
        }
        if st.session_state.get("_prev_active_page") != selected_page:
            for key in PAGE_RESULT_KEYS.get(selected_page, []):
                st.session_state.pop(key, None)
            st.session_state["_prev_active_page"] = selected_page

        # Route to the correct page render function based on the active page
        if selected_page == "Home":
            render_home()
        elif selected_page == "CSV Upload":
            render_csv_upload()
        elif selected_page == "Manual Entry":
            render_manual_entry()
        elif selected_page == "Medical Report Upload":
            render_medical_report_upload()
        elif selected_page == "Dashboard":
            render_dashboard()
        elif selected_page == "History":
            render_history()
        else:
            render_home()

    except Exception as e:
        st.error(f"A critical error occurred while running the application: {e}")


if __name__ == "__main__":
    main()