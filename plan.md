# Cambodia fuel price model comparison

Build a Vue dashboard that answers **which one-day-ahead model best predicts each fuel, and where does it beat yesterday’s price?** The first version will use a static JSON export from Python so the historical comparison can run without a backend.

## Verified project findings

- The [source CSV](data/Gasoline%20price%20-%20Gas_EN.csv) contains 248 observed daily records from March 8 to November 11, 2026, for regular gasoline (`regu_gas`) and diesel (`diesel_gas`). Prices are in KHR per litre. [The shared pipeline](src/gas_common.py) forward-fills June 26 and builds lagged prices, a trailing seven-day average, and calendar features.
- After preparing the features, the chronological split has **193 training days** (March 15–September 23) and **49 test days** (September 24–November 11). Each forecast uses the actual prices observed before its target date. Label the results as a **one-day-ahead backtest** in the dashboard.
- The project contains six saved bundles, one per algorithm and fuel. Linear Regression predicts price directly. Random Tree and XGBoost estimate the change from yesterday and add it to yesterday’s price. The baseline predicts yesterday’s price.
- [The comparison script](src/compare_models.py) evaluates the saved bundles on the same test dates and writes `reports/model_comparison.csv` and `reports/model_comparison.png`. The CSV contains aggregate metrics. The script already computes the day-by-day predictions needed for the web charts.

### Verified 49-day results

RMSE and MAE are in KHR/L. The existing leaderboard ranks by RMSE. Lower is better for both metrics.

| Model | Regular RMSE | Regular MAE | Diesel RMSE | Diesel MAE |
|---|---:|---:|---:|---:|
| Yesterday’s price | 53.45 | **12.24** | 67.39 | **13.27** |
| Linear Regression | 54.13 | 17.83 | **65.77** | 28.15 |
| Random Tree | 53.51 | 12.96 | 67.52 | 14.19 |
| XGBoost (delta) | **52.69** | 29.70 | 66.57 | 17.52 |

Each fuel changed price on **3 of 49 days**. For regular gasoline, XGBoost averaged 185.96 KHR/L of absolute error on change days versus 200.00 for the baseline. On the 46 flat days, XGBoost averaged 19.50 KHR/L and the baseline was exact. Showing both groups and both metrics will make that trade-off visible.

### Reproduce the complete comparison

[The XGBoost wrapper](src/gas_wrappers.py) is present and both XGBoost bundles loaded successfully. [The dependency list](requirements.txt) still needs an XGBoost entry. This command uses the versions verified with the bundled models.

```bash
uv run --no-project --isolated --python 3.12 \
  --with 'scikit-learn==1.5.2' --with 'xgboost-cpu==3.4.1' \
  --with pandas --with matplotlib --with joblib \
  python src/compare_models.py
```

## Implementation plan

1. **Export the evaluated data.** Add the verified XGBoost dependency and extend the existing comparison to export JSON alongside its CSV and PNG. Reuse the current split, feature preparation, saved-model predictions, and metrics. Include the test period, units, and for each fuel, ISO dates, actual prices, yesterday’s prices, price-change flags, and predictions keyed by stable model IDs. Include display names, authors, and full-period scores so Vue can match the series to the ranking. Surface skipped bundles explicitly in the export if a model fails to load.
2. **Build the Vue dashboard.** Use Vue 3 and Vite. Start with a fuel selector, a price chart with the actual price drawn as a step line, and toggles for model and baseline overlays. Add a daily absolute error chart aligned to the same dates, with change days marked and exact values available on hover or focus. Show RMSE and MAE in a ranked table and keep the displayed period visible. Apply `$dashboard-design` when implementing and checking the desktop and phone layouts.
3. **Verify the full flow.** Regenerate the JSON from Python and confirm it contains 49 dates per fuel with all six model predictions represented. Compare the exported scores with the leaderboard above and spot-check chart values on a price-change day and a flat day. Check the fuel switch, series toggles, keyboard access, phone layout, and missing-data state. Document the export command and the Vue dev and production build commands once the app exists.

## Dashboard implementation prompt

Build a local Vue 3 / Vite research dashboard for the Cambodian retail fuel study. A reader should be able to choose a fuel, identify the lowest-RMSE model, and inspect the days on which it gains or loses against yesterday’s price.

1. Evaluate the existing bundles once using the shared Python comparison. Export a reproducible static snapshot containing cleaned history, the train/test boundary, per-date predictions, model identities and scores. Preserve the existing reports and expose missing or skipped bundles.
2. Make the price line the primary view. Connect pre-test actual prices to separately colored prediction lines at the first test date, mark the boundary, and keep the observed test prices visible. Distinguish overlapping lines with patterns, toggles and exact daily values. Offer recent context and full history. Keep every score tied to the same 49 held-out days.
3. Rank the three fitted algorithms alongside persistence. Show RMSE, MAE, change-day and flat-day performance. Pair the overview with daily errors and explain the small sample of price moves.
4. Trace the workflow from the CSV through cleaning, lagging, chronological splitting, per-algorithm training and scoring. Identify source files and distinguish saved-model evidence from available training scripts.
5. Create a dedicated analysis gallery. Include every available saved notebook figure in notebook order with provenance, and clearly label CSV-derived analysis and the comparison script’s figure. The checkout currently contains no notebook. Report unavailable or unsupported outputs honestly.
6. Validate both fuels against the reference figures above, the first forecast boundary, keyboard and mobile chart inspection, and unavailable data states. Document start, build, refresh, and gallery import commands.
