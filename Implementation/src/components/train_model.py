# =============================================================================
# BC Health Platform - ML Model Training Script
# =============================================================================
# Trains a Random Forest classifier to predict diseases from symptoms.
# Part of the 3-layer hybrid system: OpenAI → Rules → ML (this model)
# =============================================================================

"""
Train a Random Forest classifier on the Kaggle symptom-disease dataset.

Pipeline:
    1. Load symptom_disease_data.csv, symptom_severity.csv, urgency_mapping.csv
    2. Preprocess: strip whitespace, lowercase, remove stray internal spaces
    3. One-hot encode symptoms into binary matrix, then weight by severity
    4. Train/test split: 80/20 stratified by disease
    5. Train Random Forest (100 trees, balanced class weights)
    6. Evaluate: accuracy, classification report, confusion matrix
    7. Save model.pkl + model_metadata.json to Implementation/models/

Usage:
    cd Implementation/src
    python -m components.train_model
"""

import os
import json

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib


# =============================================================================
# PATHS — relative to this script's location (Implementation/src/components/)
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "..", "data")
MODELS_DIR = os.path.join(BASE_DIR, "..", "..", "models")

DISEASE_DATA_PATH = os.path.join(DATA_DIR, "symptom_disease_data.csv")
SEVERITY_DATA_PATH = os.path.join(DATA_DIR, "symptom_severity.csv")
URGENCY_DATA_PATH = os.path.join(DATA_DIR, "urgency_mapping.csv")

MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_symptom(name):
    """
    Normalize a symptom name.

    Handles known data quality issues:
    - Leading/trailing whitespace (e.g., " skin_rash" → "skin_rash")
    - Internal stray spaces (e.g., "dischromic _patches" → "dischromic_patches")
    - Mixed case
    """
    if pd.isna(name) or not str(name).strip():
        return None
    # Strip outer whitespace, lowercase, then remove any remaining spaces
    # so "dischromic _patches" becomes "dischromic_patches"
    return str(name).strip().lower().replace(" ", "")


# =============================================================================
# MAIN TRAINING PIPELINE
# =============================================================================

