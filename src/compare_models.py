"""Rank every team model (.pkl) on the same test set.

Usage:
    python src/compare_models.py                      # uses models/
    python src/compare_models.py --models-dir models other_folder

Outputs: a leaderboard per fuel in the terminal, reports/model_comparison.csv
and reports/model_comparison.png.
WARNING: only load .pkl files from people you trust; unpickling runs code.
"""
import argparse
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import sklearn

from dashboard_export import DASHBOARD_DIR, export_dashboard, series
from gas_common import (MODELS_DIR, REPORTS_DIR, TARGETS, TEST_START, load_clean_data,
                        load_model_bundle, make_features, metrics, train_test_split_time)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-dir", nargs="+", default=[str(MODELS_DIR)])
    parser.add_argument("--reports-dir", default=str(REPORTS_DIR))
    parser.add_argument("--dashboard-dir", default=str(DASHBOARD_DIR))
    args = parser.parse_args()

    df = load_clean_data()
    splits = {t: train_test_split_time(make_features(df, t, include_study=True)) for t in TARGETS}
    tests = {t: split[1] for t, split in splits.items()}
    models = {t: [] for t in TARGETS}
    skipped = []
    test = tests[TARGETS[0]]
    print(f"Test set: {test.index.min().date()} to {test.index.max().date()} ({len(test)} days)\n")

    rows = []
    for t in TARGETS:  # reference line every model should be compared with
        scores = metrics(tests[t]["y"], tests[t]["lag_1"])
        models[t].append(series("baseline", "Yesterday’s price", "baseline", tests[t]["lag_1"],
                                tests[t], scores, ["lag_1"]))
        rows.append({"target": t, "model": "Naive (same as yesterday)", "author": "baseline",
                     "file": "-", **scores})

    files = sorted(p for d in args.models_dir for p in Path(d).glob("*.pkl"))
    if not files:
        print("No .pkl files found in", args.models_dir)
    for path in files:
        try:
            b = load_model_bundle(path)
            if b["sklearn_version"] != sklearn.__version__:
                warnings.warn(f"{path.name}: saved with scikit-learn {b['sklearn_version']}, "
                              f"installed {sklearn.__version__}")
            te = tests[b["target"]]
            pred = b["model"].predict(te[b["features"]])
            scores = metrics(te["y"], pred)
            model_id = path.stem.removeprefix(b["target"] + "__")
            models[b["target"]].append(series(model_id, b["model_name"], b["author"], pred,
                                              te, scores, b["features"]))
        except Exception as e:  # skip bad files but keep going
            skipped.append({"file": path.name, "reason": str(e)})
            print(f"SKIPPED {path.name}: {e}")
            continue
        rows.append({"target": b["target"], "model": b["model_name"], "author": b["author"],
                     "file": path.name, **scores})

    board = pd.DataFrame(rows).sort_values(["target", "RMSE"]).reset_index(drop=True)
    board.insert(1, "rank", board.groupby("target")["RMSE"].rank(method="min").astype(int))

    pd.set_option("display.width", 160)
    for t in TARGETS:
        print(f"=== {t} (sorted by test RMSE, lower is better) ===")
        print(board[board["target"] == t].drop(columns="target")
              .to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
        print()

    out = Path(args.reports_dir)
    out.mkdir(parents=True, exist_ok=True)
    board.to_csv(out / "model_comparison.csv", index=False)

    fig, axes = plt.subplots(1, len(TARGETS), figsize=(7 * len(TARGETS), 0.6 * len(board) + 2))
    for ax, t in zip(axes, TARGETS):
        b = board[board["target"] == t].iloc[::-1]
        labels = b["model"] + " (" + b["author"] + ")"
        colors = ["#999999" if a == "baseline" else "#4c72b0" for a in b["author"]]
        ax.barh(labels, b["RMSE"], color=colors)
        ax.set_title(f"{t}: test RMSE (KHR), lower is better")
    plt.tight_layout()
    fig.savefig(out / "model_comparison.png", dpi=120)
    export_dashboard(args.dashboard_dir, df, splits, models, skipped, out / "model_comparison.png")
    print("Saved", out / "model_comparison.csv", "and", out / "model_comparison.png")


if __name__ == "__main__":
    main()
