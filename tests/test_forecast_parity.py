"""Check the shipped browser models against the fitted Python bundles."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gas_common import (STUDY_MODEL_AUTHORS, TARGETS, load_clean_data, load_model_bundle,
                        make_features, model_bundle_path)


class ForecastParityTest(unittest.TestCase):
    def test_recursive_forecasts_with_a_new_quote(self):
        history = load_clean_data()
        last_date = history.index[-1]
        quote_date = last_date + pd.Timedelta(days=4)
        limit = last_date + pd.DateOffset(months=3)
        quote = {"day": quote_date.date().isoformat(), "regu_gas": 4830.5, "diesel_gas": 5721.25}
        # Exercise the actual static assets and browser implementation, including the gap.
        script = """
            import fs from 'node:fs';
            import {forecastDays, historyWithQuotes, monthsAfter} from './dashboard/src/forecast.js';
            const read = file => JSON.parse(fs.readFileSync('dashboard/public/study/' + file));
            const snapshot = read('backtest.json'), bundle = read('forecast-models.json');
            const history = historyWithQuotes(snapshot, [JSON.parse(process.argv[1])]);
            const limit = monthsAfter(snapshot.dates.at(-1), 3);
            const result = {};
            for (const name of Object.keys(bundle.models))
                result[name] = forecastDays(history, limit, bundle, name, limit);
            console.log(JSON.stringify(result));
        """
        browser = json.loads(subprocess.check_output(
            ["node", "--input-type=module", "-e", script, json.dumps(quote)], cwd=ROOT))
        self.assertEqual(set(browser), {"Linear Regression", "Random Tree", "XGBoost"})
        history.loc[quote_date] = [quote[fuel] for fuel in TARGETS]
        for name, rows in browser.items():
            with self.subTest(model=name):
                projected = history.asfreq("D").ffill()
                bundles = {fuel: load_model_bundle(model_bundle_path(fuel, name, STUDY_MODEL_AUTHORS[name]))
                           for fuel in TARGETS}
                for day in pd.date_range(quote_date + pd.Timedelta(days=1), limit):
                    projected.loc[day] = np.nan
                    for fuel in TARGETS:
                        bundle = bundles[fuel]
                        features = make_features(projected, fuel, include_study=True)
                        projected.loc[day, fuel] = bundle["model"].predict(
                            features.loc[[day], bundle["features"]])[0]
                expected = projected.loc[projected.index > quote_date]
                self.assertEqual([r["day"] for r in rows], expected.index.strftime("%Y-%m-%d").tolist())
                np.testing.assert_allclose([[r[f] for f in TARGETS] for r in rows],
                                           expected[TARGETS].to_numpy(), rtol=0, atol=1e-5)
