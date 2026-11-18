"""TEMPLATE for teammates: train your algorithm and save it for the team comparison.

1. Copy this file, e.g. `src/train_random_forest.py`
2. Edit AUTHOR, MODEL_NAME, FEATURES_USED and make_model()
3. Run:  python src/train_random_forest.py
4. Your .pkl files appear in models/; then run:  python src/compare_models.py
"""
import argparse

from sklearn.ensemble import RandomForestRegressor

from gas_common import FEATURES, MODELS_DIR, TARGETS, get_train_test, metrics, save_model_bundle

# ----------------------------------------------------- EDIT THIS PART
AUTHOR = "your_name"
MODEL_NAME = "Random Forest"
FEATURES_USED = FEATURES            # or a subset, e.g. ["lag_1", "lag_7", "roll_mean_7"]


def make_model():
    """Return a NEW, unfitted scikit-learn estimator (a Pipeline is fine too)."""
    return RandomForestRegressor(n_estimators=300, random_state=42)
# ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(MODELS_DIR), help="where to save the .pkl files")
    args = parser.parse_args()

    for target in TARGETS:
        train, test = get_train_test(target)
        model = make_model().fit(train[FEATURES_USED], train["y"])
        score = metrics(test["y"], model.predict(test[FEATURES_USED]))
        path = save_model_bundle(model, model_name=MODEL_NAME, author=AUTHOR, target=target,
                                 features=FEATURES_USED, train=train, out_dir=args.out_dir)
        print(f"{target:11s} test RMSE={score['RMSE']:8.1f}  R2={score['R2']:.3f}  -> {path}")


if __name__ == "__main__":
    main()
