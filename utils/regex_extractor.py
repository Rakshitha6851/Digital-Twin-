"""
regex_extractor.py
--------------------
Parses the raw OCR text (produced by utils/ocr.py) using regular
expressions to pull out structured medical report fields:

    - Patient Name
    - Age
    - Gender
    - ALT
    - AST
    - Creatinine
    - CRP

Returns a dictionary such as:
{
    "PatientName": "Rahul Verma",
    "Age": 45,
    "Gender": "Male",
    "ALT": 47,
    "AST": 42,
    "Creatinine": 1.06,
    "CRP": 19.5
}

Missing fields are returned as None so the calling UI can prompt the
user to fill them in manually (the app always allows manual editing
of OCR results, since OCR on real-world scans is never 100% reliable).
"""

import re
from typing import Optional, Dict, Any


# OCR frequently confuses visually similar letters and digits, especially
# in tightly-kerned printed text (e.g. "45" -> "4S", "0" -> "O"). This
# translation table is used ONLY on short, isolated tokens we already know
# are supposed to be numeric (e.g. an age value), to recover the intended
# digit.
_OCR_DIGIT_FIX = str.maketrans({
    "O": "0", "o": "0", "D": "0",
    "S": "5", "s": "5",
    "I": "1", "l": "1", "i": "1",
    "B": "8",
    "Z": "2", "z": "2",
    "G": "6",
})


def _fix_ocr_digits(token: str) -> str:
    """Applies letter->digit OCR-confusion fixes to a short token."""
    try:
        return token.translate(_OCR_DIGIT_FIX)
    except Exception:
        return token


def _search_float(pattern: str, text: str) -> Optional[float]:
    """Helper: search for a numeric pattern and return it as a float."""
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None
    except Exception:
        return None


def _search_int(pattern: str, text: str) -> Optional[int]:
    """Helper: search for a numeric pattern and return it as an int."""
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(float(match.group(1)))
        return None
    except Exception:
        return None


def _search_str(pattern: str, text: str) -> Optional[str]:
    """Helper: search for a text pattern and return the matched group, stripped."""
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    except Exception:
        return None


def _fix_dropped_decimal(value: Optional[float], raw_match_str: Optional[str],
                          plausible_max: float, divisor: float) -> Optional[float]:
    """
    OCR sometimes drops the decimal point entirely (e.g. "1.06" -> "106",
    "19.5" -> "195"), rather than misplacing it. If a value comes back as a
    "clean" integer (no '.' in the original matched text) AND it's above a
    clinically plausible maximum, we assume the decimal point was lost and
    rescale it (divide by `divisor`) rather than silently discarding a
    plausible OCR read. The user still sees the result in the editable
    form and can correct it if this heuristic is wrong.
    """
    try:
        if value is None or raw_match_str is None:
            return value
        has_decimal = "." in raw_match_str
        if not has_decimal and value > plausible_max:
            return round(value / divisor, 2)
        return value
    except Exception:
        return value


