"""Run from the ml-service folder:  python -m pytest"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

GOOD_PAYER = {
    "LIMIT_BAL": 200000, "EDUCATION": 1, "MARRIAGE": 2, "AGE": 35,
    "PAY_0": -1, "PAY_2": -1, "PAY_3": -1, "PAY_4": -1, "PAY_5": -1, "PAY_6": -1,
    "BILL_AMT1": 5000, "BILL_AMT2": 4000, "BILL_AMT3": 3000,
    "BILL_AMT4": 3000, "BILL_AMT5": 2000, "BILL_AMT6": 2000,
    "PAY_AMT1": 5000, "PAY_AMT2": 4000, "PAY_AMT3": 3000,
    "PAY_AMT4": 3000, "PAY_AMT5": 2000, "PAY_AMT6": 2000,
}

LATE_PAYER = {**GOOD_PAYER,
              "LIMIT_BAL": 20000, "PAY_0": 3, "PAY_2": 2, "PAY_3": 2,
              "PAY_4": 2, "PAY_5": 2, "PAY_6": 2,
              "PAY_AMT1": 0, "PAY_AMT2": 0, "PAY_AMT3": 0}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_predict_returns_probability_and_explanation():
    body = client.post("/predict", json=GOOD_PAYER).json()
    assert 0 <= body["probability_of_default"] <= 1
    assert body["decision"] in {"APPROVE", "MANUAL_REVIEW", "DECLINE"}
    assert len(body["top_factors"]) == 5


def test_late_payer_is_riskier_than_good_payer():
    good = client.post("/predict", json=GOOD_PAYER).json()
    late = client.post("/predict", json=LATE_PAYER).json()
    assert late["probability_of_default"] > good["probability_of_default"]


def test_invalid_input_is_rejected():
    response = client.post("/predict", json={**GOOD_PAYER, "AGE": 5})
    assert response.status_code == 422
