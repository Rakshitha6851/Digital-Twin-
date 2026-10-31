"""
utils/validation.py
-----------------------
Age/sex-aware clinical reference-range validation for the Manual Entry
workflow. This runs BEFORE the prediction model. If Age/Sex are
missing or invalid, or if any lab value is missing, non-numeric,
physically impossible, or outside its age/sex-appropriate reference
range, prediction is blocked and the specific failing field(s) are
returned so the page can display them.

====================================================================
CONFIGURATION - REFERENCE RANGES  (edit this section only)
====================================================================
This project did not already define age/sex-specific reference
ranges anywhere else in the codebase (only rough, adult-oriented,
non-age-aware thresholds exist inside utils/rsv_risk.py, for a
different purpose - RSV vaccination risk scoring - not general lab
validation).

The ranges below are therefore standard, commonly-published clinical
reference intervals (the kind found in general lab-medicine
references), used as sensible out-of-the-box defaults so this feature
works immediately. They are NOT taken from this project's own
dataset/lab, and real reference ranges legitimately vary between labs,
instruments, and populations.

Before relying on this for anything beyond a learning demo, replace
or verify these numbers against your own trusted clinical source
(e.g. your lab's own reference intervals, or a peer-reviewed
pediatric/adult reference table). No other code in this file needs to
change to update the ranges - only the tables below.
====================================================================
"""


# ---- Age bands (in years): [low, high) - each age matches exactly one ----
AGE_BANDS = [
    ("infant",      0,   1),    # 0 to <1 year
    ("child",       1,   12),   # 1 to <12 years
    ("adolescent",  12,  18),   # 12 to <18 years
    ("adult",       18,  65),   # 18 to <65 years
    ("elderly",     65,  130),  # 65+ years
]

# ---- Reference ranges: (min, max) in each parameter's usual unit ----
# CRP uses the same normal range for males/females at every age band in
# standard references. ALT / AST / Creatinine vary by age band and,
# from adolescence onward, by sex.
REFERENCE_RANGES = {
    "ALT": {  # U/L
        "infant":     {"Male": (5, 45),  "Female": (5, 45)},
        "child":      {"Male": (5, 35),  "Female": (5, 35)},
        "adolescent": {"Male": (5, 40),  "Female": (5, 35)},
        "adult":      {"Male": (7, 55),  "Female": (7, 45)},
        "elderly":    {"Male": (7, 55),  "Female": (7, 45)},
    },
    "AST": {  # U/L
        "infant":     {"Male": (10, 58), "Female": (10, 58)},
        "child":      {"Male": (10, 50), "Female": (10, 50)},
        "adolescent": {"Male": (10, 45), "Female": (10, 40)},
        "adult":      {"Male": (8, 48),  "Female": (8, 43)},
        "elderly":    {"Male": (8, 48),  "Female": (8, 43)},
    },
    "Creatinine": {  # mg/dL
        "infant":     {"Male": (0.2, 0.4), "Female": (0.2, 0.4)},
        "child":      {"Male": (0.3, 0.7), "Female": (0.3, 0.7)},
        "adolescent": {"Male": (0.5, 1.0), "Female": (0.4, 0.9)},
        "adult":      {"Male": (0.7, 1.3), "Female": (0.6, 1.1)},
        "elderly":    {"Male": (0.7, 1.3), "Female": (0.6, 1.1)},
    },
    "CRP": {  # mg/L
        "infant":     {"Male": (0, 10), "Female": (0, 10)},
        "child":      {"Male": (0, 10), "Female": (0, 10)},
        "adolescent": {"Male": (0, 10), "Female": (0, 10)},
        "adult":      {"Male": (0, 10), "Female": (0, 10)},
        "elderly":    {"Male": (0, 10), "Female": (0, 10)},
    },
}

UNITS = {"ALT": "U/L", "AST": "U/L", "Creatinine": "mg/dL", "CRP": "mg/L"}

