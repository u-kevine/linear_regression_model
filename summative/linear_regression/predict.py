"""
predict.py
──────────
Uses the saved best model (best_model.pkl) and scaler (scaler.pkl) to predict
a country's Anxiety disorder prevalence from a single input sample.

This logic is reused by the API in Task 2.

Usage:
    python predict.py
"""

import joblib
import pandas as pd

# Load saved model and scaler
model  = joblib.load('best_model.pkl')
scaler = joblib.load('scaler.pkl')

# Column order must match training
FEATURE_COLUMNS = ['Entity', 'Year', 'Schizophrenia', 'Depressive', 'Bipolar', 'Eating']

# Example input (Entity is the label-encoded country code, 0-213)
sample = {
    'Entity'        : 10,      # country code — see country_codes.json
    'Year'          : 2014,
    'Schizophrenia' : 0.28,
    'Depressive'    : 2.95,
    'Bipolar'       : 0.54,
    'Eating'        : 0.12,
}


def predict_anxiety_prevalence(input_dict: dict) -> float:
    """Scale the input and return the predicted Anxiety prevalence."""
    input_df = pd.DataFrame([input_dict], columns=FEATURE_COLUMNS)
    input_scaled = scaler.transform(input_df)
    prediction = model.predict(input_scaled)[0]
    return round(float(prediction), 3)


if __name__ == '__main__':
    predicted = predict_anxiety_prevalence(sample)
    print('=== Anxiety Prevalence Prediction ===')
    print(f'Input sample: {sample}')
    print(f'Predicted Anxiety prevalence: {predicted}%')
