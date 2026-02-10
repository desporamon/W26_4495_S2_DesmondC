# W26_4495_S2_DesmondC

## 📋 Project Information

| Field | Details |
|-------|---------|
| **Project Name** | BC Personal Health Management Platform |
| **Student Name** | Desmond Chua |
| **Student ID** | 300369803 |
| **Email** | chuad1@student.douglascollege.ca |
| **Course** | CSIS 4495 - Applied Research Project |
| **Section** | 2 |
| **Instructor** | Prof. Padmapriya Arasanipalai Kandhadai |
| **Term** | Winter 2026 |

---

# 🏥 BC Personal Health Management Platform

**CSIS 4495 Applied Research Project - Douglas College**

---

## 📍 Overview

A comprehensive healthcare navigation assistant for British Columbia residents featuring AI-powered symptom assessment, personalized health dashboards, and healthcare facility mapping. The platform uses a **hybrid Rule-Based + Machine Learning approach** to provide safe, accurate health guidance while connecting users with appropriate BC healthcare resources.

---

## ❗ Problem Statement

British Columbia residents face challenges navigating the healthcare system:

- **Uncertainty** – Difficulty determining urgency of symptoms and appropriate care level
- **Accessibility** – Limited awareness of nearby healthcare facilities and services
- **Information Overload** – Scattered health resources without personalized guidance
- **Wait Times** – Unnecessary ER visits for non-emergency conditions

BC Health Platform addresses these issues through an intelligent, user-friendly assistant that provides personalized health guidance while respecting clinical safety standards.

---

## ✨ Key Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **AI-Powered Symptom Assessment** | Hybrid Rule-Based + ML classification with OpenAI integration for natural conversation |
| 2 | **Personal Health Dashboard** | Track and visualize personal health metrics with interactive charts |
| 3 | **BC Healthcare Facility Finder** | Locate nearby hospitals, clinics, walk-ins, and pharmacies |
| 4 | **Health Education Resources** | Curated BC-specific health information from HealthLinkBC |
| 5 | **System Analytics Dashboard** | Usage patterns, health trends, and ML-powered insights |

---

## 🔬 Technical Approach

### Hybrid Classification System
```
User Input → OpenAI NLP → Rule-Based Safety Check (CTAS) → ML Classifier → Output
                                    ↓
                            Critical Symptom?
                              ↓         ↓
                            YES        NO
                              ↓         ↓
                        Emergency    ML Assessment
                        (Call 911)   (Urgency Level)
```

- **Layer 1:** OpenAI API for natural language understanding
- **Layer 2:** Rule-based logic for critical symptom detection (CTAS guidelines)
- **Layer 3:** Random Forest ML classifier for urgency prediction

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Platform** | Streamlit Cloud |
| **Language** | Python 3.10+ |
| **ML/NLP** | scikit-learn, NLTK, spaCy |
| **AI Integration** | OpenAI API (GPT-4) |
| **Visualization** | Power BI, Plotly |
| **Database** | SQLite |
| **Version Control** | GitHub |
| **Data Sources** | Kaggle, HealthLinkBC, CTAS Guidelines |

---

## 📁 Repository Structure
```
W26_4495_S2_DesmondC/
│
├── DocumentsAndReports/
│   ├── final-report/           # Final report & documentation
│   ├── midterm/                # Midterm report & demo video
│   ├── progress-reports/       # Weekly progress reports
│   ├── proposal/               # Project proposal
│   └── worklog/                # Work hours tracking (Excel)
│
├── Implementation/
│   ├── data/                   # Datasets (raw & processed)
│   │   └── health_platform.db  # SQLite database
│   ├── notebooks/              # Jupyter notebooks for exploration
│   ├── samples/                # Proof of concept code
│   ├── src/                    # Source code (Streamlit app)
│   │   ├── .streamlit/         # Streamlit configuration
│   │   │   └── config.toml     # Theme colors (VCH teal)
│   │   ├── components/         # Reusable Python modules
│   │   │   ├── auth.py         # Authentication (login, register, bcrypt)
│   │   │   ├── chatbot.py      # Chatbot logic & conversation flow
│   │   │   ├── database.py     # SQLite CRUD functions
│   │   │   ├── openai_utils.py # OpenAI API integration
│   │   │   └── rules.py        # CTAS rule-based safety checks
│   │   ├── models/             # Trained ML models (.pkl files)
│   │   ├── pages/              # Streamlit multi-page app
│   │   │   ├── 1_🏠_Home.py
│   │   │   ├── 2_💬_Symptom_Assessment.py
│   │   │   ├── 3_📊_My_Dashboard.py
│   │   │   ├── 4_🗺️_Facility_Finder.py
│   │   │   ├── 5_📚_Health_Library.py
│   │   │   └── 6_📈_System_Analytics.py
│   │   └── app.py              # Main Streamlit application
│   └── tests/                  # Unit tests
│
├── Misc/                       # Miscellaneous resources
│   ├── design/                 # UI mockups (UX Pilot)
│   └── learning-notes/         # Study materials, certificates, notes
│
├── .gitignore
└── README.md
```
---

## 📊 Data Sources

| Dataset | Source | Files | Purpose |
|---------|--------|-------|---------|
| **Disease Symptom Prediction** | [Kaggle (itachi9604)](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) | `symptom_disease_data.csv`, `symptom_severity.csv`, `symptom_description.csv`, `symptom_precaution.csv` | ML model training & Health Library |
| **CTAS Guidelines** | Canadian Triage and Acuity Scale (2008) | Rule-based logic in `rules.py` | Emergency symptom detection |
| **HealthLinkBC** | [healthlinkbc.ca](https://www.healthlinkbc.ca) | Referenced in app | Health education content |

---

## 🗓️ Project Timeline

| Phase | Duration | Milestone | Due Date |
|-------|----------|-----------|----------|
| **Phase 1** | Jan 13 - Feb 9 | Proposal Submission | Jan 26, 2026 |
| **Phase 2** | Feb 10 - Mar 9 | Midterm Report & Demo | Feb 23, 2026 |
| **Phase 3** | Mar 10 - Mar 30 | Check-in #2 | Mar 27, 2026 |
| **Phase 4** | Mar 31 - Apr 14 | Final Report & Presentation | Apr 8-14, 2026 |

**Total Duration:** 13 weeks | **Total Effort:** 144 hours

---

## 📈 Expected Outcomes

- **Deployable Web App:** Fully functional Streamlit application on Streamlit Cloud
- **Hybrid AI System:** OpenAI + Rule-Based + ML classification pipeline
- **Interactive Dashboards:** Power BI embedded analytics and Plotly visualizations
- **Healthcare Integration:** BC facility data and HealthLinkBC resources
- **Documentation:** Complete technical documentation and user guide

---

## 📌 License

This project is part of **CSIS 4495 Applied Research Project** at **Douglas College**.

© 2026 Desmond Chua. All rights reserved.
