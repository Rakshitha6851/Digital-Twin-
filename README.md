# 🧬 AI Digital Twin for Personalized mRNA Vaccine Simulation
### Using Machine Learning and Medical Report Analysis

> ⚠️ **DISCLAIMER — EDUCATIONAL / ACADEMIC PROJECT ONLY**
> This project uses a **100% synthetic, artificially generated dataset** and demo
> Machine Learning models. It does **NOT** use any real patient data, and its
> outputs (risk scores, recommendations, "Digital Twin" profiles) are **NOT**
> real medical advice, diagnoses, or clinical predictions. This software must
> **never** be used to make real healthcare decisions. Always consult a
> licensed medical professional.

---

## 📌 Overview

This is a complete, end-to-end demonstration application that simulates how
an **AI Digital Twin** could combine:

- OCR-based medical report reading (OpenCV + pytesseract + Regex)
- Machine Learning risk prediction (Scikit-Learn `RandomForestClassifier`)
- A virtual "Digital Twin" patient profile with a rule-based recommendation
- An interactive Streamlit dashboard with Plotly visualizations

for **personalized mRNA vaccine risk screening**, purely for learning
purposes (data science / ML / healthcare-AI coursework, portfolio projects,
demos, etc.).

---

## 🧰 Tech Stack

| Component        | Library         |
|-------------------|-----------------|
| Language           | Python 3.12     |
| Web UI             | Streamlit       |
| Machine Learning   | Scikit-Learn    |
| Data Handling      | Pandas, NumPy   |
| Image Processing   | OpenCV          |
| OCR                | pytesseract     |
| Image I/O          | Pillow          |
| Model Persistence  | Joblib          |
| Charts             | Plotly          |

---

## 📂 Project Structure

```
AI_DigitalTwin_Project/
│
├── app.py                          # Main Streamlit entry point
├── train_model.py                  # Trains & saves the ML models
├── requirements.txt
├── README.md
│
├── dataset/
│   ├── generate_dataset.py         # Generates the synthetic dataset
│   └── vaccine_data.csv            # 5000-row synthetic dataset
│
├── models/
│   ├── allergy_model.pkl           # Trained Allergy_Risk model bundle
│   ├── side_effect_model.pkl       # Trained SideEffect_Risk model bundle
│   └── gender_encoder.pkl          # Shared Gender LabelEncoder
│
├── app_pages/
│   ├── splash.py                    # Splash/landing screen (title + hero image)
│   ├── home.py                      # Home page with navigation cards
│   ├── csv_upload.py                # Batch CSV upload + analysis
│   ├── manual_entry.py              # Manual single-patient entry form
│   ├── medical_report_upload.py     # Image upload + OCR + review form
│   └── dashboard.py                 # Digital Twin results + charts
│
├── utils/
│   ├── preprocessing.py            # OpenCV image preprocessing pipeline
│   ├── ocr.py                      # pytesseract OCR wrapper
│   ├── regex_extractor.py          # Regex parsing of OCR text
│   ├── prediction.py               # Loads models & runs predictions
│   └── digital_twin.py             # Builds the Digital Twin profile
│
├── reports/                        # (optional) place to store generated reports
└── results/                        # (optional) place to store exported results
```

---

## ⚙️ Installation

### 1. Prerequisites
- Python 3.12 installed
- **Tesseract OCR engine** installed on your system (required by `pytesseract`):
  - **Windows**: Download and install from
    https://github.com/UB-Mannheim/tesseract/wiki, then add the install folder
    (e.g. `C:\Program Files\Tesseract-OCR`) to your PATH.
  - **macOS**: `brew install tesseract`
  - **Linux (Debian/Ubuntu)**: `sudo apt-get install tesseract-ocr`

### 2. Clone / Download the project
Place the `AI_DigitalTwin_Project` folder anywhere on your machine, then open
it in **VS Code**.

### 3. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🗂️ Step-by-Step: Running in VS Code

1. Open the `AI_DigitalTwin_Project` folder in VS Code (`File > Open Folder`).
2. Open a new terminal: `Terminal > New Terminal`.
3. Activate your virtual environment (see above) if you created one.
4. Install dependencies: `pip install -r requirements.txt`.
5. (Optional — a dataset & models are already included) Regenerate the
   dataset and retrain models if you want fresh ones (see commands below).
6. Run the app: `streamlit run app.py`.
7. Your browser will open automatically at `http://localhost:8501`.

---

## 🧪 Regenerating the Dataset (optional)

The dataset is already generated and included at `dataset/vaccine_data.csv`.
To regenerate a fresh synthetic dataset (5000 rows):

```bash
python dataset/generate_dataset.py
```

