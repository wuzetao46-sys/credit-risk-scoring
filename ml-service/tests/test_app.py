"""Run from the ml-service folder:  python -m pytest"""
from fastapi.testclient import TestClient

import economics
from app import app

client = TestClient(app)

LOW_RISK = {
    "loan_amnt": 8000, "term_months": 36, "emp_length": 10, "annual_inc": 120000,
    "dti": 5, "delinq_2yrs": 0, "revol_util": 10, "total_acc": 30,
    "longest_credit_length": 20, "home_ownership": "MORTGAGE",
    "purpose": "credit_card", "verification_status": "verified", "addr_state": "CA",
}

HIGH_RISK = {**LOW_RISK,
             "loan_amnt": 30000, "term_months": 60, "emp_length": 0, "annual_inc": 25000,
             "dti": 30, "delinq_2yrs": 3, "revol_util": 95, "total_acc": 5,
             "longest_credit_length": 3, "home_ownership": "RENT", "purpose": "small_business"}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_options_list_the_categories():
    options = client.get("/options").json()
    assert "debt_consolidation" in options["purpose"]
    assert "CA" in options["addr_state"]


def test_predict_returns_probability_explanation_and_price():
    body = client.post("/predict", json=LOW_RISK).json()
    assert 0 <= body["probability_of_default"] <= 1
    assert body["decision"] in {"APPROVE", "MANUAL_REVIEW", "DECLINE"}
    assert len(body["top_factors"]) == 5
    assert body["suggested_interest_rate"] > body["break_even_rate"]


def test_high_risk_applicant_is_riskier_and_pays_more():
    low = client.post("/predict", json=LOW_RISK).json()
    high = client.post("/predict", json=HIGH_RISK).json()
    assert high["probability_of_default"] > low["probability_of_default"]
    assert high["break_even_rate"] > low["break_even_rate"]
    assert high["decision"] == "DECLINE" and high["suggested_interest_rate"] is None


def test_unknown_category_is_rejected():
    response = client.post("/predict", json={**LOW_RISK, "purpose": "holiday_on_mars"})
    assert response.status_code == 422


def test_break_even_rate_gives_zero_expected_profit():
    pd_, term, amount = 0.2, 36, 10000
    rate = economics.break_even_rate(pd_, term)
    profit = (1 - pd_) * economics.interest_earned(amount, rate, term) - pd_ * economics.loss_if_default(amount)
    assert abs(profit) < 1e-6
