"""
pages/home.py
---------------
Landing / Home page for the AI Digital Twin Streamlit application.
Gives an overview of the project, tech stack, and workflow, plus
clickable navigation cards that take the user straight to each page.
"""

import streamlit as st


def _go_to(page_name: str):
    """Callback: switches the active page by updating the app-wide
    "active_page" session_state key (see app.py's render_topbar / main).
    Callbacks run BEFORE the script reruns and widgets are re-instantiated,
    so it's safe to mutate this key here (doing it directly inside the
    button's `if` block would raise a "cannot be modified after the widget
    is instantiated" error for widget-bound keys). "active_page" is a plain
    state key, not a widget key, so it can be set freely and is picked up
    by main()'s routing on the next run."""
    st.session_state["active_page"] = page_name


def _nav_card(col, *, step, title, desc, accent, target_page, button_label):
    """Renders one clickable navigation card inside the given column."""
    with col:
        st.markdown(
            f"""
            <div class="nav-card" style="--card-accent:{accent};">
                <div class="nav-card-step">{step}</div>
                <div class="nav-card-title">{title}</div>
                <div class="nav-card-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            button_label,
            key=f"card_btn_{target_page}",
            use_container_width=True,
            on_click=_go_to,
            args=(target_page,),
        )


def _feature_card(col, *, label, title, desc, accent):
    """Renders one static feature card (no button) inside the given column."""
    with col:
        st.markdown(
            f"""
            <div class="feature-card" style="--feature-accent:{accent};">
                <div class="feature-label">{label}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _back_to_splash():
    """Callback: returns the user to the splash (first) page."""
    st.session_state["app_stage"] = "splash"


def render_home():
    """Renders the Home page content."""
    try:
        top_left, top_right = st.columns([5, 1.4])
        with top_left:
            st.markdown(
                "<h2 style='font-weight:800; margin-bottom:0;'>Home</h2>",
                unsafe_allow_html=True,
            )
        with top_right:
            st.button(
                "← Welcome Screen",
                use_container_width=True,
                on_click=_back_to_splash,
            )

        st.markdown("---")
        st.markdown("### How to use this app")
        st.caption("Select a card below to jump straight to that step.")

        row1_col1, row1_col2 = st.columns(2)
        _nav_card(
            row1_col1,
            step="OPTION 1",
            title="CSV Upload",
            desc="Analyze a batch of patients at once from a CSV file.",
            accent="#0b7285",
            target_page="CSV Upload",
            button_label="Go to CSV Upload",
        )
        _nav_card(
            row1_col2,
            step="OPTION 2",
            title="Manual Entry",
            desc="Type in a single patient's details by hand.",
            accent="#7048e8",
            target_page="Manual Entry",
            button_label="Go to Manual Entry",
        )

        row2_col1, row2_col2 = st.columns(2)
        _nav_card(
            row2_col1,
            step="OPTION 3",
            title="Medical Report Upload",
            desc="Upload a photo or scan of a lab report and let OCR "
                 "extract the values automatically.",
            accent="#e8590c",
            target_page="Medical Report Upload",
            button_label="Go to Report Upload",
        )
        _nav_card(
            row2_col2,
            step="STEP 4 - FINAL",
            title="Dashboard",
            desc="View the generated Digital Twin, risk predictions, "
                 "and charts after using any option above.",
            accent="#2f9e44",
            target_page="Dashboard",
            button_label="Go to Dashboard",
        )

        row3_col1, _row3_col2 = st.columns(2)
        _nav_card(
            row3_col1,
            step="SAVED",
            title="History",
            desc="Reopen earlier results, the images you uploaded or captured, "
                 "and the reports you downloaded.",
            accent="#1971c2",
            target_page="History",
            button_label="Go to History",
        )

    except Exception as e:
        st.error(f"Error rendering Home page: {e}")
