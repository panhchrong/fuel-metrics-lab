"""Shared data, features, split and model-bundle helpers for the team.

Every team member imports from this file so all models use the same
cleaned data, the same features and the same train/test split.
That is what makes the comparison fair.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import (mean_absolute_error, mean_absolute_percentage_error,
                             mean_squared_error, r2_score)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "Gasoline price - Gas_EN.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

TARGETS = ["regu_gas", "diesel_gas"]
FEATURES = ["day_index", "month", "day_of_week", "lag_1", "lag_7", "other_lag_1", "roll_mean_7"]
STUDY_FEATURES = ["last_change", "flat_days", "weekday_sin", "weekday_cos", "ten_day_boundary"]

START_DATE = pd.Timestamp("2026-03-08")  # origin of day_index; do not change
TEST_START = pd.Timestamp("2026-09-24")  # first day of the shared test set; do not change

REQUIRED_KEYS = {"model", "model_name", "author", "target", "features",
                 "train_period", "sklearn_version", "created_at"}


# ---------------------------------------------------------------- data
def load_clean_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Daily prices indexed by date; missing days forward-filled."""
    raw = pd.read_csv(path, dtype={"moc_no": str})
    raw["im_date"] = pd.to_datetime(raw["im_date"], format="%d-%m-%Y")
    raw = raw.sort_values("im_date")
    full_range = pd.date_range(raw["im_date"].min(), raw["im_date"].max(), freq="D")
    df = raw.set_index("im_date")[TARGETS].reindex(full_range).ffill().astype(float)
    df.index.name = "date"
    return df


def make_features(data: pd.DataFrame, target: str, *, include_study=False) -> pd.DataFrame:
    """Feature matrix + 'y' column for one fuel. Uses past values only (no leakage)."""
    if target not in TARGETS:
        raise ValueError(f"target must be one of {TARGETS}")
    other = [t for t in TARGETS if t != target][0]
    X = pd.DataFrame(index=data.index)
    X["day_index"] = (data.index - START_DATE).days
    X["month"] = data.index.month
    X["day_of_week"] = data.index.day_of_week
    X["lag_1"] = data[target].shift(1)
    X["lag_7"] = data[target].shift(7)
    X["other_lag_1"] = data[other].shift(1)
    X["roll_mean_7"] = data[target].shift(1).rolling(7).mean()
    if include_study:
        previous = X["lag_1"]
        X["last_change"] = previous.diff()
        # Run length through yesterday. The first observed price starts a new run.
        run = previous.ne(previous.shift()).cumsum()
        X["flat_days"] = previous.groupby(run).cumcount().where(previous.notna())
        angle = 2 * np.pi * data.index.day_of_week / 7
        X["weekday_sin"] = np.sin(angle)
        X["weekday_cos"] = np.cos(angle)
        X["ten_day_boundary"] = data.index.day.isin([1, 11, 21]).astype(int)
    X["y"] = data[target]
    return X


def train_test_split_time(feat: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological split: train before TEST_START, test from TEST_START on."""
    feat = feat.dropna()
    return feat[feat.index < TEST_START], feat[feat.index >= TEST_START]


def get_train_test(target: str, path: str | Path = DATA_PATH, *, include_study=False):
    """One call for teammates: returns (train, test) feature frames for a target."""
    return train_test_split_time(make_features(load_clean_data(path), target, include_study=include_study))


# ---------------------------------------------------------------- metrics
def metrics(y_true, y_pred) -> dict:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": r2_score(y_true, y_pred),
        "MAPE%": mean_absolute_percentage_error(y_true, y_pred) * 100,
    }


# ---------------------------------------------------------------- bundles
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def save_model_bundle(model, *, model_name: str, author: str, target: str,
                      features: list[str], train: pd.DataFrame,
                      out_dir: str | Path = MODELS_DIR) -> Path:
    """Save a fitted model in the team's standard .pkl format and return its path."""
    unknown = set(features) - set(FEATURES + STUDY_FEATURES)
    if unknown:
        raise ValueError(f"Unknown features {unknown}")
    if train.index.max() >= TEST_START:
        raise ValueError("Model must be trained only on data before TEST_START")
    bundle = {
        "model": model,
        "model_name": model_name,
        "author": author,
        "target": target,
        "features": list(features),
        "train_period": (str(train.index.min().date()), str(train.index.max().date())),
        "sklearn_version": sklearn.__version__,
        "created_at": _dt.date.today().isoformat(),
    }
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{target}__{_slug(model_name)}__{_slug(author)}.pkl"
    joblib.dump(bundle, path)
    return path


def load_model_bundle(path: str | Path) -> dict:
    """Load and check a bundle. Only load files from people you trust: unpickling runs code."""
    bundle = joblib.load(path)
    if not isinstance(bundle, dict):
        raise ValueError("not a team bundle (expected a dict)")
    missing = REQUIRED_KEYS - bundle.keys()
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")
    if bundle["target"] not in TARGETS:
        raise ValueError(f"unknown target {bundle['target']!r}")
    unknown = set(bundle["features"]) - set(FEATURES + STUDY_FEATURES)
    if unknown:
        raise ValueError(f"unknown features {sorted(unknown)}")
    if pd.Timestamp(bundle["train_period"][1]) >= TEST_START:
        raise ValueError(f"train_period {bundle['train_period']} overlaps the test set "
                         f"(starts {TEST_START.date()})")
    return bundle
