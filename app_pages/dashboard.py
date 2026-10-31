"""
pages/dashboard.py
---------------------
The main results Dashboard. Displays the Digital Twin card, prediction
percentages, recommendation, risk gauges, and Plotly charts for either
the current single patient (from Manual Entry / Medical Report Upload)
or the full batch (from CSV Upload).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.report_generator import generate_pdf_report
from utils.history import log_download
from utils.i18n import (
    LANGUAGES, DEFAULT_LANG, t, tr_risk, tr_gender, tr_recommendation,
    tr_precautions, tr_rsv_factor,
)


RISK_COLORS = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"}


def _risk_gauge(title: str, predicted_class: str, probability: float, lang: str = DEFAULT_LANG):
    """Builds a Plotly gauge chart for a single risk prediction."""
    try:
        color = RISK_COLORS.get(predicted_class, "#3498db")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": "%"},
            title={"text": f"{title}<br><span style='font-size:0.8em;color:{color}'>{tr_risk(predicted_class, lang)} {t('risk_word', lang)}</span>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 33], "color": "#eafaf1"},
                    {"range": [33, 66], "color": "#fef5e7"},
                    {"range": [66, 100], "color": "#fdedec"},
                ],
            },
        ))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20))
        return fig
    except Exception as e:
        st.error(f"Error building gauge chart: {e}")
        return None


def _render_rsv_risk_card(rsv_risk: dict, lang: str = DEFAULT_LANG):
    """Renders the RSV (Respiratory Syncytial Virus) risk screening card."""
    try:
        if not rsv_risk:
            return
        risk_level = rsv_risk.get("risk_level", "Low")
        recommendation = rsv_risk.get("recommendation", "Low")
        score = rsv_risk.get("score", 0)
        max_score = rsv_risk.get("max_score", 8)
        color = RISK_COLORS.get(risk_level, "#3498db")

        st.markdown(f"#### {t('rsv_title', lang)}")
        st.markdown(
            f"""
            <div style="border:2px solid {color}; border-radius:12px; padding:16px; background-color:#fafafa;">
                <p style="margin:0;"><b>{t('rsv_risk_level', lang)}:</b>
                    <span style="color:{color}; font-weight:bold;">{tr_risk(risk_level, lang)}</span>
                </p>
                <p style="margin:6px 0 0 0;"><b>{t('result', lang)}:</b>
                    <span style="font-weight:bold;">{tr_recommendation(recommendation, lang)}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Precautions (Medium risk only) ----
        precautions = rsv_risk.get("precautions") or []
        if risk_level == "Medium" and precautions:
            st.markdown(f"**{t('precautions_title', lang)}:**")
            for step in tr_precautions(precautions, lang):
                st.markdown(f"- {step}")

        st.caption(f"{t('risk_score', lang)}: {score} / {max_score} ({t('based_on', lang)})")
        with st.expander(t("view_breakdown", lang)):
            breakdown = rsv_risk.get("breakdown", {})
            for factor, points in breakdown.items():
                st.write(f"{tr_rsv_factor(factor, lang)}: {points} / 2 {t('points', lang)}")
    except Exception as e:
        st.error(f"Error rendering RSV risk card: {e}")


def language_selector() -> str:
    """Shows the English / Hindi / Kannada picker and returns the code.
    The choice is kept in st.session_state["result_lang"] so it follows the
    user between pages (see app.py, which preserves it across navigation)."""
    labels = list(LANGUAGES.keys())
    codes = list(LANGUAGES.values())
    current = st.session_state.get("result_lang", DEFAULT_LANG)
    index = codes.index(current) if current in codes else 0
    choice = st.radio(
        "Result language / परिणाम की भाषा / ಫಲಿತಾಂಶದ ಭಾಷೆ",
        labels, index=index, horizontal=True, key="result_lang_radio",
    )
    code = LANGUAGES[choice]
    st.session_state["result_lang"] = code
    return code


def _log_download_cb(record_id, lang, pdf_bytes):
    """download_button callback: saves a copy of the downloaded PDF in
    reports/ and logs it on the history record."""
    log_download(record_id, lang, pdf_bytes)


