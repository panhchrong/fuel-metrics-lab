# Cambodia Gasoline Price Prediction: Team Model Comparison

We have 3 team members and 3 algorithms. Each person trains one algorithm on the **same data, features and train/test split**, saves it as `.pkl` files, and one script ranks every model on the **same test set**. The lowest test error wins.

- **Goal:** predict tomorrow's retail fuel price (KHR per litre) for **regular gasoline** (`regu_gas`) and **diesel** (`diesel_gas`).
- **Train:** 15 Mar to 23 Sep 2026 (193 days). **Test:** 24 Sep to 11 Nov 2026 (49 days). Fixed in `src/gas_common.py`.
- **Main metric:** test RMSE in KHR (lower is better). MAE, R² and MAPE are also reported.

## Time-series study notebook

Open [fuel_price_study.ipynb](fuel_price_study.ipynb) for the executed study, including the missing-date audit, price and revision charts, feature comparisons, and daily forecast errors. The notebook applies the course material to both fuels. It selects features on four expanding validation folds and trains Linear Regression, Random Tree and XGBoost on 192 observed outcomes per fuel. The June 26 fill supplies lag history only.

To rerun from the project root with the dependencies below, use Python 3.12 and run:

```bash
jupyter nbconvert --execute --to notebook --inplace fuel_price_study.ipynb
```

The six newly fitted bundles are in `models/study/`. The leaderboard below and the dashboard’s **Model comparison** tab describe the original team bundles. To score the notebook bundles independently with the project’s comparison script:

```bash
python src/compare_models.py --models-dir models/study --reports-dir reports/study --dashboard-dir reports/study/snapshot
```

## What's in this package
```
README.md                     this file
requirements.txt              same library versions for everyone (scikit-learn==1.5.2)
data/Gasoline price - Gas_EN.csv
src/gas_common.py             SHARED: cleaning, features, split, metrics, save/load .pkl
src/train_template.py         copy this to train your own algorithm
src/compare_models.py         ranks every .pkl in models/ on the test set
models/regu_gas__linear_regression_time_lags__kay.pkl     Kay's model, regular gasoline
models/diesel_gas__linear_regression_time_lags__kay.pkl   Kay's model, diesel
```
`reports/` is created when you run `compare_models.py`.

**Why 2 `.pkl` files per algorithm?** A scikit-learn model predicts one value, so each algorithm is trained once per fuel: one file for `regu_gas`, one for `diesel_gas`.

## Setup (once)
```bash
pip install -r requirements.txt
```
Use Python 3.10 or newer, and **exactly scikit-learn 1.5.2**. A `.pkl` saved with another version may not load or may give different results.

## The data
- 248 daily rows (8 Mar to 11 Nov 2026), with 61 distinct `moc_no` values and 39 distinct notification filenames in `reference`.
- Prices are **step-shaped**: they only change on notification days and stay flat in between.
- Cleaning (done for you in `gas_common.load_clean_data`): one missing day is forward-filled, because the price stays the same until the next notification. `moc_no` and `reference` are document IDs, not used as features.

## The shared features
Built by `gas_common.make_features(data, target)`. Only **past** values are used, so there's no leakage.

| Feature | Meaning |
|---|---|
| `day_index` | days since 8 Mar 2026 (trend) |
| `month`, `day_of_week` | calendar effects |
| `lag_1` | price of this fuel yesterday |
| `lag_7` | price of this fuel 7 days ago |
| `other_lag_1` | price of the *other* fuel yesterday |
| `roll_mean_7` | average price over the previous 7 days |

You may use all of them or a subset. Don't add new feature names without agreeing with the team first.

