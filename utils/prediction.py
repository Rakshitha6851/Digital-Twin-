"""
prediction.py
---------------
Loads the trained RandomForest model bundles (models/allergy_model.pkl
and models/side_effect_model.pkl) and runs predictions on a single
patient record, returning both the predicted risk class and the
class probabilities (used for the dashboard's percentage bars/gauges).
"""

import os
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

ALLERGY_MODEL_PATH = os.path.join(MODELS_DIR, "allergy_model.pkl")
SIDE_EFFECT_MODEL_PATH = os.path.join(MODELS_DIR, "side_effect_model.pkl")
GENDER_ENCODER_PATH = os.path.join(MODELS_DIR, "gender_encoder.pkl")


def _load_bundle(path: str):
    """Loads a joblib model bundle, raising a clear error if missing."""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model file not found: {path}. "
                f"Please run 'python train_model.py' first to train and save the models."
            )
        return joblib.load(path)
    except Exception as e:
        raise RuntimeError(f"Error loading model bundle from {path}: {e}")


def load_models():
    """
    Loads both model bundles and the gender encoder once. Intended to
    be cached by the Streamlit app (st.cache_resource) so models are
    not reloaded from disk on every interaction.
    """
    try:
        allergy_bundle = _load_bundle(ALLERGY_MODEL_PATH)
        side_effect_bundle = _load_bundle(SIDE_EFFECT_MODEL_PATH)
        gender_encoder = joblib.load(GENDER_ENCODER_PATH) if os.path.exists(GENDER_ENCODER_PATH) else None
        return allergy_bundle, side_effect_bundle, gender_encoder
    except Exception as e:
        raise RuntimeError(f"Error loading trained models: {e}")


def _encode_gender(gender_value: str, gender_encoder) -> int:
    """Safely encodes a gender string using the saved LabelEncoder,
    falling back to a simple manual mapping if the encoder is
    unavailable or the value is unseen."""
    try:
        if gender_encoder is not None and gender_value in list(gender_encoder.classes_):
            return int(gender_encoder.transform([gender_value])[0])
        # Fallback manual mapping
        return 1 if str(gender_value).strip().lower().startswith("m") else 0
    except Exception:
        return 0


def build_feature_row(patient: dict, gender_encoder) -> pd.DataFrame:
    """
    Converts a patient dictionary (from manual entry / OCR / CSV row)
    into a single-row DataFrame matching the exact feature order the
    models were trained on.
    """
    try:
        row = {
            "Age": float(patient.get("Age", 0) or 0),
            "Gender": _encode_gender(patient.get("Gender", "Male"), gender_encoder),
            "ALT": float(patient.get("ALT", 0) or 0),
            "AST": float(patient.get("AST", 0) or 0),
            "Creatinine": float(patient.get("Creatinine", 0) or 0),
            "CRP": float(patient.get("CRP", 0) or 0),
            "PEG_Allergy": int(patient.get("PEG_Allergy", 0) or 0),
            "ImmuneScore": float(patient.get("ImmuneScore", 50) or 50),
            "GeneticRisk": float(patient.get("GeneticRisk", 50) or 50),
        }
        return pd.DataFrame([row])
    except Exception as e:
        raise RuntimeError(f"Error building feature row for prediction: {e}")


def predict_risk(model_bundle: dict, feature_row: pd.DataFrame) -> dict:
    """
    Runs a prediction using a single model bundle.

    Returns:
        {
            "predicted_class": "Low" | "Medium" | "High",
            "probabilities": {"Low": 0.7, "Medium": 0.2, "High": 0.1}
        }
    """
    try:
        model = model_bundle["model"]
        label_encoder = model_bundle["label_encoder"]
        feature_columns = model_bundle["feature_columns"]

        X = feature_row[feature_columns]
        pred_encoded = model.predict(X)[0]
        pred_proba = model.predict_proba(X)[0]

        predicted_class = label_encoder.inverse_transform([pred_encoded])[0]
        proba_dict = {
            label_encoder.inverse_transform([i])[0]: float(round(p, 4))
            for i, p in enumerate(pred_proba)
        }

        return {"predicted_class": predicted_class, "probabilities": proba_dict}
    except Exception as e:
        raise RuntimeError(f"Error during risk prediction: {e}")


def run_full_prediction(patient: dict) -> dict:
    """
    High-level convenience function: loads models, builds the feature
    row, and returns predictions for BOTH Allergy_Risk and
    SideEffect_Risk in a single dictionary.
    """
    try:
        allergy_bundle, side_effect_bundle, gender_encoder = load_models()
        feature_row = build_feature_row(patient, gender_encoder)

        allergy_result = predict_risk(allergy_bundle, feature_row)
        side_effect_result = predict_risk(side_effect_bundle, feature_row)

        return {
            "allergy": allergy_result,
            "side_effect": side_effect_result,
        }
    except Exception as e:
        raise RuntimeError(f"Error running full prediction pipeline: {e}")