---

## 🤖 Training the ML Models

Pre-trained models are already included in `models/`. To retrain them from
scratch (e.g. after regenerating the dataset):

```bash
python train_model.py
```

This will:
- Load `dataset/vaccine_data.csv`
- Train two `RandomForestClassifier` models (`Allergy_Risk`, `SideEffect_Risk`)
- Print accuracy scores and classification reports for each
- Save the trained model bundles to `models/allergy_model.pkl` and
  `models/side_effect_model.pkl`, plus the shared gender encoder.

---

## ▶️ Running the Application

```bash
streamlit run app.py
```

Then use the **sidebar** to navigate between:
- 🏠 **Home** — project overview
- 📁 **CSV Upload** — batch-analyze multiple patients from a CSV
- ✍️ **Manual Entry** — enter one patient's data manually
- 🖼️ **Medical Report Upload** — upload a lab report image (JPG/JPEG/PNG),
  which is auto-processed with OpenCV + OCR + Regex, then reviewed/edited
  before analysis
- 📊 **Dashboard** — view the Digital Twin card, prediction probabilities,
  risk gauges, and Plotly charts

---

## 🧬 How the Digital Twin Works

1. Patient data (from CSV, manual form, or OCR) is passed to
   `utils/prediction.py`, which loads the trained RandomForest models and
   predicts:
   - **Allergy_Risk**: Low / Medium / High (+ probabilities)
   - **SideEffect_Risk**: Low / Medium / High (+ probabilities)
2. `utils/digital_twin.py` combines both predictions into an **overall risk
   level** (the more severe of the two) and maps it to a recommendation:

   | Overall Risk | Recommendation                         |
   |---------------|------------------------------------------|
   | Low           | Vaccination Recommended                  |
   | Medium        | Vaccinate Under Observation               |
   | High          | Specialist Consultation Required          |

3. The Dashboard renders this as a **Digital Twin card**, with metric cards,
   progress bars, gauges, and comparison bar charts.

---

## 🖼️ OCR Pipeline (Medical Report Upload)

1. **`utils/preprocessing.py`** — OpenCV pipeline: grayscale → resize →
   contrast enhancement (CLAHE) → denoising → Otsu thresholding →
   sharpening.
2. **`utils/ocr.py`** — Runs `pytesseract` on the cleaned image to extract
   raw text.
3. **`utils/regex_extractor.py`** — Uses regex patterns to pull out:
   `PatientName`, `Age`, `Gender`, `ALT`, `AST`, `Creatinine`, `CRP` into a
   dictionary, e.g.:
   ```python
   {
       "PatientName": "Rahul Verma",
       "Age": 45,
       "Gender": "Male",
       "ALT": 47,
       "AST": 42,
       "Creatinine": 1.06,
       "CRP": 19.5
   }
   ```
4. The extracted values are shown in an **editable form** so the user can
   correct any OCR misreads before generating the Digital Twin.

---

## ❗ Troubleshooting

- **`TesseractNotFoundError`**: Tesseract OCR is not installed or not on your
  PATH. Install it (see Prerequisites) and restart your terminal/VS Code.
- **`FileNotFoundError` for model `.pkl` files**: Run `python train_model.py`
  first to generate the model files.
- **`FileNotFoundError` for `vaccine_data.csv`**: Run
  `python dataset/generate_dataset.py` first.
- **Streamlit doesn't open automatically**: Manually visit
  `http://localhost:8501` in your browser.

---

## 📄 License & Ethical Use

This project is provided **strictly for educational and academic purposes**.
It must not be used, in whole or in part, to make real medical, clinical, or
public-health decisions. All data is synthetic; all models are illustrative.

---

## New: camera input, history, and Hindi / Kannada / English results

- **Camera**: on *Medical Report Upload*, choose "Take a photo with camera". The photo goes through the same blur check, OpenCV preprocessing, OCR and editable review form as an uploaded file. (Browsers only allow camera access on `https://` or `localhost`.)
- **History** (new card on Home): every result from Medical Report Upload and Manual Entry is saved — the uploaded/captured image, the values used, the OCR text, the result, and each PDF you download. Files live in `results/` and `reports/`. There is no login, so history is shared by everyone using the same running instance; on hosts with a temporary disk it resets on restart.
- **Languages**: pick English / हिन्दी / ಕನ್ನಡ above any result. The on-screen result and the PDF both follow your choice. PDFs use bundled Noto fonts (`assets/fonts/`) and `fpdf2` + `uharfbuzz` for correct Hindi/Kannada letter shaping (this replaced `reportlab`). Translations are in `utils/i18n.py` — have a native speaker review the wording before real use.
