# Test script - verifies model loads correctly and produces valid predictions
# Tests: chest_pain + vomiting → expects Heart attack (Emergency) with confidence check

import joblib, json, numpy as np

model = joblib.load('../models/model.pkl')
meta = json.load(open('../models/model_metadata.json'))

symptoms = meta['symptom_list']
sev = meta['severity_weights']

# Simulate patient with chest_pain and vomiting
X = np.zeros(len(symptoms))
for s in ['chest_pain', 'vomiting']:
    if s in symptoms:
        X[symptoms.index(s)] = sev.get(s, 1)

proba = model.predict_proba([X])[0]
idx = np.argmax(proba)
disease = model.classes_[idx]
confidence = proba[idx]
urgency = meta['urgency_mapping'].get(disease.lower(), 'Unknown')

print(f'Disease: {disease}')
print(f'Confidence: {confidence:.1%}')
print(f'Urgency: {urgency}')
print(f'Above threshold: {confidence >= 0.70}')