"""
Loading and cleaning the data, shared by train.py and app.py so that the API
prepares an applicant exactly the same way as the training data.
"""
import json
from pathlib import Path

import pandas as pd

from features import CATEGORICAL_FEATURES, FEATURES

DATA_FILE = Path(__file__).parent / "data" / "lending_club_loans.csv"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    # "36 months" -> 36
    df["term_months"] = df["term"].str.extract(r"(\d+)").astype(int)
    # Very few rows have no income; they cannot be scored sensibly.
    df = df.dropna(subset=["annual_inc"])
    # Keep the main categories; the rare ones (NONE, ANY) go into OTHER.
    df["home_ownership"] = df["home_ownership"].where(
        df["home_ownership"].isin(["RENT", "MORTGAGE", "OWN"]), "OTHER")
    return df


def category_lists(df: pd.DataFrame) -> dict:
    """The allowed values of each categorical feature, saved next to the model."""
    return {column: sorted(df[column].dropna().unique().tolist()) for column in CATEGORICAL_FEATURES}


def to_model_input(df: pd.DataFrame, categories: dict) -> pd.DataFrame:
    """Select the feature columns and give the categorical ones a fixed set of categories."""
    X = df[FEATURES].copy()
    for column in CATEGORICAL_FEATURES:
        X[column] = pd.Categorical(X[column], categories=categories[column])
    return X


def save_categories(categories: dict, path: Path) -> None:
    path.write_text(json.dumps(categories, indent=2))


def load_categories(path: Path) -> dict:
    return json.loads(path.read_text())
