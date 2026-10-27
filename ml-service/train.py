"""
Step 2: train the credit risk models, choose the approval threshold that maximises
the lender's profit, and analyse the results.

Run:  python train.py
Needs: data/lending_club_loans.csv  (run download_data.py first)
Creates:
  model/xgboost_model.json   the trained XGBoost model used by the API
  model/categories.json      allowed values of the categorical inputs
  model/metrics.json         all results (accuracy, profit, pricing, groups)

What it does:
  1. Split the loans into 60% training / 20% validation / 20% test.
  2. Train a baseline (Logistic Regression) and XGBoost.
  3. Compare them on the test set with standard ML metrics.
  4. Economics: pick the threshold that maximises profit on the validation set,
     then compare "approve everyone", "threshold 0.5" and "profit-optimal" on the test set.
  5. Pricing check: does Lending Club's interest rate match the risk our model sees?
  6. Group analysis: approval and default rates by home ownership and income band.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

import economics
from data import category_lists, load_raw, save_categories, to_model_input
from features import (CATEGORICAL_FEATURES, INTEREST_RATE, LOSS_GIVEN_DEFAULT,
                      NUMERIC_FEATURES, TARGET)

MODEL_DIR = Path(__file__).parent / "model"


def classification_metrics(y_true, probabilities, threshold=0.5) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "auc": round(roc_auc_score(y_true, probabilities), 4),
        "accuracy": round(accuracy_score(y_true, predictions), 4),
        "precision": round(precision_score(y_true, predictions, zero_division=0), 4),
        "recall": round(recall_score(y_true, predictions), 4),
        "f1": round(f1_score(y_true, predictions), 4),
    }


def total_profit(df: pd.DataFrame, probabilities, threshold) -> float:
    """Profit the lender would have made by approving every loan with PD below the threshold."""
    approved = probabilities < threshold
    profit = economics.realised_profit(df["loan_amnt"], df[INTEREST_RATE], df["term_months"], df[TARGET])
    return float(profit[approved].sum())


def profit_optimal_threshold(df: pd.DataFrame, probabilities) -> float:
    candidates = np.round(np.arange(0.05, 0.96, 0.01), 2)
    profits = [total_profit(df, probabilities, t) for t in candidates]
    return float(candidates[int(np.argmax(profits))])


def profit_comparison(df: pd.DataFrame, probabilities, best_threshold) -> list:
    rows = []
    for name, threshold in [("Approve everyone", 1.01),
                            ("Model, threshold 0.50", 0.50),
                            (f"Model, profit-optimal threshold {best_threshold:.2f}", best_threshold)]:
        approved = probabilities < threshold
        rows.append({
            "strategy": name,
            "approval_rate": round(float(approved.mean()), 4),
            "default_rate_of_approved": round(float(df[TARGET][approved].mean()), 4),
            "total_profit_usd": round(total_profit(df, probabilities, threshold)),
        })
    return rows


def pricing_check(df: pd.DataFrame, probabilities) -> list:
    """Group loans by Lending Club's interest rate and compare price with risk."""
    bands = [0, 8, 11, 14, 17, 20, 100]
    labels = ["<8%", "8-11%", "11-14%", "14-17%", "17-20%", ">=20%"]
    table = df.assign(pd=probabilities,
                      band=pd.cut(df[INTEREST_RATE], bands, labels=labels, right=False))
    table["break_even"] = [economics.break_even_rate(p, t) for p, t in zip(table["pd"], table["term_months"])]
    table["underpriced"] = table[INTEREST_RATE] < table["break_even"]

    rows = []
    for label, group in table.groupby("band", observed=True):
        rows.append({
            "interest_rate_band": label,
            "loans": len(group),
            "actual_default_rate": round(float(group[TARGET].mean()), 4),
            "mean_predicted_pd": round(float(group["pd"].mean()), 4),
            "share_underpriced": round(float(group["underpriced"].mean()), 4),
        })
    return rows


def group_analysis(df: pd.DataFrame, probabilities, threshold) -> dict:
    table = df.assign(approved=probabilities < threshold,
                      income_band=pd.qcut(df["annual_inc"], 4,
                                          labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]))
    result = {}
    for column in ["home_ownership", "income_band"]:
        result[column] = [
            {"group": str(name), "loans": len(group),
             "actual_default_rate": round(float(group[TARGET].mean()), 4),
             "approval_rate": round(float(group["approved"].mean()), 4)}
            for name, group in table.groupby(column, observed=True)
        ]
    return result


def main() -> None:
    df = load_raw()
    print(f"Loaded {len(df)} loans; default rate = {df[TARGET].mean():.1%}")

    train_df, rest = train_test_split(df, test_size=0.4, random_state=42, stratify=df[TARGET])
    val_df, test_df = train_test_split(rest, test_size=0.5, random_state=42, stratify=rest[TARGET])

    categories = category_lists(train_df)
    X_train, X_val, X_test = (to_model_input(d, categories) for d in (train_df, val_df, test_df))
    y_train, y_test = train_df[TARGET], test_df[TARGET]

    # Baseline: Logistic Regression. Needs missing values filled, numbers scaled
    # and categories turned into 0/1 columns (one-hot encoding).
    preprocess = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC_FEATURES),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    baseline = make_pipeline(preprocess, LogisticRegression(max_iter=2000))
    baseline.fit(X_train, y_train)
    baseline_probabilities = baseline.predict_proba(X_test)[:, 1]

    # Main model: XGBoost. Handles missing values and categories by itself.
    model = XGBClassifier(
        n_estimators=400, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="auc",
        enable_categorical=True, tree_method="hist", random_state=42)
    model.fit(X_train, y_train)
    val_probabilities = model.predict_proba(X_val)[:, 1]
    test_probabilities = model.predict_proba(X_test)[:, 1]

    best_threshold = profit_optimal_threshold(val_df, val_probabilities)

    metrics = {
        "dataset": "Lending Club personal loans (USA)",
        "dataset_rows": len(df),
        "test_rows": len(test_df),
        "assumptions": {"loss_given_default": LOSS_GIVEN_DEFAULT},
        "approval_threshold": best_threshold,
        "logistic_regression": classification_metrics(y_test, baseline_probabilities),
        "xgboost": classification_metrics(y_test, test_probabilities),
        "xgboost_at_approval_threshold": classification_metrics(y_test, test_probabilities, best_threshold),
        "profit_comparison": profit_comparison(test_df, test_probabilities, best_threshold),
        "pricing_check": pricing_check(test_df, test_probabilities),
        "group_analysis": group_analysis(test_df, test_probabilities, best_threshold),
    }

    MODEL_DIR.mkdir(exist_ok=True)
    model.save_model(MODEL_DIR / "xgboost_model.json")
    save_categories(categories, MODEL_DIR / "categories.json")
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(json.dumps(metrics, indent=2))
    print(f"Model saved to {MODEL_DIR}")


if __name__ == "__main__":
    main()
