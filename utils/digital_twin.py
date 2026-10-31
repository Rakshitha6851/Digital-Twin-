"""
digital_twin.py
------------------
Builds the "AI Digital Twin" profile for a patient: a consolidated
virtual representation combining patient details, ML-predicted risk
scores, side-effect probability, and a rule-based recommendation.

DISCLAIMER: The Digital Twin and its recommendation are purely
illustrative outputs of a synthetic-data ML demo. They are NOT medical
advice and must never be used for real clinical decisions.
"""

from utils.prediction import run_full_prediction
from utils.rsv_risk import assess_rsv_risk

# Risk level -> recommendation text mapping
RECOMMENDATIONS = {
    "Low": "Vaccination Recommended",
    "Medium": "Vaccinate Under Observation",
    "High": "Specialist Consultation Required",
}

# Numeric weight used to combine allergy + side-effect risk into one
# overall risk score for the digital twin summary
RISK_WEIGHTS = {"Low": 1, "Medium": 2, "High": 3}


def _overall_risk_level(allergy_class: str, side_effect_class: str) -> str:
    """
    Combines the two individual risk classes into a single overall
    risk level by taking the higher-severity of the two (a
    conservative/safety-first approach for a health-related demo).
    """
    try:
        allergy_weight = RISK_WEIGHTS.get(allergy_class, 1)
        side_effect_weight = RISK_WEIGHTS.get(side_effect_class, 1)
        max_weight = max(allergy_weight, side_effect_weight)
        for level, weight in RISK_WEIGHTS.items():
            if weight == max_weight:
                return level
        return "Medium"
    except Exception:
        return "Medium"


def create_digital_twin(patient: dict) -> dict:
    """
    Creates a full Digital Twin profile for the given patient dict.

    Args:
        patient: dict with keys like PatientName, Age, Gender, ALT,
                 AST, Creatinine, CRP, PEG_Allergy, ImmuneScore,
                 GeneticRisk (missing keys default sensibly).

    Returns:
        A dictionary containing:
            - patient_details
            - allergy_risk (class + probabilities)
            - side_effect_risk (class + probabilities)
            - overall_risk_level
            - recommendation
    """
    try:
        predictions = run_full_prediction(patient)

        allergy_class = predictions["allergy"]["predicted_class"]
        side_effect_class = predictions["side_effect"]["predicted_class"]

        overall_risk = _overall_risk_level(allergy_class, side_effect_class)
        recommendation = RECOMMENDATIONS.get(overall_risk, "Specialist Consultation Required")

        # RSV (Respiratory Syncytial Virus) risk screening add-on:
        # rule-based, using Age/CRP/ALT/AST already collected for every patient.
        rsv_risk = assess_rsv_risk(patient)

        digital_twin_profile = {
            "patient_details": {
                "PatientName": patient.get("PatientName", "Unknown"),
                "Age": patient.get("Age", "N/A"),
                "Gender": patient.get("Gender", "N/A"),
                "ALT": patient.get("ALT", "N/A"),
                "AST": patient.get("AST", "N/A"),
                "Creatinine": patient.get("Creatinine", "N/A"),
                "CRP": patient.get("CRP", "N/A"),
            },
            "allergy_risk": predictions["allergy"],
            "side_effect_risk": predictions["side_effect"],
            "overall_risk_level": overall_risk,
            "recommendation": recommendation,
            "rsv_risk": rsv_risk,
        }
        return digital_twin_profile

    except Exception as e:
        raise RuntimeError(f"Error creating digital twin profile: {e}")
