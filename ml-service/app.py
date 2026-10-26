"""
Step 3: the model service (a small REST API).

Run:  uvicorn app:app --port 8000
Docs: http://localhost:8000/docs   (try the API in your browser)

Endpoints:
  GET  /health    is the service up and the model loaded?
  GET  /metrics   evaluation results produced by train.py
  POST /predict   score one applicant and explain the score
"""
import json
from pathlib import Path

import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from features import FEATURE_LABELS, FEATURES

MODEL_DIR = Path(__file__).parent / "model"

# Decision rule: probability of default -> recommendation for the loan officer.
APPROVE_BELOW = 0.30
DECLINE_FROM = 0.50

app = FastAPI(title="Credit Risk Model Service")

model = xgb.XGBClassifier()
model.load_model(MODEL_DIR / "xgboost_model.json")


class Applicant(BaseModel):
    """One credit card customer. Field names match the UCI dataset columns."""
    LIMIT_BAL: float = Field(gt=0)
    EDUCATION: int = Field(ge=1, le=4)
    MARRIAGE: int = Field(ge=1, le=3)
    AGE: int = Field(ge=18, le=100)
    PAY_0: int = Field(ge=-2, le=9)
    PAY_2: int = Field(ge=-2, le=9)
    PAY_3: int = Field(ge=-2, le=9)
    PAY_4: int = Field(ge=-2, le=9)
    PAY_5: int = Field(ge=-2, le=9)
    PAY_6: int = Field(ge=-2, le=9)
    BILL_AMT1: float
    BILL_AMT2: float
    BILL_AMT3: float
    BILL_AMT4: float
    BILL_AMT5: float
    BILL_AMT6: float
    PAY_AMT1: float = Field(ge=0)
    PAY_AMT2: float = Field(ge=0)
    PAY_AMT3: float = Field(ge=0)
    PAY_AMT4: float = Field(ge=0)
    PAY_AMT5: float = Field(ge=0)
    PAY_AMT6: float = Field(ge=0)


class Factor(BaseModel):
    feature: str
    label: str
    value: float
    impact: float  # SHAP value: > 0 pushes risk up, < 0 pushes risk down


class Prediction(BaseModel):
    probability_of_default: float
    decision: str
    top_factors: list[Factor]


def decide(probability: float) -> str:
    if probability < APPROVE_BELOW:
        return "APPROVE"
    if probability < DECLINE_FROM:
        return "MANUAL_REVIEW"
    return "DECLINE"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    metrics_file = MODEL_DIR / "metrics.json"
    if not metrics_file.exists():
        raise HTTPException(404, "Run train.py first")
    return json.loads(metrics_file.read_text())


@app.post("/predict", response_model=Prediction)
def predict(applicant: Applicant):
    row = pd.DataFrame([applicant.model_dump()])[FEATURES]
    probability = float(model.predict_proba(row)[0, 1])

    # SHAP values from XGBoost's built-in TreeSHAP. The last column is the
    # base value (average prediction), so we drop it. Values are in log-odds.
    contributions = model.get_booster().predict(
        xgb.DMatrix(row), pred_contribs=True)[0][:-1]

    factors = [
        Factor(feature=name, label=FEATURE_LABELS[name],
               value=float(row.iloc[0][name]), impact=round(float(impact), 4))
        for name, impact in zip(FEATURES, contributions)
    ]
    factors.sort(key=lambda f: abs(f.impact), reverse=True)

    return Prediction(
        probability_of_default=round(probability, 4),
        decision=decide(probability),
        top_factors=factors[:5],
    )
