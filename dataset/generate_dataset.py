"""
generate_dataset.py
--------------------
Generates a SYNTHETIC dataset of 5000 rows for the AI Digital Twin
mRNA Vaccine Simulation project.

IMPORTANT: This dataset is entirely artificial and created using
statistical rules for educational/academic demonstration purposes only.
It does NOT represent real patient data and must NOT be used for any
real clinical or medical decision-making.

Run this script directly to (re)create dataset/vaccine_data.csv:
    python dataset/generate_dataset.py
"""

import numpy as np
import pandas as pd
import os

# Fix the random seed so the dataset is reproducible every time it is generated
np.random.seed(42)

# Number of synthetic patient records to generate
N_ROWS = 5000


def generate_synthetic_dataset(n_rows: int = N_ROWS) -> pd.DataFrame:
    """
    Generates a synthetic patient dataset with clinically-plausible
    (but artificial) ranges for lab values, then derives two target
    labels (Allergy_Risk, SideEffect_Risk) using simple rule-based
    heuristics + noise, so that the labels are learnable by ML models
    but not deterministic/trivial.
    """
    try:
        # ---- Demographics ----
        age = np.random.randint(1, 90, size=n_rows)                     # Age in years
        gender = np.random.choice(["Male", "Female"], size=n_rows)      # Gender

        # ---- Lab / biomarker values (synthetic, plausible ranges) ----
        alt = np.round(np.random.normal(30, 15, n_rows).clip(5, 200), 1)         # ALT (U/L)
        ast = np.round(np.random.normal(28, 14, n_rows).clip(5, 200), 1)         # AST (U/L)
        creatinine = np.round(np.random.normal(1.0, 0.4, n_rows).clip(0.3, 5.0), 2)  # Creatinine (mg/dL)
        crp = np.round(np.random.normal(8, 10, n_rows).clip(0.1, 100), 1)        # CRP (mg/L)

        # ---- Vaccine-related synthetic risk factors ----
        peg_allergy = np.random.choice([0, 1], size=n_rows, p=[0.85, 0.15])      # PEG allergy flag
        immune_score = np.round(np.random.uniform(0, 100, n_rows), 1)            # Immune competence score
        genetic_risk = np.round(np.random.uniform(0, 100, n_rows), 1)            # Genetic predisposition score

        df = pd.DataFrame({
            "Age": age,
            "Gender": gender,
            "ALT": alt,
            "AST": ast,
            "Creatinine": creatinine,
            "CRP": crp,
            "PEG_Allergy": peg_allergy,
            "ImmuneScore": immune_score,
            "GeneticRisk": genetic_risk,
        })

        # ---- Derive Allergy_Risk label using a weighted rule + random noise ----
        allergy_score = (
            df["PEG_Allergy"] * 40
            + (df["CRP"] > 20).astype(int) * 20
            + (df["GeneticRisk"] > 60).astype(int) * 20
            + np.random.normal(0, 10, n_rows)
        )
        df["Allergy_Risk"] = pd.cut(
            allergy_score,
            bins=[-np.inf, 25, 55, np.inf],
            labels=["Low", "Medium", "High"]
        )

        # ---- Derive SideEffect_Risk label using another weighted rule + noise ----
        side_effect_score = (
            (df["ALT"] > 45).astype(int) * 15
            + (df["AST"] > 40).astype(int) * 15
            + (df["Creatinine"] > 1.3).astype(int) * 20
            + (df["CRP"] > 15).astype(int) * 15
            + (df["ImmuneScore"] < 40).astype(int) * 15
            + (df["Age"] > 60).astype(int) * 10
            + np.random.normal(0, 10, n_rows)
        )
        df["SideEffect_Risk"] = pd.cut(
            side_effect_score,
            bins=[-np.inf, 25, 55, np.inf],
            labels=["Low", "Medium", "High"]
        )

        return df

    except Exception as e:
        # Fail loudly with a clear message if dataset generation breaks
        raise RuntimeError(f"Error while generating synthetic dataset: {e}")


if __name__ == "__main__":
    try:
        dataset = generate_synthetic_dataset()
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "vaccine_data.csv")
        dataset.to_csv(output_path, index=False)
        print(f"Synthetic dataset with {len(dataset)} rows saved to: {output_path}")
        print(dataset.head())
    except Exception as err:
        print(f"Failed to generate dataset: {err}")
