"""
Step 2: train the credit risk models and save the best one.

Run:  python train.py
Needs: data/default_of_credit_card_clients.xls  (run download_data.py first)
Creates:
  model/xgboost_model.json   the trained XGBoost model used by the API
  model/metrics.json         evaluation results (accuracy, AUC, fairness)

What it does:
  1. Load the data and split it into 80% training / 20% test.
  2. Train a simple baseline (Logistic Regression) and XGBoost.
  3. Compare them on the test set.
  4. Fairness audit: compare XGBoost's results for men and women.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from features import FEATURES, PROTECTED_ATTRIBUTE, TARGET

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "default_of_credit_card_clients.xls"
MODEL_DIR = BASE_DIR / "model"
THRESHOLD = 0.5  # probability above which we predict "will default"


def load_data() -> pd.DataFrame:
    # The first row of the sheet is a second header (X1, X2, ...), so skip it.
    df = pd.read_excel(DATA_FILE, header=1)
    # EDUCATION has undocumented codes 0, 5, 6; group them into 4 = "others".
    df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    # MARRIAGE has an undocumented code 0; treat it as 3 = "others".
    df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})
    return df


def evaluate(y_true, probabilities) -> dict:
    predictions = (probabilities >= THRESHOLD).astype(int)
    return {
        "auc": round(roc_auc_score(y_true, probabilities), 4),
        "accuracy": round(accuracy_score(y_true, predictions), 4),
        "precision": round(precision_score(y_true, predictions), 4),
        "recall": round(recall_score(y_true, predictions), 4),
        "f1": round(f1_score(y_true, predictions), 4),
    }


def fairness_audit(test_df: pd.DataFrame, probabilities) -> dict:
    """Compare how the model treats each group of the protected attribute."""
    result = {}
    names = {1: "male", 2: "female"}
    for code, name in names.items():
        mask = (test_df[PROTECTED_ATTRIBUTE] == code).to_numpy()
        y_group = test_df[TARGET].to_numpy()[mask]
        p_group = probabilities[mask]
        predicted_default = p_group >= THRESHOLD
        result[name] = {
            "count": int(mask.sum()),
            "actual_default_rate": round(float(y_group.mean()), 4),
            # share of applicants the model would approve (predicts no default)
            "approval_rate": round(float(1 - predicted_default.mean()), 4),
            "auc": round(roc_auc_score(y_group, p_group), 4),
        }
    # Demographic parity difference: 0 means both groups are approved equally often.
    result["approval_rate_difference"] = round(
        abs(result["male"]["approval_rate"] - result["female"]["approval_rate"]), 4)
    return result


def main() -> None:
    df = load_data()
    print(f"Loaded {len(df)} rows; default rate = {df[TARGET].mean():.1%}")

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df[TARGET])
    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    # Baseline: Logistic Regression (needs scaled inputs).
    baseline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    baseline.fit(X_train, y_train)
    baseline_metrics = evaluate(y_test, baseline.predict_proba(X_test)[:, 1])

    # Main model: XGBoost (gradient boosted decision trees).
    model = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="auc", random_state=42)
    model.fit(X_train, y_train)
    xgb_probabilities = model.predict_proba(X_test)[:, 1]
    xgb_metrics = evaluate(y_test, xgb_probabilities)

    metrics = {
        "dataset_rows": len(df),
        "test_rows": len(test_df),
        "threshold": THRESHOLD,
        "logistic_regression": baseline_metrics,
        "xgboost": xgb_metrics,
        "fairness_by_sex": fairness_audit(test_df, xgb_probabilities),
    }

    MODEL_DIR.mkdir(exist_ok=True)
    model.save_model(MODEL_DIR / "xgboost_model.json")
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(json.dumps(metrics, indent=2))
    print(f"Model saved to {MODEL_DIR / 'xgboost_model.json'}")


if __name__ == "__main__":
    main()
