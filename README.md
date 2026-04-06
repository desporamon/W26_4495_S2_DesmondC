# W26_4495_S2_DesmondC

## Project Information

| Field | Details |
|-------|---------|
| **Project Name** | CedarCare — AI Health Navigation Platform |
| **Student Name** | Desmond Chua |
| **Student ID** | 300369803 |
| **Email** | chuad1@student.douglascollege.ca |
| **Course** | CSIS 4495 - Applied Research Project |
| **Section** | 2 |
| **Instructor** | Prof. Padmapriya Arasanipalai Kandhadai |
| **Term** | Winter 2026 |

---

# CedarCare — AI Health Navigation Platform for British Columbia

**Live deployment:** https://cedarcare.streamlit.app  
**Test account:** test@test.com / Password123

---

## What This Project Does

CedarCare helps BC residents figure out what to do when they feel unwell. A user describes their symptoms in plain language. The platform extracts structured medical data using GPT-4o-mini, runs it through 14 deterministic CTAS emergency rules, and classifies it with a trained Random Forest model across 41 disease categories. If the model confidence falls below 70%, the system falls back to OpenAI for general health guidance rather than forcing an uncertain prediction.

Beyond symptom assessment, the platform includes a personal health dashboard, a BC facility finder with an interactive Folium map, a health education library sourced from HealthLinkBC, and a system analytics dashboard with K-Means patient segmentation. Everything runs in a single Python stack — no separate frontend or backend API layer.

---

## Problem Statement

With 895,000 BC residents lacking a family doctor and no Canadian-built AI symptom checker available since Babylon's collapse in 2023, there is no accessible tool that combines clinical triage with BC-specific care navigation.

CedarCare addresses three specific gaps:
- People do not know whether their symptoms warrant a 911 call, ER visit, walk-in clinic, or home care
- No digital tool connects triage output to actual BC facilities nearby
- No consumer health app offers longitudinal symptom tracking for individuals without a family doctor

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Symptom Assessment Chatbot** | Three-layer pipeline: GPT-4o-mini NLP extraction, CTAS rule-based safety check, Random Forest ML classification |
| **Personal Health Dashboard** | Assessment history, urgency trends, symptom breakdown, Plotly charts |
| **BC Facility Finder** | Interactive Folium map with hospital, walk-in, and urgent care locations |
| **Health Education Library** | 18 articles across 8 categories sourced from HealthLinkBC |
| **System Analytics Dashboard** | K-Means patient segmentation, population health trends, BC Health Authority breakdown |

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Web Framework** | Streamlit 1.41+ | Python-native UI — no separate frontend or backend API required |
| **Language Model** | OpenAI GPT-4o-mini | NLP symptom extraction and fallback guidance |
| **ML — Supervised** | scikit-learn RandomForestClassifier | Disease classification with 70% confidence threshold |
| **ML — Unsupervised** | scikit-learn KMeans + StandardScaler | Patient segmentation across 3 behavioural clusters |
| **Data Layer** | SQLite + bcrypt | Embedded database, password hashing |
| **Visualisation** | Plotly + Folium | Interactive charts and BC facility maps |
| **Testing** | pytest + Hypothesis | 95 automated tests: unit, integration, UI, property-based |
| **CI/CD** | GitHub Actions | Automated pipeline on push to main, Ubuntu 22.04, Python 3.11 |
| **Deployment** | Streamlit Community Cloud | Live at cedarcare.streamlit.app |

---

## Why Streamlit

This project is data-science-first. Choosing React + FastAPI would have required maintaining a separate frontend build, a REST API layer, and two deployment pipelines. Streamlit runs the UI, the ML models, the OpenAI API calls, and the SQLite database in the same Python process. For a solo capstone focused on ML pipeline architecture rather than web infrastructure, that tradeoff was deliberate and appropriate.

---

## Quick Start (Live — No Installation Required)

| Field | Value |
|-------|-------|
| **URL** | https://cedarcare.streamlit.app |
| **Email** | test@test.com |
| **Password** | Password123 |

---

## Installation (Local Development)

**Prerequisites:** Python 3.11, Git, OpenAI API key

**1. Clone the repository**
```bash
git clone https://github.com/desporamon/W26_4495_S2_DesmondC.git
cd BC-Health-Platform
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure OpenAI API key**

Create `Implementation/src/.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-your-key-here"
```

**5. Seed the database**
```bash
cd Implementation/src
python seed_db.py
```

**6. Run the application**
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser. Use test@test.com / Password123 or register a new account.

---

## Running the Test Suite

```bash
# Full suite — 95 tests (unit, integration, UI, property-based)
cd BC-Health-Platform
pytest tests/ -v --tb=short

# CI subset — 79 tests (matches GitHub Actions pipeline)
pytest tests/ -v --ignore=tests/ui
```

Note: UI AppTests must be run from the `Implementation/src/` working directory due to relative asset path dependencies.

---

## Repository Structure

```
W26_4495_S2_DesmondC/
├── DocumentsAndReports/
│   ├── final-report/               # Final report and documentation
│   ├── progress-reports/           # Sprint progress reports (PR1-PR6)
│   ├── proposal/                   # Project proposal
│   └── worklog/                    # Work hours log (Excel)
├── Implementation/
│   ├── data/                       # SQLite database and synthetic CSV dataset
│   ├── models/                     # model.pkl and model_metadata.json
│   ├── notebooks/                  # EDA and model training Jupyter notebooks
│   └── src/
│       ├── components/             # auth, chatbot, database, rules, openai_utils
│       ├── pages/                  # 6 Streamlit pages
│       ├── app.py                  # Application entry point
│       └── seed_db.py              # Seeds test account on fresh deployment
├── tests/
│   ├── unit/                       # test_auth, test_ctas_rules, test_database, test_ml_model
│   ├── integration/                # test_pipeline, test_chatbot_scenarios
│   ├── ui/                         # test_dashboard_apptest, test_chatbot_apptest
│   └── property/                   # test_fuzz_hypothesis
└── .github/
    └── workflows/
        └── ci.yml                  # GitHub Actions CI pipeline
```

---

## Data Sources

| Source | Purpose |
|--------|---------|
| Kaggle — Disease Symptom Prediction dataset | ML model training (4,920 records, 41 diseases, 131 symptoms) |
| CTAS Guidelines (Bullard et al., 2008) | 14 deterministic emergency detection rules |
| HealthLinkBC | Health education library content (18 articles) |

---

## Project Stats

| Metric | Value |
|--------|-------|
| **Automated tests** | 95 (unit, integration, UI, property-based) |
| **CTAS emergency rules** | 14 |
| **Disease categories** | 41 |
| **Health education articles** | 18 |
| **Development effort** | 185.35 hours across 8 sprints |
| **Project period** | Jan 27 – Apr 6, 2026 |

---

## License

CSIS 4495 Applied Research Project — Douglas College  
Desmond Chua (300369803) — Winter 2026  
All rights reserved.
