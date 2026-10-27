"""
Step 3: the model service (a small REST API).

Run:  uvicorn app:app --port 8000
Docs: http://localhost:8000/docs   (try the API in your browser)

Endpoints:
  GET  /health    is the service up?
  GET  /options   allowed values for the drop-down fields (purpose, state, ...)
  GET  /metrics   evaluation results produced by train.py
  POST /predict   score one loan application, explain it and suggest a price
"""
import json
from pathlib import Path

import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import economics
from data import load_categories, to_model_input
from features import CATEGORICAL_FEATURES, FEATURE_LABELS, FEATURES, TARGET_MARGIN

MODEL_DIR = Path(__file__).parent / "model"

app = FastAPI(title="Credit Risk Model Service")

model = xgb.XGBClassifier()
model.load_model(MODEL_DIR / "xgboost_model.json")
categories = load_categories(MODEL_DIR / "categories.json")
metrics_data = json.loads((MODEL_DIR / "metrics.json").read_text())

# Decision rule: below the profit-optimal threshold -> approve; a band of 10 points
# above it -> a loan officer looks at it; anything riskier -> decline.
APPROVE_BELOW = metrics_data["approval_threshold"]
DECLINE_FROM = APPROVE_BELOW + 0.10


class LoanApplication(BaseModel):
    """One loan application. Field names match the dataset columns."""
    loan_amnt: float = Field(gt=0, le=100000)
    term_months: int = Field(description="36 or 60")
    emp_length: float = Field(ge=0, le=10)
    annual_inc: float = Field(gt=0)
    dti: float = Field(ge=0, le=100)
    delinq_2yrs: int = Field(ge=0, le=50)
    revol_util: float = Field(ge=0, le=200)
    total_acc: int = Field(ge=0, le=200)
    longest_credit_length: float = Field(ge=0, le=80)
    home_ownership: str
    purpose: str
    verification_status: str
    addr_state: str


class Factor(BaseModel):
    feature: str
    label: str
    value: str
    impact: float  # SHAP value: > 0 pushes risk up, < 0 pushes risk down


class Prediction(BaseModel):
    probability_of_default: float
    decision: str
    expected_loss: float           # USD, PD x LGD x amount
    break_even_rate: float         # % interest at which expected profit is zero
    suggested_interest_rate: float | None  # break-even plus the target margin; None if declined
    top_factors: list[Factor]


def decide(probability: float) -> str:
    if probability < APPROVE_BELOW:
        return "APPROVE"
    if probability < DECLINE_FROM:
        return "MANUAL_REVIEW"
    return "DECLINE"


def check_categories(application: LoanApplication) -> None:
    if application.term_months not in (36, 60):
        raise HTTPException(422, "term_months must be 36 or 60")
    for column in CATEGORICAL_FEATURES:
        value = getattr(application, column)
        if value not in categories[column]:
            raise HTTPException(422, f"{column} must be one of {categories[column]}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/options")
def options():
    return categories


@app.get("/metrics")
def metrics():
    return metrics_data


@app.post("/predict", response_model=Prediction)
def predict(application: LoanApplication):
    check_categories(application)
    row = to_model_input(pd.DataFrame([application.model_dump()]), categories)
    probability = float(model.predict_proba(row)[0, 1])

    # SHAP values from XGBoost's built-in TreeSHAP, one per input feature.
    # The last column is the base value (average prediction), so we drop it. Values are in log-odds.
    contributions = model.get_booster().predict(
        xgb.DMatrix(row, enable_categorical=True), pred_contribs=True)[0][:-1]

    factors = [
        Factor(feature=name, label=FEATURE_LABELS[name],
               value=str(getattr(application, name)), impact=round(float(impact), 4))
        for name, impact in zip(FEATURES, contributions)
    ]
    factors.sort(key=lambda f: abs(f.impact), reverse=True)

    break_even = economics.break_even_rate(probability, application.term_months)
    decision = decide(probability)
    return Prediction(
        probability_of_default=round(probability, 4),
        decision=decision,
        expected_loss=round(float(economics.expected_loss(probability, application.loan_amnt)), 2),
        break_even_rate=round(break_even, 2),
        suggested_interest_rate=None if decision == "DECLINE" else round(break_even + TARGET_MARGIN * 100, 2),
        top_factors=factors[:5],
    )