def render_digital_twin_card(twin: dict, record_id: str = None):
    """Renders the Digital Twin summary card + gauges + charts for one
    patient, in the language chosen with the selector at the top. Public so
    other pages (Medical Report Upload, Manual Entry, History) can render
    the result inline. If record_id is given, downloaded PDFs are saved to
    that history record."""
    try:
        details = twin["patient_details"]
        allergy = twin["allergy_risk"]
        side_effect = twin["side_effect_risk"]
        overall_risk = twin["overall_risk_level"]
        recommendation = twin["recommendation"]
        rsv_risk = twin.get("rsv_risk")

        lang = language_selector()

        # ---- Digital Twin Card ----
        st.markdown(f"### {t('digital_twin_profile', lang)}")
        card_color = RISK_COLORS.get(overall_risk, "#3498db")
        st.markdown(
            f"""
            <div style="border:2px solid {card_color}; border-radius:12px; padding:20px; background-color:#fafafa;">
                <h4 style="margin-top:0;">{details.get('PatientName', 'Unknown')}</h4>
                <p><b>{t('age', lang)}:</b> {details.get('Age')} &nbsp;|&nbsp; <b>{t('gender', lang)}:</b> {tr_gender(details.get('Gender'), lang)}</p>
                <p><b>{t('alt', lang)}:</b> {details.get('ALT')} U/L &nbsp;|&nbsp; <b>{t('ast', lang)}:</b> {details.get('AST')} U/L</p>
                <p><b>{t('creatinine', lang)}:</b> {details.get('Creatinine')} mg/dL &nbsp;|&nbsp; <b>{t('crp', lang)}:</b> {details.get('CRP')} mg/L</p>
                <p><b>{t('overall_risk_level', lang)}:</b> <span style="color:{card_color}; font-weight:bold;">{tr_risk(overall_risk, lang)}</span></p>
                <p><b>{t('recommendation', lang)}:</b> <span style="font-weight:bold;">{tr_recommendation(recommendation, lang)}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("&nbsp;")

        # ---- Download Report button (PDF in the selected language) ----
        patient_name = details.get("PatientName") or "patient"
        safe_name = "".join(c if c.isalnum() else "_" for c in str(patient_name))
        try:
            pdf_bytes = generate_pdf_report(twin, lang)
            st.download_button(
                label=t("download_report", lang),
                data=pdf_bytes,
                file_name=f"{safe_name}_digital_twin_report_{lang}.pdf",
                mime="application/pdf",
                key=f"download_report_{safe_name}_{lang}_{record_id or 'unsaved'}",
                on_click=_log_download_cb,
                args=(record_id, lang, pdf_bytes),
            )
        except Exception as e:
            st.error(f"Error generating downloadable report: {e}")

        st.markdown("&nbsp;")

        # ---- RSV Risk Screening card ----
        _render_rsv_risk_card(rsv_risk, lang)

        st.markdown("&nbsp;")

        # ---- Metric cards ----
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("allergy_risk", lang), tr_risk(allergy["predicted_class"], lang))
        m2.metric(t("side_effect_risk", lang), tr_risk(side_effect["predicted_class"], lang))
        m3.metric(t("overall_risk", lang), tr_risk(overall_risk, lang))
        if rsv_risk:
            m4.metric(t("rsv_risk", lang), tr_risk(rsv_risk.get("risk_level", "N/A"), lang))

        # ---- Progress bars for probabilities ----
        st.markdown(f"#### {t('prediction_probabilities', lang)}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{t('allergy_probs', lang)}**")
            for cls, prob in allergy["probabilities"].items():
                st.write(f"{tr_risk(cls, lang)}: {prob * 100:.1f}%")
                st.progress(min(max(prob, 0.0), 1.0))
        with col2:
            st.markdown(f"**{t('side_effect_probs', lang)}**")
            for cls, prob in side_effect["probabilities"].items():
                st.write(f"{tr_risk(cls, lang)}: {prob * 100:.1f}%")
                st.progress(min(max(prob, 0.0), 1.0))

        # ---- Risk gauges ----
        st.markdown(f"#### {t('risk_gauges', lang)}")
        g1, g2 = st.columns(2)
        with g1:
            allergy_top_prob = allergy["probabilities"].get(allergy["predicted_class"], 0)
            fig1 = _risk_gauge(t("allergy_risk", lang), allergy["predicted_class"], allergy_top_prob, lang)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        with g2:
            se_top_prob = side_effect["probabilities"].get(side_effect["predicted_class"], 0)
            fig2 = _risk_gauge(t("side_effect_risk", lang), side_effect["predicted_class"], se_top_prob, lang)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)

        # ---- Bar chart comparing probability distributions ----
        st.markdown(f"#### {t('risk_prob_comparison', lang)}")
        x_label, y_label, type_label = (
            t("risk_level_axis", lang), t("probability_axis", lang), t("prediction_type", lang),
        )
        chart_df = pd.DataFrame({
            x_label: [tr_risk(k, lang) for k in allergy["probabilities"].keys()]
                     + [tr_risk(k, lang) for k in side_effect["probabilities"].keys()],
            y_label: list(allergy["probabilities"].values()) + list(side_effect["probabilities"].values()),
            type_label: ([t("allergy_risk", lang)] * len(allergy["probabilities"])) +
                        ([t("side_effect_risk", lang)] * len(side_effect["probabilities"])),
        })
        fig3 = px.bar(
            chart_df, x=x_label, y=y_label, color=type_label,
            barmode="group", color_discrete_sequence=["#3498db", "#9b59b6"],
        )
        fig3.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig3, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering Digital Twin card: {e}")


def render_batch_summary(twins: list, key_prefix: str = "batch"):
    """Renders the batch summary table, aggregate charts, and a
    per-patient drill-down for a list of Digital Twin results. Public
    so other pages (e.g. CSV Upload) can render this inline right after
    processing, without requiring a trip to the Dashboard page.

    key_prefix keeps widget keys unique when this is called from more
    than one page (only one page runs per script execution, but a
    distinct prefix avoids any ambiguity)."""
    try:
        st.markdown(f"### Batch Summary — {len(twins)} Patients")

        summary_rows = []
        for twin in twins:
            rsv = twin.get("rsv_risk") or {}
            summary_rows.append({
                "PatientName": twin["patient_details"].get("PatientName"),
                "Age": twin["patient_details"].get("Age"),
                "Gender": twin["patient_details"].get("Gender"),
                "Allergy_Risk": twin["allergy_risk"]["predicted_class"],
                "SideEffect_Risk": twin["side_effect_risk"]["predicted_class"],
                "Overall_Risk": twin["overall_risk_level"],
                "Recommendation": twin["recommendation"],
                "RSV_Risk": rsv.get("risk_level", "N/A"),
                "RSV_Result": rsv.get("recommendation", "N/A"),
            })
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True)

        st.download_button(
            label="Download Batch Summary (CSV)",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name="digital_twin_batch_summary.csv",
            mime="text/csv",
            key=f"{key_prefix}_download_batch_summary_csv",
        )

        # ---- Aggregate charts ----
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Overall Risk Distribution")
            fig = px.pie(
                summary_df, names="Overall_Risk", color="Overall_Risk",
                color_discrete_map=RISK_COLORS,
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_risk_pie")
        with c2:
            st.markdown("##### Recommendation Breakdown")
            fig2 = px.histogram(summary_df, x="Recommendation", color="Overall_Risk",
                                 color_discrete_map=RISK_COLORS)
            st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_rec_hist")

        st.markdown("##### Drill Down: View a Specific Patient")
        selected_name = st.selectbox(
            "Select Patient", summary_df["PatientName"].tolist(),
            key=f"{key_prefix}_select_patient",
        )
        selected_twin = next(
            (t for t in twins if t["patient_details"].get("PatientName") == selected_name), None
        )
        if selected_twin:
            st.markdown("---")
            render_digital_twin_card(selected_twin)

    except Exception as e:
        st.error(f"Error rendering batch summary: {e}")


def render_dashboard():
    """Renders the full Dashboard page."""
    try:
        st.title("Digital Twin Dashboard")

        has_single = "current_twin" in st.session_state
        has_batch = "batch_twins" in st.session_state and st.session_state["batch_twins"]

        if not has_single and not has_batch:
            st.warning(
                "No Digital Twin data available yet. Please generate one via "
                "**CSV Upload**, **Manual Entry**, or **Medical Report Upload** first."
            )
            return

        view_mode = st.radio(
            "Select View",
            ["Current Patient"] + (["Batch (CSV) Overview"] if has_batch else []),
            horizontal=True,
        )

        if view_mode == "Current Patient":
            if has_single:
                render_digital_twin_card(
                    st.session_state["current_twin"],
                    record_id=st.session_state.get("current_record_id"),
                )
            else:
                st.info("No single-patient Digital Twin found yet.")

        elif view_mode == "Batch (CSV) Overview":
            render_batch_summary(st.session_state["batch_twins"], key_prefix="dashboard_batch")

    except Exception as e:
        st.error(f"Error rendering Dashboard page: {e}")