# Physically-impossible bounds (reject obvious data-entry errors
# regardless of age/sex - e.g. a negative lab value can never be real).
ABSOLUTE_BOUNDS = {
    "ALT": (0, 5000),
    "AST": (0, 5000),
    "Creatinine": (0, 50),
    "CRP": (0, 1000),
}
# ====================================================================
# END CONFIGURATION
# ====================================================================


def _get_age_band(age: float) -> str:
    """Maps a numeric age (years) to one of the AGE_BANDS names."""
    for band_name, low, high in AGE_BANDS:
        if low <= age < high:
            return band_name
    return "adult"  # fallback, should not normally be reached


def get_reference_range(parameter: str, age: float, sex: str):
    """Returns the (min, max) reference range for a lab parameter, given
    a patient's age (years) and sex ('Male' or 'Female')."""
    band = _get_age_band(age)
    sex_key = "Male" if str(sex).strip().lower().startswith("m") else "Female"
    return REFERENCE_RANGES[parameter][band][sex_key]


def validate_patient_values(age, sex, alt, ast, creatinine, crp) -> dict:
    """
    Validates Age, Sex, ALT, AST, Creatinine, and CRP before prediction,
    per the required flow:
        1. Check Age and Sex first.
        2. Use them to select the age/sex-appropriate reference range
           for each lab value.
        3. Check every lab value against its applicable range.

    Returns:
        {
            "valid": bool,
            "failures": [
                {
                    "field": "ALT",
                    "value": 70,
                    "unit": "U/L",
                    "expected_range": (5, 35),
                    "reason": "outside expected range",
                },
                ...
            ],
        }

    A field fails validation if it is missing, non-numeric, physically
    impossible (see ABSOLUTE_BOUNDS), or outside its age/sex-appropriate
    reference range from REFERENCE_RANGES.
    """
    failures = []

    # ---- Step 1: Age and Sex must themselves be valid first, since
    # every lab threshold below depends on them. ----
    # Allowed range: 0 < Age <= 120 (Age = 0 and Age > 120 are invalid).
    age_val = None
    try:
        age_val = float(age)
        if age_val <= 0 or age_val > 120:
            failures.append({
                "field": "Age", "value": age, "unit": "years",
                # expected_range left as None here (rather than (1, 120))
                # so the page doesn't append a duplicate "(expected
                # range: ...)" suffix - the exact required message is
                # already in "reason" below.
                "expected_range": None,
                "reason": "Age must be between 1 and 120.",
            })
            age_val = None
    except (TypeError, ValueError):
        failures.append({
            "field": "Age", "value": age, "unit": "years",
            "expected_range": None,
            "reason": "missing or non-numeric",
        })

    sex_str = str(sex).strip() if sex else ""
    if sex_str.lower() not in ("male", "female"):
        failures.append({
            "field": "Sex", "value": sex, "unit": None,
            "expected_range": None,
            "reason": "must be 'Male' or 'Female'",
        })
        sex_str = ""

    # If Age or Sex is itself invalid, there is no reliable threshold to
    # check labs against - stop here rather than guessing a default.
    if age_val is None or not sex_str:
        return {"valid": False, "failures": failures}

    # ---- Step 2 & 3: Look up age/sex-appropriate thresholds and check
    # every lab value against them. ----
    raw_values = {"ALT": alt, "AST": ast, "Creatinine": creatinine, "CRP": crp}

    for field, raw_value in raw_values.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            failures.append({
                "field": field, "value": raw_value, "unit": UNITS[field],
                "expected_range": None,
                "reason": "missing or non-numeric",
            })
            continue

        abs_low, abs_high = ABSOLUTE_BOUNDS[field]
        if value < abs_low or value > abs_high:
            failures.append({
                "field": field, "value": value, "unit": UNITS[field],
                "expected_range": (abs_low, abs_high),
                "reason": "physically impossible value",
            })
            continue

        low, high = get_reference_range(field, age_val, sex_str)
        if value < low or value > high:
            failures.append({
                "field": field, "value": value, "unit": UNITS[field],
                "expected_range": (low, high),
                "reason": "outside expected range",
            })

    return {"valid": len(failures) == 0, "failures": failures}
