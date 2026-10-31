"""
pages/medical_report_upload.py
---------------------------------
Lets the user upload a photo/scan (JPG, JPEG, PNG) of a medical lab
report. Runs the OpenCV preprocessing pipeline, then pytesseract OCR,
then regex field extraction. Displays the extracted fields in an
EDITABLE form (OCR is never 100% reliable) so the user can correct
any mistakes before generating the Digital Twin.
"""

import hashlib
import io

import streamlit as st
from PIL import Image, ImageOps

from utils.preprocessing import preprocess_pipeline, is_image_too_blurry, compute_blur_score
from utils.ocr import extract_text_from_image
from utils.regex_extractor import extract_fields_from_text
from utils.digital_twin import create_digital_twin
from app_pages.dashboard import render_digital_twin_card
from utils.history import save_record


REQUIRED_FIELDS = ["Age", "ALT", "AST", "Creatinine", "CRP"]

# If this many (or more) of the required clinical fields couldn't be
# extracted at all, the uploaded image doesn't contain enough usable
# data to produce a meaningful result — rather than silently falling
# back to made-up default numbers, we tell the user plainly instead.
INSUFFICIENT_DATA_THRESHOLD = 3


def _missing_required_fields(extracted_fields: dict) -> list:
    """Returns the list of required fields that OCR could not find at all."""
    try:
        return [f for f in REQUIRED_FIELDS if extracted_fields.get(f) is None]
    except Exception:
        return list(REQUIRED_FIELDS)


# Keywords that indicate the uploaded document is at least *trying* to be a
# medical/lab report (patient/clinical/lab vocabulary, common test names,
# or lab units), even if OCR couldn't pull out the specific numeric fields
# we need. Used to distinguish "wrong kind of document entirely" (Invalid
# Report) from "a real medical document that's just missing the values we
# need" (Insufficient Data).
MEDICAL_KEYWORDS = [
    "patient", "report", "lab", "laboratory", "pathology", "hospital",
    "clinic", "diagnosis", "diagnos", "doctor", "dr.", "physician",
    "consultant", "discharge", "treatment", "prescription", "clinical",
    "age", "gender", "sex", "alt", "ast", "sgpt", "sgot", "creatinine",
    "crp", "mg/dl", "u/l", "mg/l", "medical", "test result", "specimen",
    "referred by", "vaccine", "rsv", "symptom",
]


def _looks_like_medical_document(raw_text: str) -> bool:
    """Returns True if the OCR text contains at least one term that
    suggests this is genuinely medical/lab-report content, even if the
    specific required fields weren't found."""
    try:
        if not raw_text:
            return False
        lowered = raw_text.lower()
        return any(keyword in lowered for keyword in MEDICAL_KEYWORDS)
    except Exception:
        return False


def _clamp(value, min_value, max_value, default):
    """
    Safely clamps an OCR-extracted numeric value into the allowed
    [min_value, max_value] range for a given form field.

    OCR can sometimes misread decimal points (e.g. "1.06" -> "106"),
    producing values wildly outside a field's plausible range. Rather
    than letting that crash the Streamlit form (number_input requires
    min_value <= value <= max_value), we clamp it and let the user
    visually notice/correct the value in the editable form.
    """
    try:
        if value is None:
            return default
        value = float(value)
        return max(min_value, min(value, max_value))
    except (TypeError, ValueError):
        return default


@st.cache_data(show_spinner=False, max_entries=8)
def _analyze_image(image_bytes: bytes):
    """Blur check + OpenCV preprocessing + OCR for one image.

    Cached on the image bytes so that switching the result language or
    clicking Download (which rerun the page) doesn't redo the slow OCR.
    Returns (blur_score, too_blurry, processed_image, raw_text)."""
    pil_image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
    blur_score = compute_blur_score(pil_image)
    if is_image_too_blurry(pil_image):
        return blur_score, True, None, ""
    processed = preprocess_pipeline(pil_image)
    raw_text = extract_text_from_image(processed)
    return blur_score, False, processed, raw_text


