from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import numpy as np
import pandas as pd
import os
import io

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Mental Health Anxiety Prevalence Predictor",
    description="Predicts a country's Anxiety disorder prevalence (share of "
                "population) from its other mental-health indicators, year, and "
                "country code.",
    version="1.0.0"
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
# Explicit allow-list — NOT the wildcard "*".
#
# ALLOWED:
#   - localhost variants -> local development of the Flutter web build
#   - the deployed Render URL of this service -> so Swagger UI and browser
#     clients served from that domain can reach /predict
# RESTRICTED:
#   - all other origins are blocked by the browser same-origin policy, which
#     stops unknown third-party sites from calling this API on a user's behalf.
# METHODS: only GET (health) and POST (predict / retrain) are used.
# HEADERS: limited to the ones the client actually sends.
# CREDENTIALS: allowed so auth headers survive if authentication is added later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://mental-health-anxiety-predictor.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ── Load model and scaler ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, "best_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# ── Input schema with Pydantic ─────────────────────────────────────────────────
# Each field has: type enforcement + realistic range constraint + description.
# Ranges reflect the actual training-data bounds.
class PrevalenceInput(BaseModel):
    Entity: int = Field(
        ..., ge=0, le=213,
        description="Country code (0-213). See country_codes.json for the mapping."
    )
    Year: int = Field(
        ..., ge=1990, le=2019,
        description="Year of observation (1990-2019)."
    )
    Schizophrenia: float = Field(
        ..., ge=0.0, le=1.0,
        description="Schizophrenia disorder prevalence, share of population (%)."
    )
    Depressive: float = Field(
        ..., ge=0.0, le=10.0,
        description="Depressive disorder prevalence, share of population (%)."
    )
    Bipolar: float = Field(
        ..., ge=0.0, le=3.0,
        description="Bipolar disorder prevalence, share of population (%)."
    )
    Eating: float = Field(
        ..., ge=0.0, le=3.0,
        description="Eating disorder prevalence, share of population (%)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "Entity": 10,
                "Year": 2014,
                "Schizophrenia": 0.28,
                "Depressive": 2.95,
                "Bipolar": 0.54,
                "Eating": 0.12
            }
        }

# ── Feature column order (must match training) ────────────────────────────────
FEATURE_COLUMNS = ["Entity", "Year", "Schizophrenia", "Depressive", "Bipolar", "Eating"]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"message": "Anxiety Prevalence Prediction API is running. Visit /docs for Swagger UI."}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict", tags=["Prediction"])
def predict(data: PrevalenceInput):
    """
    Predict a country's Anxiety disorder prevalence (share of population)
    from the input features. Returns the predicted value as a float.
    """
    try:
        input_dict = data.dict()
        input_df = pd.DataFrame([input_dict], columns=FEATURE_COLUMNS)
        input_scaled = scaler.transform(input_df)
        prediction = model.predict(input_scaled)[0]
        return {
            "predicted_anxiety_prevalence": round(float(prediction), 3),
            "input_received": input_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrain", tags=["Model Update"])
async def retrain(file: UploadFile = File(...)):
    """
    Upload a new CSV to retrain the model. The CSV must contain the same
    columns as the original dataset (Entity, Year, and the disorder columns
    including Anxiety as the target). Triggers retraining automatically.
    """
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error
        import warnings
        warnings.filterwarnings("ignore")

        contents = await file.read()
        new_df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        # Normalize long OWID column names to short ones if present
        rename_map = {}
        for col in new_df.columns:
            low = col.lower()
            if "schizophrenia" in low: rename_map[col] = "Schizophrenia"
            elif "depressive" in low:  rename_map[col] = "Depressive"
            elif "anxiety" in low:     rename_map[col] = "Anxiety"
            elif "bipolar" in low:     rename_map[col] = "Bipolar"
            elif "eating" in low:      rename_map[col] = "Eating"
        new_df = new_df.rename(columns=rename_map)

        # Drop redundant Code column if present
        if "Code" in new_df.columns:
            new_df = new_df.drop(columns=["Code"])

        # Encode the categorical Entity column
        if "Entity" in new_df.columns and new_df["Entity"].dtype == object:
            le = LabelEncoder()
            new_df["Entity"] = le.fit_transform(new_df["Entity"].astype(str))

        # Drop any remaining non-numeric columns defensively
        new_df = new_df.select_dtypes(include=[np.number])

        if "Anxiety" not in new_df.columns:
            raise ValueError("Uploaded CSV must contain an 'Anxiety' target column.")

        X = new_df.drop(columns=["Anxiety"])
        y = new_df["Anxiety"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        new_scaler = StandardScaler()
        X_train_scaled = new_scaler.fit_transform(X_train)
        X_test_scaled  = new_scaler.transform(X_test)

        new_model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )
        new_model.fit(X_train_scaled, y_train)

        preds = new_model.predict(X_test_scaled)
        rmse  = np.sqrt(mean_squared_error(y_test, preds))

        joblib.dump(new_model,  MODEL_PATH)
        joblib.dump(new_scaler, SCALER_PATH)

        global model, scaler
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)

        return {
            "message": "Model retrained and updated successfully.",
            "new_data_rows": len(new_df),
            "retrain_rmse": round(rmse, 4)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")
