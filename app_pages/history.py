"""
app_pages/history.py
-----------------------
Shows everything saved earlier: each generated Digital Twin (from Medical
Report Upload — file or camera — and Manual Entry), the original image,
the values used, and every PDF report that was downloaded. Results can be
reopened in English / Hindi / Kannada and re-downloaded.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from utils import history as store
from utils.i18n import LANGUAGES
from app_pages.dashboard import render_digital_twin_card

_LANG_NAMES = {code: label for label, code in LANGUAGES.items()}


def _fmt_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %I:%M %p")
    except (TypeError, ValueError):
        return iso or ""


def render_history():
    """Renders the History page."""
    try:
        st.title("History")
        st.caption(
            "Saved results, the images you uploaded or captured, and the reports you "
            "downloaded. Stored on the machine running this app."
        )

        records = store.list_records()
        if not records:
            st.info(
                "Nothing saved yet. Generate a Digital Twin from **Medical Report Upload** "
                "or **Manual Entry** and it will appear here."
            )
            return

        rows = []
        for r in records:
            twin = r.get("twin", {})
            rows.append({
                "Date": _fmt_time(r.get("created_at")),
                "Patient": r.get("patient", {}).get("PatientName", "Unknown"),
                "Source": r.get("source", ""),
                "Overall Risk": twin.get("overall_risk_level", "N/A"),
                "RSV Risk": (twin.get("rsv_risk") or {}).get("risk_level", "N/A"),
                "Reports downloaded": len(r.get("downloads", [])),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        ids = [r["id"] for r in records]
        labels = {
            r["id"]: f"{_fmt_time(r.get('created_at'))} — "
                     f"{r.get('patient', {}).get('PatientName', 'Unknown')} ({r.get('source', '')})"
            for r in records
        }
        selected_id = st.selectbox(
            "Open a saved result", ids, format_func=lambda i: labels.get(i, i),
            key="history_selected_id",
        )
        record = store.load_record(selected_id)
        if record is None:
            st.error("This record could not be read.")
            return

        st.markdown("---")

        # ---- Source image + values that were used ----
        image_bytes = store.read_source_image(record)
        info_col, img_col = st.columns([1, 1])
        with info_col:
            st.markdown("##### Values used")
            p = record.get("patient", {})
            st.table(pd.DataFrame({
                "Field": ["Name", "Age", "Gender", "ALT (U/L)", "AST (U/L)",
                          "Creatinine (mg/dL)", "CRP (mg/L)", "PEG allergy"],
                "Value": [p.get("PatientName"), p.get("Age"), p.get("Gender"), p.get("ALT"),
                          p.get("AST"), p.get("Creatinine"), p.get("CRP"),
                          "Yes" if p.get("PEG_Allergy") else "No"],
            }).astype(str))
        with img_col:
            if image_bytes:
                st.markdown("##### Uploaded / captured image")
                st.image(image_bytes, use_container_width=True)
            else:
                st.caption("No image was saved for this entry (it was typed in manually).")

        if record.get("raw_ocr_text"):
            with st.expander("View saved OCR text"):
                st.text(record["raw_ocr_text"])

        # ---- Previously downloaded reports ----
        downloads = record.get("downloads", [])
        st.markdown("##### Downloaded reports")
        if not downloads:
            st.caption("No report has been downloaded for this result yet.")
        for i, d in enumerate(reversed(downloads)):
            data = store.read_report_file(d.get("file"))
            c1, c2 = st.columns([3, 1])
            c1.write(f"{_fmt_time(d.get('at'))} — {_LANG_NAMES.get(d.get('lang'), d.get('lang'))}")
            if data:
                c2.download_button(
                    "Download again", data=data, file_name=d.get("file"),
                    mime="application/pdf", key=f"hist_dl_{selected_id}_{i}",
                )
            else:
                c2.caption("file missing")

        # ---- Full result (language selector + new PDF download) ----
        st.markdown("---")
        render_digital_twin_card(record["twin"], record_id=selected_id)

        # ---- Delete ----
        st.markdown("---")
        with st.expander("Delete saved data"):
            st.warning("Deleting removes the result, its image and its downloaded reports permanently.")
            d1, d2 = st.columns(2)
            if d1.button("Delete this record", key="hist_delete_one"):
                store.delete_record(selected_id)
                st.session_state.pop("history_selected_id", None)
                st.rerun()
            confirm_all = d2.checkbox("I want to delete ALL history", key="hist_confirm_all")
            if d2.button("Delete all history", key="hist_delete_all", disabled=not confirm_all):
                store.delete_all()
                st.session_state.pop("history_selected_id", None)
                st.rerun()

    except Exception as e:
        st.error(f"Error rendering History page: {e}")
