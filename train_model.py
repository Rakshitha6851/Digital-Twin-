"""
train_model.py
----------------
Trains two RandomForestClassifier models on the synthetic dataset
(dataset/vaccine_data.csv):

    1. allergy_model.pkl      -> predicts Allergy_Risk (Low/Medium/High)
    2. side_effect_model.pkl  -> predicts SideEffect_Risk (Low/Medium/High)

Saves both trained models (plus the fitted feature encoders) to the
models/ folder using joblib, and prints accuracy + classification
reports for each.

DISCLAIMER: These models are trained purely on synthetic, artificially
generated data for educational demonstration. They must never be used
to inform real medical or clinical decisions.

Run with:
    python train_model.py
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ---- Paths ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "vaccine_data.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Feature columns used as input (X) for both models
FEATURE_COLUMNS = [
    "Age", "Gender", "ALT", "AST", "Creatinine",
    "CRP", "PEG_Allergy", "ImmuneScore", "GeneticRisk",
]


def load_dataset(path: str) -> pd.DataFrame:
    """Loads the synthetic vaccine dataset from disk."""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Dataset not found at {path}. "
                f"Run 'python dataset/generate_dataset.py' first."
            )
        df = pd.read_csv(path)
        return df
    except Exception as e:
        raise RuntimeError(f"Error loading dataset: {e}")


def prepare_features(df: pd.DataFrame):
    """
    Prepares the feature matrix X. Encodes the categorical 'Gender'
    column into numeric form using LabelEncoder so RandomForest can
    consume it.
    """
    try:
        df = df.copy()
        gender_encoder = LabelEncoder()
        df["Gender"] = gender_encoder.fit_transform(df["Gender"])  # Male/Female -> 0/1
        X = df[FEATURE_COLUMNS]
        return X, gender_encoder
    except Exception as e:
        raise RuntimeError(f"Error preparing features: {e}")


def train_and_save_model(X, y, target_name: str, model_filename: str):
    """
    Trains a RandomForestClassifier for a single target column,
    prints evaluation metrics, and saves the model + label encoder
    to the models/ directory.
    """
    try:
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y.astype(str))

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)

        # ---- Evaluate ----
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(
            y_test, y_pred, target_names=label_encoder.classes_
        )

        print(f"\n===== {target_name} Model =====")
        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(report)

        # ---- Save model bundle (model + its own label encoder) ----
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_bundle = {
            "model": model,
            "label_encoder": label_encoder,
            "feature_columns": FEATURE_COLUMNS,
        }
        save_path = os.path.join(MODELS_DIR, model_filename)
        joblib.dump(model_bundle, save_path)
        print(f"Saved {target_name} model to: {save_path}")

        return model, accuracy

    except Exception as e:
        raise RuntimeError(f"Error training model for {target_name}: {e}")


def main():
    try:
        print("Loading synthetic dataset...")
        df = load_dataset(DATASET_PATH)

        print("Preparing features...")
        X, gender_encoder = prepare_features(df)

        # Save the gender encoder too, since the app needs it at inference time
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(gender_encoder, os.path.join(MODELS_DIR, "gender_encoder.pkl"))

        # ---- Train Allergy_Risk model ----
        train_and_save_model(
            X, df["Allergy_Risk"], target_name="Allergy_Risk",
            model_filename="allergy_model.pkl"
        )

        # ---- Train SideEffect_Risk model ----
        train_and_save_model(
            X, df["SideEffect_Risk"], target_name="SideEffect_Risk",
            model_filename="side_effect_model.pkl"
        )

        print("\nAll models trained and saved successfully.")

    except Exception as e:
        print(f"Training failed: {e}")


if __name__ == "__main__":
    main()
