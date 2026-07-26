# Mental Health — Anxiety Prevalence Prediction

## Mission & Problem
Mental-health surveillance is uneven — many countries and years lack direct anxiety-disorder data while other indicators are reported more consistently. This project predicts a country's **Anxiety disorder prevalence** (share of population) from its other disorder prevalences, country, and year. A linear-regression pipeline (compared against tree and ensemble models) fills these gaps so analysts can estimate anxiety burden where direct measurement is missing.

## Dataset
- **Source:** Mental Illnesses Prevalence (Our World in Data / IHME GBD) — https://www.kaggle.com/datasets/imtkaggleteam/mental-health
- **Size:** 6,419 rows (214 countries × 30 years, 1990–2019)
- **Target:** `Anxiety` prevalence (%). **Features:** Entity (country, label-encoded), Year, Schizophrenia, Depressive, Bipolar, Eating.

## Live API Endpoint (test via Swagger UI)
Publicly routable URL (not localhost):

- **Swagger UI:** https://linear-regression-model-gako.onrender.com/docs
- **Prediction (POST):** https://linear-regression-model-gako.onrender.com/predict
- **Retraining (POST):** https://linear-regression-model-gako.onrender.com/retrain
- **Health check (GET):** https://linear-regression-model-gako.onrender.com/health

> Hosted on Render free tier — the first request after idle may take ~40–60 seconds while the instance wakes up. Open `/health` once and wait for `{"status":"healthy"}` before testing.

**Example `/predict` request body:**
```json
{
  "Entity": 10,
  "Year": 2014,
  "Schizophrenia": 0.28,
  "Depressive": 2.95,
  "Bipolar": 0.54,
  "Eating": 0.12
}
```
## How to Run the Mobile App
The Flutter app has a single prediction page with 6 input fields, a **Predict** button, and a result area.

1. **Install Flutter** (https://docs.flutter.dev/get-started/install) and confirm setup:
   ```bash
   flutter doctor
   ```
2. **Open the app folder:**
   ```bash
   cd summative/FlutterApp/anxiety_predictor
   ```
3. **Get dependencies:**
   ```bash
   flutter pub get
   ```
4. **Run the app** (pick one):
   ```bash
   flutter run                             # connected device / Android emulator
   flutter run -d windows                  # Windows desktop
   flutter run -d chrome --web-port=8080   # web (fixed port matches CORS)
   ```
5. **Make a prediction:** enter values within the allowed ranges, then tap **Predict**.

   | Field | Range |
   |---|---|
   | Country Code (Entity) | 0–213 (see `summative/API/country_codes.json`) |
   | Year | 1990–2019 |
   | Schizophrenia (%) | 0.0–1.0 |
   | Depressive (%) | 0.0–10.0 |
   | Bipolar (%) | 0.0–3.0 |
   | Eating (%) | 0.0–3.0 |

   The result box shows the predicted anxiety prevalence, or an error if a value is out of range or missing.

> The app already points at the live API above. To repoint it, edit `apiUrl` in `summative/FlutterApp/anxiety_predictor/lib/main.dart`.

---

## Visualizations

**Correlation heatmap** — Bipolar (0.58) and Eating (0.59) correlate most strongly with Anxiety; Schizophrenia is moderate (0.30); Depressive is weak (0.11).

![Correlation Heatmap](summative/linear_regression/correlation_heatmap.png)

**Distributions** — anxiety prevalence is right-skewed, continuous, and well-suited as a regression target.

![Distributions](summative/linear_regression/distributions.png)

**Scatterplots vs Anxiety** — Bipolar and Eating rise together with Anxiety, showing usable linear structure.

![Scatterplots](summative/linear_regression/scatterplots.png)

**Loss curve (train vs test)** and **before/after best-fit line:**

![Loss Curve](summative/linear_regression/loss_curve.png)
![Before & After](summative/linear_regression/scatter_before_after.png)

**Model comparison:**

![Model Comparison](summative/linear_regression/model_comparison.png)

## Features & Encoding

| Column | Role | Notes |
|---|---|---|
| Entity (country) | Feature (categorical) | **Label-encoded** to integers 0–213 — the column converted to numeric. Mapping in `country_codes.json`. |
| Code (ISO) | **Dropped** | Redundant duplicate of Entity, and the only source of missing values. |
| Year | Feature (numeric) | 1990–2019; temporal trend. |
| Schizophrenia / Depressive / Bipolar / Eating | Features (numeric) | Prevalence, share of population (%). |
| **Anxiety** | **Target** | Prevalence (%) — the value predicted. |

All features are standardized with `StandardScaler` (fit on the training set only).

## Models Trained

| Model | Test RMSE | Test R2 |
|---|---|---|
| Linear Regression (SGD / Gradient Descent) | 0.800 | 0.426 |
| Linear Regression (OLS) | 0.773 | 0.464 |
| Decision Tree | 0.230 | 0.952 |
| **Random Forest (best, saved)** | **0.155** | **0.979** |

**Best model (lowest RMSE): Random Forest** — saved as `best_model.pkl`. The linear models underperform because country-level prevalence is highly non-linear across the 214 encoded entities, which the ensemble captures far better.

### CORS configuration & reasoning
Uses `CORSMiddleware` with an **explicit allow-list**, not the wildcard `*`.
- **Allowed origins:** the deployed Render URL and localhost (Flutter web dev), so Swagger UI and legitimate front-ends can reach the API.
- **Restricted:** all other origins — the browser same-origin policy blocks unknown third-party sites from calling the API on a user's behalf (prevents CSRF-style abuse).
- **Methods:** only `GET` (health) and `POST` (predict/retrain). **Headers:** `Content-Type`, `Authorization`, `Accept`. **Credentials:** allowed, so auth headers survive if authentication is added later.

## How to Run the Notebook
```bash
cd summative/linear_regression
jupyter notebook multivariate.ipynb    # Kernel > Restart and Run All
python predict.py                      # single prediction using the saved model
```

## Technologies
Python, Jupyter, pandas, numpy, matplotlib, seaborn, scikit-learn (SGDRegressor, LinearRegression, DecisionTreeRegressor, RandomForestRegressor, StandardScaler, LabelEncoder), joblib, FastAPI, Uvicorn, Pydantic, Flutter/Dart, Render.
