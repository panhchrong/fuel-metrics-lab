"""Static data contract for the Vue backtest viewer."""
import json
from pathlib import Path
from shutil import copyfile

import pandas as pd

from gas_common import DATA_PATH, PROJECT_ROOT, TARGETS, TEST_START

DASHBOARD_DIR = PROJECT_ROOT / "dashboard" / "public" / "study"


def series(model_id, name, author, prediction, test, scores, features):
    change = test["y"] != test["lag_1"]
    error = (test["y"] - prediction).abs()

    def mean(mask):
        return float(error[mask].mean()) if mask.any() else None

    return dict(id=model_id, name=name, author=author, features=features,
                values=list(map(float, prediction)), scores=scores,
                changeMAE=mean(change), flatMAE=mean(~change))


def export_dashboard(directory, history, splits, models, skipped, figure):
    raw = pd.read_csv(DATA_PATH)
    observed = set(pd.to_datetime(raw["im_date"], format="%d-%m-%Y"))
    train, test = splits[TARGETS[0]]
    snapshot = dict(
        dates=history.index.strftime("%Y-%m-%d").tolist(),
        observedDays=len(observed),
        filled=[day.date().isoformat() for day in history.index if day not in observed],
        trainStart=train.index[0].date().isoformat(), trainDays=len(train),
        testStart=TEST_START.date().isoformat(), testDays=len(test), units="KHR/L",
        fuels={}, skipped=skipped,
    )
    for target in TARGETS:
        te = splits[target][1]
        snapshot["fuels"][target] = dict(actual=history[target].tolist(),
            dates=te.index.strftime("%Y-%m-%d").tolist(),
            changed=(te["y"] != te["lag_1"]).tolist(),
            models=sorted(models[target], key=lambda m: m["scores"]["RMSE"]))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "backtest.json").write_text(json.dumps(snapshot, allow_nan=False))
    copyfile(figure, directory / "model_comparison.png")