def render_medical_report_upload():
    """Renders the Medical Report Upload page."""
    try:
        st.title("Upload Medical Report (Image)")
        st.info(
            "Upload a JPG/JPEG/PNG photo or scan of a lab report, or take a photo with your camera. The app will "
            "preprocess it with OpenCV, extract text with OCR, and parse key "
            "values automatically. Please review and correct the extracted "
            "values below before generating the Digital Twin — OCR can make mistakes."
        )

        input_method = st.radio(
            "How do you want to add the report?",
            ["Upload a file", "Take a photo with camera"],
            horizontal=True,
            key="report_input_method",
        )
        using_camera = input_method == "Take a photo with camera"

        if using_camera:
            st.caption(
                "Hold the report flat in good light, fill the frame, and keep the phone steady. "
                "The browser will ask for camera permission (camera needs https:// or localhost)."
            )
            uploaded_image = st.camera_input("Take a photo of the medical report")
        else:
            uploaded_image = st.file_uploader(
                "Choose a medical report image", type=["jpg", "jpeg", "png"]
            )

        if uploaded_image is not None:
            try:
                image_bytes = uploaded_image.getvalue()

                # Detect a NEW image (different content than last time) and
                # clear any previously generated Digital Twin result, so a
                # stale result from an earlier report doesn't linger on
                # screen while the user reviews the newly extracted values.
                current_file_id = hashlib.md5(image_bytes).hexdigest()
                if st.session_state.get("report_upload_file_id") != current_file_id:
                    st.session_state["report_upload_file_id"] = current_file_id
                    st.session_state["report_upload_twin"] = None
                    st.session_state["report_upload_record_id"] = None

                pil_image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
                source_label = (
                    "Medical Report (Camera)" if using_camera else "Medical Report (Upload)"
                )
                image_ext = (pil_image.format or Image.open(io.BytesIO(image_bytes)).format or "jpeg").lower()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Uploaded Image" if not using_camera else "##### Captured Photo")
                    st.image(pil_image, use_container_width=True)

                # --- Blur check + preprocessing + OCR (cached) ---
                with st.spinner("Reading the report (OpenCV preprocessing + OCR)..."):
                    blur_score, too_blurry, processed_image, raw_text = _analyze_image(image_bytes)

                if too_blurry:
                    st.error(
                        f"Image not recognized — it appears too blurry to read reliably "
                        f"(sharpness score: {blur_score:.1f}). Please "
                        f"{'retake the photo' if using_camera else 'upload a clearer photo or scan'} "
                        f"of the medical report: hold the camera steady, ensure good lighting, "
                        f"and make sure the text is in focus before capturing."
                    )
                    return

                with col2:
                    st.markdown("##### Preprocessed Image (for OCR)")
                    st.image(processed_image, use_container_width=True, clamp=True)

                with st.expander("View Raw OCR Text"):
                    st.text(raw_text if raw_text else "No text detected.")

                extracted_fields = extract_fields_from_text(raw_text)

                # --- Insufficient data check ---
                # If the report doesn't actually contain the values needed to
                # calculate a result (wrong document type, empty/near-empty
                # scan, etc.), say so clearly instead of quietly generating a
                # result built mostly from made-up default numbers.
                missing_fields = _missing_required_fields(extracted_fields)
                if len(missing_fields) >= INSUFFICIENT_DATA_THRESHOLD:
                    if not _looks_like_medical_document(raw_text):
                        # No medical/lab-report vocabulary detected at all —
                        # this is the wrong kind of document entirely.
                        st.error(
                            "**Invalid Report** — this doesn't appear to be a "
                            "medical/lab report at all (no patient, lab, or clinical "
                            "information was detected).\n\n"
                            "Please upload a genuine medical lab report image."
                        )
                    else:
                        # It reads as a medical document, but is missing the
                        # specific values needed to calculate a result.
                        st.error(
                            "**Insufficient Data** — this report doesn't contain enough "
                            "of the required lab values to calculate a result.\n\n"
                            f"Missing: **{', '.join(missing_fields)}**\n\n"
                            "Please upload a report that includes Age, ALT, AST, "
                            "Creatinine, and CRP, or use **Manual Entry** / "
                            "**CSV Upload** instead."
                        )
                    return

                st.markdown("---")
                st.markdown("### Review & Edit Extracted Values")
                st.caption(
                    "OCR-extracted values are pre-filled below. Please verify and correct as needed. "
                    "Values outside plausible medical ranges (likely OCR misreads) are auto-capped — double-check them."
                )

                with st.form("ocr_review_form"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        patient_name = st.text_input(
                            "Patient Name", value=extracted_fields.get("PatientName") or ""
                        )
                        age = st.number_input(
                            "Age", min_value=0, max_value=120,
                            value=int(_clamp(extracted_fields.get("Age"), 0, 120, 40))
                        )
                        gender = st.selectbox(
                            "Gender", ["Male", "Female"],
                            index=0 if (extracted_fields.get("Gender") or "Male") == "Male" else 1
                        )
                        peg_allergy = st.selectbox("PEG Allergy History", ["No", "Yes"])

                    with col_b:
                        alt = st.number_input(
                            "ALT (U/L)", min_value=0.0, max_value=500.0,
                            value=_clamp(extracted_fields.get("ALT"), 0.0, 500.0, 30.0)
                        )
                        ast = st.number_input(
                            "AST (U/L)", min_value=0.0, max_value=500.0,
                            value=_clamp(extracted_fields.get("AST"), 0.0, 500.0, 28.0)
                        )
                        creatinine = st.number_input(
                            "Creatinine (mg/dL)", min_value=0.0, max_value=10.0, step=0.01,
                            value=_clamp(extracted_fields.get("Creatinine"), 0.0, 10.0, 1.0)
                        )
                        crp = st.number_input(
                            "CRP (mg/L)", min_value=0.0, max_value=200.0,
                            value=_clamp(extracted_fields.get("CRP"), 0.0, 200.0, 8.0)
                        )

                    confirmed = st.form_submit_button("Generate Digital Twin", type="primary")

                # Immune Score / Genetic Risk Score aren't printed on real lab
                # reports, so a fixed baseline is used for both.
                immune_score = 50
                genetic_risk = 30

                if confirmed:
                    patient = {
                        "PatientName": patient_name or "Unknown Patient",
                        "Age": age, "Gender": gender, "ALT": alt, "AST": ast,
                        "Creatinine": creatinine, "CRP": crp,
                        "PEG_Allergy": 1 if peg_allergy == "Yes" else 0,
                        "ImmuneScore": immune_score, "GeneticRisk": genetic_risk,
                    }
                    with st.spinner("Running ML prediction and building Digital Twin..."):
                        twin = create_digital_twin(patient)

                    st.session_state["current_patient"] = patient
                    st.session_state["current_twin"] = twin
                    # Separate, page-scoped key so the inline result below
                    # persists across reruns (e.g. clicking the PDF download
                    # button inside the card), without showing a stale
                    # result left over from a different page (Manual Entry
                    # / CSV Upload) that also sets "current_twin".
                    st.session_state["report_upload_twin"] = twin

                    # Save the uploaded/captured image, the confirmed values,
                    # the result and the OCR text to History.
                    try:
                        record_id = save_record(
                            patient, twin, source=source_label,
                            image_bytes=image_bytes, image_ext=image_ext,
                            raw_ocr_text=raw_text,
                        )
                        st.session_state["report_upload_record_id"] = record_id
                        st.session_state["current_record_id"] = record_id
                    except Exception as save_err:
                        st.session_state["report_upload_record_id"] = None
                        st.session_state["current_record_id"] = None
                        st.warning(f"Result generated, but it could not be saved to History: {save_err}")

                    st.success("Digital Twin generated successfully! Saved to History.")

                if st.session_state.get("report_upload_twin") is not None:
                    st.markdown("---")
                    render_digital_twin_card(
                        st.session_state["report_upload_twin"],
                        record_id=st.session_state.get("report_upload_record_id"),
                    )

            except Exception as e:
                st.error(f"Error processing uploaded medical report: {e}")
        else:
            # No file currently selected (initial load, or the user removed
            # a previously uploaded file) — don't show a stale result from
            # an earlier upload.
            st.session_state["report_upload_file_id"] = None
            st.session_state["report_upload_twin"] = None
            st.session_state["report_upload_record_id"] = None

    except Exception as e:
        st.error(f"Error rendering Medical Report Upload page: {e}")