def extract_fields_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Applies a series of regex patterns to raw OCR text and extracts
    the seven target medical report fields.

    Args:
        raw_text: The raw string returned by pytesseract OCR.

    Returns:
        A dictionary with keys: PatientName, Age, Gender, ALT, AST,
        Creatinine, CRP. Any field that could not be found is set to
        None.
    """
    try:
        if not raw_text:
            return {
                "PatientName": None, "Age": None, "Gender": None,
                "ALT": None, "AST": None, "Creatinine": None, "CRP": None,
            }

        text = raw_text.replace("\n", " \n")  # keep line breaks but normalize

        # OCR frequently misreads ':' as '.', so treat both as a separator
        SEP = r"\s*[:.\-]\s*"

        # --- Patient Name: e.g. "Patient Name: Rahul Verma" / "Name - Rahul Verma"
        # Uses a lookahead for the next known report field/label (rather than
        # baking stop characters into the captured character class), since
        # real lab reports often run several fields together on one OCR'd
        # "line" with only single spaces between them (no reliable newline
        # or double-space boundary to stop at).
        patient_name = _search_str(
            r"(?:Patient\s*Name|Name)" + SEP +
            r"([A-Za-z][A-Za-z\.\s]{1,40}?)"
            r"(?=\s+(?:Registered|Collected|Reported|Referred|Age|Patient\s*ID|Gender|Sex)\b|\n|$)",
            text
        )

        # --- Age & Gender ---
        # Many real-world lab reports print these as a single combined field,
        # e.g. "Age / Sex : 45 Y / Male". OCR can also mangle the digits in
        # that context (e.g. "45" -> "4S" next to the word "Sex"), so we try
        # a combined pattern FIRST (with OCR digit-fixing on the age token),
        # then fall back to simpler standalone patterns for reports that
        # print Age and Gender on separate lines.
        age = None
        gender = None

        combined_match = re.search(
            r"Age\s*/?\s*Sex" + SEP + r"([A-Za-z0-9]{1,3})\s*Y?\s*/\s*(Male|Female|M|F)\b",
            text, re.IGNORECASE
        )
        if combined_match:
            age_token = _fix_ocr_digits(combined_match.group(1))
            age_digits = re.sub(r"\D", "", age_token)
            if age_digits:
                age = int(age_digits)
            gender_token = combined_match.group(2).strip().lower()
            gender = "Male" if gender_token.startswith("m") else "Female"

        if age is None:
            # Fallback: standalone "Age: 45" / "Age - 45 Yrs"
            age = _search_int(r"Age" + SEP + r"(\d{1,3})", text)

        if gender is None:
            # Fallback: standalone "Gender: Male" / "Sex: F" / "Gender. Male"
            gender_match = _search_str(r"(?:Gender|Sex)" + SEP + r"([A-Za-z]+)", text)
            if gender_match:
                g = gender_match.strip().lower()
                if g.startswith("m"):
                    gender = "Male"
                elif g.startswith("f"):
                    gender = "Female"
                else:
                    gender = gender_match.strip().title()

        # --- ALT: e.g. "ALT: 47 U/L" / "ALT (SGPT) - 47" / "ALT. 47 U/L"
        alt = _search_float(r"ALT[^0-9]{0,20}?(\d+\.?\d*)", text)

        # --- AST: e.g. "AST: 42 U/L" / "AST (SGOT) - 42" / "AST. 42 U/L"
        ast = _search_float(r"AST[^0-9]{0,20}?(\d+\.?\d*)", text)

        # --- Creatinine: e.g. "Creatinine: 1.06 mg/dL" ---
        # OCR sometimes drops the decimal point entirely ("1.06" -> "106").
        # Normal creatinine is roughly 0.3-5.0 mg/dL, so a "clean" integer
        # read above ~15 almost certainly lost a decimal point two places in.
        creatinine_match = re.search(r"Creatinine[^0-9]{0,20}?(\d+\.?\d*)", text, re.IGNORECASE)
        creatinine = float(creatinine_match.group(1)) if creatinine_match else None
        creatinine = _fix_dropped_decimal(
            creatinine, creatinine_match.group(1) if creatinine_match else None,
            plausible_max=15.0, divisor=100.0
        )

        # --- CRP: e.g. "CRP: 19.5 mg/L" ---
        # Normal/elevated CRP is roughly 0.1-100 mg/L in most reports; a
        # "clean" integer read above ~100 with no decimal point often means
        # OCR dropped a decimal one place in (e.g. "19.5" -> "195").
        crp_match = re.search(r"C\s?RP[^0-9]{0,20}?(\d+\.?\d*)", text, re.IGNORECASE)
        crp = float(crp_match.group(1)) if crp_match else None
        crp = _fix_dropped_decimal(
            crp, crp_match.group(1) if crp_match else None,
            plausible_max=100.0, divisor=10.0
        )

        extracted = {
            "PatientName": patient_name,
            "Age": age,
            "Gender": gender,
            "ALT": alt,
            "AST": ast,
            "Creatinine": creatinine,
            "CRP": crp,
        }
        return extracted

    except Exception as e:
        raise RuntimeError(f"Error extracting structured fields from OCR text: {e}")