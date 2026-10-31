"""
pages/manual_entry.py
------------------------
Allows the user to manually type in a single patient's details via a
Streamlit form, then runs the Digital Twin ML pipeline and stores the
result in st.session_state for the Dashboard page.
"""

import streamlit as st
from utils.digital_twin import create_digital_twin
from utils.validation import validate_patient_values
from app_pages.dashboard import render_digital_twin_card
from utils.history import save_record


def render_manual_entry():
    """Renders the Manual Entry page."""
    try:
        st.title("Manual Patient Data Entry")
        st.info("Fill in the patient's details below to generate their Digital Twin.")

        with st.form("manual_entry_form"):
            col1, col2 = st.columns(2)

            with col1:
                patient_name = st.text_input("Patient Name", value="John Doe")
                # No min_value/max_value here on purpose: Streamlit enforces
                # those as hard HTML constraints in the browser, which
                # silently blocks/clamps out-of-range typed values (e.g.
                # 130) before they ever reach this script - so an invalid
                # age could never actually be checked by our own
                # validate_patient_values() rule (0 < Age <= 120) below.
                # Leaving this unbounded lets the real typed value through,
                # so our validator is the single source of truth for the
                # Age rule and always gets a chance to reject it.
                age = st.number_input("Age", value=40, step=1)
                gender = st.selectbox("Gender", ["Male", "Female"])
                peg_allergy = st.selectbox("PEG Allergy History", ["No", "Yes"])

            with col2:
                alt = st.number_input("ALT (U/L)", min_value=0.0, max_value=500.0, value=30.0)
                ast = st.number_input("AST (U/L)", min_value=0.0, max_value=500.0, value=28.0)
                creatinine = st.number_input("Creatinine (mg/dL)", min_value=0.0, max_value=10.0, value=1.0, step=0.01)
                crp = st.number_input("CRP (mg/L)", min_value=0.0, max_value=200.0, value=8.0)

            submitted = st.form_submit_button("Generate Digital Twin", type="primary")

        # Immune Score / Genetic Risk Score aren't collected via the UI (they
        # aren't printed on real lab reports either) — a fixed baseline is
        # used for both, same as Medical Report Upload.
        immune_score = 50
        genetic_risk = 30

        if submitted:
            try:
                # ---- Validation step (runs BEFORE the prediction model) ----
                # Uses Age + Sex to select the age/sex-appropriate reference
                # range for ALT, AST, Creatinine, and CRP, then checks every
                # entered value against it. See utils/validation.py for the
                # configurable reference-range tables.
                validation_result = validate_patient_values(
                    age=age, sex=gender, alt=alt, ast=ast,
                    creatinine=creatinine, crp=crp,
                )

                if not validation_result["valid"]:
                    # Clear any previously generated result for this page so
                    # an invalid submission truly shows nothing but the
                    # error - not a leftover Digital Twin from an earlier,
                    # valid submission.
                    st.session_state.pop("manual_entry_twin", None)

                    st.error("**Invalid Data**")
                    for failure in validation_result["failures"]:
                        unit = f" {failure['unit']}" if failure["unit"] else ""
                        value = failure["value"]
                        value_str = "missing" if value in (None, "") else f"{value}{unit}"
                        line = f"**{failure['field']}**: {value_str} — {failure['reason']}"
                        expected = failure["expected_range"]
                        if expected:
                            line += f" (expected range: {expected[0]}–{expected[1]}{unit})"
                        st.markdown(f"- {line}")
                    st.warning("Please correct the entered values before prediction.")

                else:
                    patient = {
                        "PatientName": patient_name,
                        "Age": age,
                        "Gender": gender,
                        "ALT": alt,
                        "AST": ast,
                        "Creatinine": creatinine,
                        "CRP": crp,
                        "PEG_Allergy": 1 if peg_allergy == "Yes" else 0,
                        "ImmuneScore": immune_score,
                        "GeneticRisk": genetic_risk,
                    }

                    with st.spinner("Running ML prediction and building Digital Twin..."):
                        twin = create_digital_twin(patient)

                    st.session_state["current_patient"] = patient
                    st.session_state["current_twin"] = twin
                    # Separate, page-scoped key so the inline result below
                    # persists across reruns (e.g. clicking the PDF download
                    # button inside the card), without showing a stale result
                    # left over from a different page (CSV Upload / Medical
                    # Report Upload) that also sets "current_twin".
                    st.session_state["manual_entry_twin"] = twin

                    try:
                        record_id = save_record(patient, twin, source="Manual Entry")
                        st.session_state["manual_entry_record_id"] = record_id
                        st.session_state["current_record_id"] = record_id
                    except Exception as save_err:
                        st.session_state["manual_entry_record_id"] = None
                        st.session_state["current_record_id"] = None
                        st.warning(f"Result generated, but it could not be saved to History: {save_err}")

                    st.success("Digital Twin generated successfully! Saved to History.")

            except Exception as e:
                st.error(f"Error generating Digital Twin: {e}")

        if st.session_state.get("manual_entry_twin") is not None:
            st.markdown("---")
            render_digital_twin_card(
                st.session_state["manual_entry_twin"],
                record_id=st.session_state.get("manual_entry_record_id"),
            )

    except Exception as e:
        st.error(f"Error rendering Manual Entry page: {e}")