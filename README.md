# Cambodia Gasoline Price Prediction: Team Model Comparison

[Open the deployed dashboard](https://fuel-metrics.cyclostack.dev/)

## Collaborators

| Name | Email | Work |
| --- | --- | --- |
| Roeuy Kay | kayroeuy66@gmail.com | Linear Regression |
| Kong Sovankiry | kongsovankiry15@gmail.com | XGBoost |
| Nom Sokheng | kongsovankiry15@gmail.com | Random Forest |
| Sith Panhchakroung | sithpanhchrong@gmail.com | Organizer |

The study notebook trains three algorithms for each fuel and keeps the team attribution for each one. Kay is credited for Linear Regression, Heng for Random Tree, and Kiry for XGBoost. All three algorithms are scored on the same test dates.

- **Goal:** predict tomorrow's retail fuel price (KHR per litre) for **regular gasoline** (`regu_gas`) and **diesel** (`diesel_gas`).
- **Train:** 15 Mar to 23 Sep 2026 (192 observed outcomes across 193 days). **Test:** 24 Sep to 11 Nov 2026 (49 days). The split date is fixed in `src/gas_common.py`.
- **Main metric:** test RMSE in KHR (lower is better). MAE, R² and MAPE are also reported.

## Time-series study notebook

Open [fuel_price_study.ipynb](fuel_price_study.ipynb) for the executed study, including the missing-date audit, price and revision charts, feature comparisons, and daily forecast errors. The notebook applies the course material to both fuels. It selects features on four expanding validation folds and trains Linear Regression, Random Tree and XGBoost on 192 observed outcomes per fuel. The June 26 fill supplies lag history only.

To rerun from the project root with the dependencies below, use Python 3.12 and run:

```bash
jupyter nbconvert --execute --to notebook --inplace fuel_price_study.ipynb
```

The notebook saves six fitted bundles in `models/`. Refresh the leaderboard and browser forecast from those bundles after retraining:

```bash
python src/compare_models.py
python src/export_forecast_models.py
```

## What's in this package
```
README.md                     this file
requirements.txt              same library versions for everyone (scikit-learn==1.5.2)
data/Gasoline price - Gas_EN.csv
src/gas_common.py             SHARED: cleaning, features, split, metrics, save/load .pkl
src/train_template.py         copy this to train your own algorithm
src/compare_models.py         ranks every .pkl in models/ on the test set
models/regu_gas__linear_regression__kay.pkl     Kay's model, regular gasoline
models/diesel_gas__linear_regression__kay.pkl   Kay's model, diesel
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
| regu_gas | 1 | XGBoost | kiry | **52.521** | 29.076 | 0.803 | 0.564 |
| regu_gas | 2 | Linear Regression | kay | 52.966 | 19.302 | 0.799 | 0.373 |
| regu_gas | 3 | Random Tree | heng | 53.445 | 13.628 | 0.796 | 0.264 |
| regu_gas | 4 | Naive (same as yesterday) | baseline | 53.452 | **12.245** | 0.796 | 0.237 |
| diesel_gas | 1 | Linear Regression | kay | **65.795** | 18.869 | 0.868 | 0.332 |
| diesel_gas | 2 | Naive (same as yesterday) | baseline | 67.386 | **13.265** | 0.861 | 0.235 |
| diesel_gas | 3 | Random Tree | heng | 67.532 | 14.245 | 0.861 | 0.253 |
| diesel_gas | 4 | XGBoost | kiry | 68.269 | 34.822 | 0.858 | 0.615 |

Yesterday's price has the lowest MAE for both fuels. Each fuel changed price on three holdout days.

## Fitted study models

- **Linear Regression · Kay** uses a standard scaler and predicts price directly from yesterday's price for both fuels.
- **Random Tree · Heng** predicts a price adjustment using yesterday's quote for regular gasoline and the price-history inputs for diesel.
- **XGBoost · Kiry** predicts a price adjustment using the price-history inputs for regular gasoline and yesterday's quote for diesel.

The price-history inputs are `lag_1`, `lag_7`, `other_lag_1`, and `roll_mean_7`. To reproduce the earlier Random Tree or XGBoost experiments, run `src/train_random_tree.py` or `src/train_xgboost.py` with Python. Those scripts save to `reports/legacy-models/` by default.

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

b = load_model_bundle("models/regu_gas__linear_regression__kay.pkl")
_, test = get_train_test(b["target"], include_study=True)
pred = b["model"].predict(test[b["features"]])
print(metrics(test["y"], pred))
```

## .pkl format (handled by `save_model_bundle`)
| key | example |
|---|---|
| `model` | fitted estimator with `.predict(DataFrame)` |
| `model_name`, `author` | `"Linear Regression"`, `"kay"` |
| `target` | `"regu_gas"` or `"diesel_gas"` |
| `features` | column names from `gas_common.FEATURES` or `gas_common.STUDY_FEATURES` |
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

The local dashboard includes the evaluated snapshot from all six study bundles. Open **Model comparison** for per-fuel price trajectories, daily errors, and the leaderboard. **Methodology** traces the pipeline and **Data analysis** contains the study figures.

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