## Current leaderboard (test set, 49 days)
| Fuel | Rank | Model | Author | RMSE | MAE | R² | MAPE% |
|---|---|---|---|---|---|---|---|
| regu_gas | 1 | Naive (same as yesterday) | baseline | 53.5 | 12.2 | 0.796 | 0.24 |
| regu_gas | 2 | Linear Regression (time + lags) | kay | 54.1 | 17.8 | 0.790 | 0.35 |
| diesel_gas | 1 | Linear Regression (time + lags) | kay | **65.8** | 28.2 | 0.868 | 0.50 |
| diesel_gas | 2 | Naive (same as yesterday) | baseline | 67.4 | 13.3 | 0.861 | 0.24 |

**The naive baseline is the bar to beat.** It just predicts "same price as yesterday". Because prices only jump on notification days, this is very hard to beat. A model is only useful if its RMSE is lower than the baseline.

## Kay's model: Linear Regression (time + lags)
**Algorithm:** `Pipeline([StandardScaler(), LinearRegression()])` using all 7 features. It fits a weighted sum of the features that minimises squared error on the train set.

**Learned equations** (original units, KHR):
```
regu_gas   ≈   87 + 0.904*lag_1 + 0.139*roll_mean_7 - 0.072*lag_7 + 0.011*other_lag_1
                  + 0.217*day_index - 3.8*month - 1.9*day_of_week
diesel_gas ≈  259 + 1.012*lag_1 + 0.019*roll_mean_7 - 0.046*lag_7 - 0.020*other_lag_1
                  + 0.979*day_index - 30.1*month - 1.4*day_of_week
```

**How it works:** the model has learned "tomorrow ≈ yesterday's price, slightly adjusted". `lag_1` carries almost all of the weight, and the other features make small corrections.

**Results:** test error is about 54 KHR for regular and 66 KHR for diesel (0.3–0.5%). It beats the baseline on diesel and is slightly behind it on regular gasoline.

**Limitation:** almost all of the error comes from notification days, when the price jumps. Past prices can't predict when or how much the next jump will be. This applies to every algorithm that uses these features.

A trend-only line (`price = a + b*day_index`) was also tried and failed badly (RMSE above 1,100 KHR). Prices went down and then up again, so a straight line can't follow them. It isn't included here.

## Add your model (about 5 minutes)
1. Copy the template: `src/train_template.py` → `src/train_<your_algo>.py`
2. Edit the top of the file:
   ```python
   AUTHOR = "dara"                   # your name, must be unique in the team
   MODEL_NAME = "SVR"
   FEATURES_USED = FEATURES          # or a subset of gas_common.FEATURES
   def make_model():
       return Pipeline([("scaler", StandardScaler()), ("svr", SVR(C=1000))])
   ```
3. Run it from the project folder: `python src/train_<your_algo>.py`
   This saves `models/regu_gas__svr__dara.pkl` and `models/diesel_gas__svr__dara.pkl` and prints your test RMSE.
4. Send the team **your 2 `.pkl` files and your training script**.

## Compare all models
Put everyone's `.pkl` files into `models/`, then run:
```bash
python src/compare_models.py
```
This prints a leaderboard per fuel, sorted by test RMSE, and saves `reports/model_comparison.csv` and `reports/model_comparison.png`. Files that are broken or trained on test dates are skipped, and the reason is printed.

## Load a model yourself
```python
import sys; sys.path.insert(0, "src")
from gas_common import load_model_bundle, get_train_test, metrics

b = load_model_bundle("models/regu_gas__linear_regression_time_lags__kay.pkl")
train, test = get_train_test(b["target"])
pred = b["model"].predict(test[b["features"]])
print(metrics(test["y"], pred))
```

## .pkl format (handled by `save_model_bundle`)
| key | example |
|---|---|
| `model` | fitted estimator with `.predict(DataFrame)` |
| `model_name`, `author` | `"Linear Regression (time + lags)"`, `"kay"` |
| `target` | `"regu_gas"` or `"diesel_gas"` |
| `features` | list of column names from `gas_common.FEATURES` |
| `train_period` | `("2026-03-15", "2026-09-23")` |
| `sklearn_version`, `created_at` | `"1.5.2"`, `"2026-11-14"` |