def main():
    # -------------------------------------------------------------------------
    # STEP 1: Load all 3 datasets
    # -------------------------------------------------------------------------
    print("=" * 60)
    print("BC Health Platform — ML Model Training")
    print("=" * 60)

    print("\n[Step 1/7] Loading datasets...")

    df_disease = pd.read_csv(DISEASE_DATA_PATH)
    print(f"  symptom_disease_data.csv : {df_disease.shape[0]} rows x {df_disease.shape[1]} columns")

    df_severity = pd.read_csv(SEVERITY_DATA_PATH)
    print(f"  symptom_severity.csv     : {df_severity.shape[0]} entries")

    df_urgency = pd.read_csv(URGENCY_DATA_PATH)
    print(f"  urgency_mapping.csv      : {df_urgency.shape[0]} diseases")

    # -------------------------------------------------------------------------
    # STEP 2: Preprocess — clean symptom names and build lookup tables
    # -------------------------------------------------------------------------
    print("\n[Step 2/7] Preprocessing...")

    # Identify the 17 symptom columns
    symptom_cols = [col for col in df_disease.columns if col.startswith("Symptom_")]
    print(f"  Symptom columns found: {len(symptom_cols)}")

    # Clean all symptom values in the disease data
    for col in symptom_cols:
        df_disease[col] = df_disease[col].apply(clean_symptom)

    # Clean the severity lookup: {symptom_name: weight}
    # If a symptom appears twice (e.g., fluid_overload), keep the higher weight
    df_severity["Symptom"] = df_severity["Symptom"].apply(clean_symptom)
    severity_dict = df_severity.groupby("Symptom")["weight"].max().to_dict()
    print(f"  Severity weights loaded: {len(severity_dict)} unique symptoms")

    # Build urgency mapping: {disease_name_lower: urgency_level}
    urgency_dict = {}
    for _, row in df_urgency.iterrows():
        urgency_dict[str(row["Disease"]).strip().lower()] = row["urgency_level"]
    print(f"  Urgency mappings loaded: {len(urgency_dict)} diseases")

    # Collect the master list of all unique symptoms from the disease data
    all_symptoms = set()
    for col in symptom_cols:
        values = df_disease[col].dropna().unique()
        all_symptoms.update(values)
    symptom_list = sorted(all_symptoms)
    print(f"  Unique symptoms after cleaning: {len(symptom_list)}")

    # -------------------------------------------------------------------------
    # STEP 3: One-hot encode symptoms, then multiply by severity weights
    # -------------------------------------------------------------------------
    print("\n[Step 3/7] Building feature matrix (one-hot x severity weights)...")

    # Create a binary matrix: rows = records, columns = symptoms
    feature_matrix = np.zeros((len(df_disease), len(symptom_list)), dtype=np.float64)

    # Map symptom name → column index for fast lookup
    symptom_to_idx = {s: i for i, s in enumerate(symptom_list)}

    for row_idx in range(len(df_disease)):
        for col in symptom_cols:
            symptom = df_disease.at[row_idx, col]
            if symptom and symptom in symptom_to_idx:
                feature_matrix[row_idx, symptom_to_idx[symptom]] = 1.0

    # Multiply each column by its severity weight (default=1 if not found)
    severity_weights = np.array([severity_dict.get(s, 1) for s in symptom_list])
    feature_matrix = feature_matrix * severity_weights

    # Target labels
    labels = df_disease["Disease"].values

    print(f"  Feature matrix shape: {feature_matrix.shape}")
    print(f"  Non-zero features per row (avg): {(feature_matrix > 0).sum(axis=1).mean():.1f}")
    print(f"  Target classes: {len(np.unique(labels))}")

    # -------------------------------------------------------------------------
    # STEP 4: Train-test split (80/20, stratified)
    # -------------------------------------------------------------------------
    print("\n[Step 4/7] Splitting data (80% train / 20% test, stratified)...")

    X_train, X_test, y_train, y_test = train_test_split(
        feature_matrix, labels,
        test_size=0.2,
        stratify=labels,
        random_state=42
    )

    print(f"  Training set: {X_train.shape[0]} samples")
    print(f"  Test set:     {X_test.shape[0]} samples")

    # -------------------------------------------------------------------------
    # STEP 5: Train Random Forest classifier
    # -------------------------------------------------------------------------
    print("\n[Step 5/7] Training Random Forest classifier...")
    print("  Config: 100 trees, balanced class weights, n_jobs=-1")

    model = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)

    print("  Training complete.")

    # -------------------------------------------------------------------------
    # STEP 6: Evaluate the model
    # -------------------------------------------------------------------------
    print("\n[Step 6/7] Evaluating model on test set...")

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    status = "(PASS — meets 70% target)" if accuracy >= 0.70 else "(BELOW 70% target)"
    print(f"\n  Overall Accuracy: {accuracy * 100:.2f}% {status}")

    # Classification report (per-class precision, recall, f1)
    class_names = sorted(np.unique(labels))
    report_text = classification_report(y_test, y_pred, target_names=class_names)
    report_dict = classification_report(
        y_test, y_pred, target_names=class_names, output_dict=True
    )

    print(f"\n  Classification Report:\n")
    print(report_text)

    # Top 5 best and worst performing diseases (by f1-score)
    disease_scores = {
        name: report_dict[name]["f1-score"]
        for name in class_names
        if name in report_dict
    }
    sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)

    print("  Top 5 BEST performing diseases (by F1-score):")
    for name, f1 in sorted_diseases[:5]:
        print(f"    {name:45s} F1={f1:.2f}")

    print("\n  Top 5 WORST performing diseases (by F1-score):")
    for name, f1 in sorted_diseases[-5:]:
        print(f"    {name:45s} F1={f1:.2f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=class_names)
    print(f"\n  Confusion matrix shape: {cm.shape} (saved in metadata)")

    # -------------------------------------------------------------------------
    # STEP 7: Save model and metadata
    # -------------------------------------------------------------------------
    print("\n[Step 7/7] Saving model and metadata...")

    # Create models/ directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Save the trained model
    joblib.dump(model, MODEL_PATH)
    model_size = os.path.getsize(MODEL_PATH)
    print(f"  Saved: {MODEL_PATH}")
    print(f"  Model file size: {model_size / (1024 * 1024):.2f} MB")

    # Build and save metadata JSON
    # This gives the chatbot everything it needs to use the model:
    # - symptom_list: column order for building feature vectors
    # - severity_weights: to weight new inputs the same way
    # - urgency_mapping: to look up urgency after prediction
    # - accuracy & confidence_threshold: for fallback logic
    metadata = {
        "symptom_list": symptom_list,
        "severity_weights": {s: severity_dict.get(s, 1) for s in symptom_list},
        "urgency_mapping": urgency_dict,
        "class_names": class_names,
        "accuracy": round(accuracy, 4),
        "confidence_threshold": 0.70,
        "n_estimators": 100,
        "test_size": 0.2,
        "random_state": 42,
        "n_features": len(symptom_list),
        "n_classes": len(class_names),
        "training_samples": int(X_train.shape[0]),
        "test_samples": int(X_test.shape[0])
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    meta_size = os.path.getsize(METADATA_PATH)
    print(f"  Saved: {METADATA_PATH}")
    print(f"  Metadata file size: {meta_size / 1024:.2f} KB")

    print("\n" + "=" * 60)
    print("Training pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
