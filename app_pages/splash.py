"""
app_pages/splash.py
--------------------
First screen the user sees when the app loads. A full-bleed, dark navy
hero screen with white text, the project title/subtitle, a glowing hero
illustration, and a single button that takes the user straight into the
actual app (Home).
"""

import base64
import os
import streamlit as st

_ASSET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "splash_hero.png",
)


def _enter_app():
    """Callback: advances past the splash screen into the real app."""
    st.session_state["app_stage"] = "app"


def _image_data_uri() -> str:
    """Reads the hero PNG and returns it as a base64 data URI so it can be
    embedded directly inside the hero <div>, letting CSS control its size,
    drop-shadow, and float animation precisely."""
    if not os.path.exists(_ASSET_PATH):
        return ""
    with open(_ASSET_PATH, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def render_splash():
    """Renders the full-bleed, dark splash / landing page."""
    try:
        # Scoped styling for the splash screen only — this block is simply
        # never emitted once app_stage moves past "splash", so the dark
        # theme can't leak into the rest of the (light-themed) app.
        st.markdown(
            """
            <style>
                /* Full-bleed cinematic blue background covering the whole page */
                .stApp {
                    background:
                        radial-gradient(circle at 50% 0%, rgba(59,130,246,0.35) 0%, transparent 55%),
                        radial-gradient(circle at 15% 85%, rgba(37,99,235,0.25) 0%, transparent 50%),
                        radial-gradient(circle at 85% 75%, rgba(14,165,233,0.22) 0%, transparent 50%),
                        linear-gradient(160deg, #020c1a 0%, #051c3a 40%, #0a3566 75%, #0e4a8f 100%) !important;
                    min-height: 100vh;
                }
                header[data-testid="stHeader"] {
                    background: transparent !important;
                }
                .block-container {
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                    max-width: 100% !important;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .splash-eyebrow {
                    display: inline-block;
                    background: rgba(255,255,255,0.08);
                    border: 1px solid rgba(255,255,255,0.22);
                    color: #eaf6f8 !important;
                    font-size: 0.72rem;
                    font-weight: 700;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    padding: 6px 18px;
                    border-radius: 20px;
                    margin-bottom: 1.4rem;
                }

                .splash-title {
                    font-size: clamp(2rem, 3.6vw, 2.9rem);
                    font-weight: 800;
                    line-height: 1.2;
                    letter-spacing: -0.015em;
                    margin: 0 auto 0.8rem auto;
                    max-width: 800px;
                    color: #ffffff !important;
                }

                .splash-subtitle {
                    font-size: 1.1rem;
                    font-weight: 500;
                    color: #b9d2de !important;
                    max-width: 560px;
                    margin: 0 auto 2.2rem auto;
                }

                div[data-testid="stButton"] button,
                div.stButton button {
                    background: linear-gradient(135deg, #5eead4 0%, #7048e8 100%);
                    color: #05202e;
                    font-size: 1.05rem;
                    font-weight: 800;
                    padding: 0.85rem 2.6rem;
                    border-radius: 999px;
                    border: none;
                    box-shadow: 0 12px 28px rgba(0,0,0,0.35);
                    transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
                    width: 100%;
                }
                div[data-testid="stButton"] button:hover,
                div.stButton button:hover {
                    transform: translateY(-2px);
                    filter: brightness(1.06);
                    box-shadow: 0 16px 34px rgba(0,0,0,0.45);
                }
                div[data-testid="stButton"] button p,
                div.stButton button p {
                    color: #05202e !important;
                    font-size: 1.05rem !important;
                    font-weight: 800 !important;
                }

            </style>
            """,
            unsafe_allow_html=True,
        )

        left, center, right = st.columns([1, 3, 1])
        with center:
            st.markdown(
                f"""
                <div style="text-align:center; padding: 2.5rem 1rem;">
                    <div class="splash-eyebrow">AI-Powered Healthcare</div>
                    <div class="splash-title">
                        Digital Twin for Personalized mRNA Vaccine Simulation
                    </div>
                    <div class="splash-subtitle">
                        Using Machine Learning and Medical Report Analysis
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_left, btn_mid, btn_right = st.columns([1, 1, 1])
            with btn_mid:
                st.button("Get Started →", on_click=_enter_app, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering splash page: {e}")
