"""Reproduce the original team's tuned Random Tree on the fixed test period."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid, TimeSeriesSplit

from gas_common import (
    FEATURES, REPORTS_DIR, TARGETS, get_train_test, metrics, save_model_bundle,
)
from random_tree_model import RandomTreeChangeRegressor

AUTHOR = "heng"
MODEL_NAME = "Random Tree"
FEATURES_USED = list(FEATURES)
PARAM_GRID = {
    "max_depth": [1, 2, 3],
    "min_samples_leaf": [10, 20, 40],
    "feature_mode": ["relative", "momentum", "calendar"],
    "target_clip": [None, 250],
    "history_window": [None, 90],
    "leaf_smoothing": [0., 50., 200.],
}
CHANGE_WEIGHTS = [0.25, 0.5, 1.0]


def tune_model(train):
    """Prefer regularized trees within one validation standard error of the best."""
    X, y = train[FEATURES_USED], train["y"]
    splits = list(TimeSeriesSplit(n_splits=4, test_size=28).split(X))
    records = []
    for params in ParameterGrid(PARAM_GRID):
        actual_changes, predicted_changes, fold_sizes = [], [], []
        for fit_idx, val_idx in splits:
            model = RandomTreeChangeRegressor(**params, change_weight=1.).fit(
                X.iloc[fit_idx], y.iloc[fit_idx])
            actual_changes.extend((y.iloc[val_idx] - X.iloc[val_idx]["lag_1"]).to_numpy())
            predicted_changes.extend(model.predict(X.iloc[val_idx]) - X.iloc[val_idx]["lag_1"])
            fold_sizes.append(len(val_idx))
        for weight in CHANGE_WEIGHTS:
            errors = np.asarray(actual_changes) - weight * np.asarray(predicted_changes)
            boundaries = np.cumsum([0] + fold_sizes)
            fold_rmse = [float(np.sqrt(np.mean(errors[a:b] ** 2)))
                         for a, b in zip(boundaries[:-1], boundaries[1:])]
            records.append({**params, "change_weight": weight,
                            "cv_RMSE": float(np.sqrt(np.mean(errors ** 2))),
                            "cv_mean_fold_RMSE": float(np.mean(fold_rmse)),
                            "cv_standard_error": float(np.std(fold_rmse, ddof=1) / np.sqrt(len(splits))),
                            **{f"fold_{i+1}_RMSE": value for i, value in enumerate(fold_rmse)}})
    results = pd.DataFrame(records).sort_values(
        ["cv_RMSE", "change_weight", "max_depth", "min_samples_leaf"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)
    minimum = results.sort_values("cv_mean_fold_RMSE").iloc[0]
    threshold = minimum["cv_mean_fold_RMSE"] + minimum["cv_standard_error"]
    results["within_one_se"] = results["cv_mean_fold_RMSE"] <= threshold
    # The one-standard-error rule is a regularization heuristic, not a confidence interval.
    best = results[results.within_one_se].sort_values(
        ["max_depth", "min_samples_leaf", "leaf_smoothing", "change_weight", "cv_RMSE"],
        ascending=[True, False, False, True, True],
    ).iloc[0]
    results["selected"] = False
    results.loc[best.name, "selected"] = True
    model = RandomTreeChangeRegressor(
        max_depth=int(best["max_depth"]),
        min_samples_leaf=int(best["min_samples_leaf"]),
        change_weight=float(best["change_weight"]),
        feature_mode=best["feature_mode"],
        target_clip=None if pd.isna(best["target_clip"]) else int(best["target_clip"]),
        history_window=None if pd.isna(best["history_window"]) else int(best["history_window"]),
        leaf_smoothing=float(best["leaf_smoothing"]),
    ).fit(X, y)
    return model, results, splits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", default=AUTHOR)
    parser.add_argument("--out-dir", default=str(REPORTS_DIR / "legacy-models"))
    parser.add_argument("--reports-dir", default=str(REPORTS_DIR))
    args = parser.parse_args()
    reports = Path(args.reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    summaries, fold_records = [], []
    for target in TARGETS:
        train, test = get_train_test(target)
        model, results, splits = tune_model(train)
        results.to_csv(reports / f"{target}_training_cv.csv", index=False)
        for fold, (fit_idx, val_idx) in enumerate(splits, start=1):
            fold_records.append({
                "target": target, "fold": fold,
                "train_start": train.index[fit_idx[0]], "train_end": train.index[fit_idx[-1]],
                "validation_start": train.index[val_idx[0]],
                "validation_end": train.index[val_idx[-1]],
            })
        # Test observations are used only after parameters have been selected.
        score = metrics(test["y"], model.predict(test[FEATURES_USED]))
        path = save_model_bundle(
            model, model_name=MODEL_NAME, author=args.author, target=target,
            features=FEATURES_USED, train=train, out_dir=args.out_dir,
        )
        selected = results[results.selected].iloc[0]
        summaries.append({
            "target": target, **model.get_params(), "cv_RMSE": selected["cv_RMSE"],
            "cv_mean_fold_RMSE": selected["cv_mean_fold_RMSE"],
            "cv_standard_error": selected["cv_standard_error"],
            **score,
        })
        print(f"{target}: {model.get_params()} CV RMSE={selected['cv_RMSE']:.3f} "
              f"test RMSE={score['RMSE']:.3f} -> {path}")
    pd.DataFrame(summaries).to_csv(reports / "training_summary.csv", index=False)
    pd.DataFrame(fold_records).to_csv(reports / "validation_folds.csv", index=False)


if __name__ == "__main__":
    main()