## Integration notes for non-scikit-learn algorithms
`compare_models.py` only calls `model.predict(test[features])`, so any model works if it:
- **Has `.predict(X)`** that takes a pandas DataFrame of the feature columns and returns one value per row. XGBoost/LightGBM's sklearn API (`XGBRegressor`, `LGBMRegressor`) already does this.
- **Uses features, not its own date index.** ARIMA/Prophet-style models that forecast from dates don't fit this interface directly. Wrap them in a small class with `.predict(X)`, and put that class in a `.py` file inside `src/` that you also share. Otherwise teammates can't unpickle your model.
- **Tree models (Random Forest, XGBoost, ...) can't predict above or below the prices seen in training.** Test prices rose higher than the training range, so a default Random Forest scored diesel RMSE ≈ 341 (worse than the baseline). If you use trees, consider wrapping the model so it learns the *change* from yesterday (`y - lag_1`) and `.predict` adds `lag_1` back.
- **Uses only agreed libraries.** If you need a library that's not in `requirements.txt` (e.g. `xgboost`), tell the team so everyone adds the same version.

## Rules
- **Don't change** `gas_common.py` (split date, features) on your own. Agree with the team first, or the comparison isn't fair.
- Train on the **train split only** (`get_train_test`). The compare script rejects models trained on test dates.
- Use the same scikit-learn version (1.5.2) so everyone can open everyone's `.pkl`.
- Only open `.pkl` files from teammates you trust. Loading a pickle can run code.

## Vue research dashboard

The local dashboard includes the evaluated snapshot from all six saved bundles. Open **Model comparison** for per-fuel price trajectories, daily errors, and the leaderboard. **Methodology** traces the pipeline and **Data analysis** contains the study figures. The earlier two-model leaderboard in this README predates the complete comparison.

From the project root, run the following with Node 22.12+ and npm.

```bash
cd dashboard
npm ci
npm run dev
```

Use the local URL printed by Vite. For a production build, run `npm run build` in the same folder. Run `npm run preview` to serve that build. The browser reads static files from `public/study`.

To refresh the snapshot after a bundle or CSV change, run `python src/compare_models.py` from the project root using the dependencies in `requirements.txt` or the isolated environment command in `plan.md`. This also regenerates the CSV and PNG reports. Rebuild the dashboard to include refreshed data in production.

### Interactive forecast

Open **Forecast** (`/#forecast`) or **Extend forecast** beneath the price trajectory. Choose a notebook model, fuel and end date. The window extends up to three calendar months from the last dataset date, currently 11 November 2026 through 11 February 2027. Random Tree is the initial fitted model because it had the lowest validation RMSE among the three trained algorithms for both fuels.

Enter a later date and both posted prices to extend the observed history. The graph recalculates immediately, carrying the previous quote across any skipped dates. Added quotes stay in memory while navigating the dashboard and clear on reload. The dashed line shows recursive daily estimates. Both fuels use history through the previous day, including prior predictions when the graph extends beyond the latest quote. The study's error scores measure one-day forecasts only.

The dashboard runs the fitted coefficients and trees locally. After retraining the notebook models, regenerate their browser representation from the project root before rebuilding:

```bash
python src/export_forecast_models.py
```

### Notebook figures

Open **Data analysis** (`/#data-analysis`) for the notebook’s validation choice, holdout scores and errors on changed and flat days. Select a fuel to inspect its results, browse the five figures, or download the executed notebook. After rerunning the notebook, refresh its results and figures together:

```bash
python src/import_notebook_figures.py fuel_price_study.ipynb
```

Pass multiple notebook paths together to replace the gallery index with their combined output. The importer extracts saved PNG, JPEG, SVG, GIF and WebP outputs in cell order and identifies rich outputs that need a static image representation. It does not execute the notebook. Refresh Data analysis after importing, or rebuild for production.
