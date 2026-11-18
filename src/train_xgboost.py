"""Train XGBoost (predicting the change from yesterday) for both fuels.
Run from the project folder:  python src/train_xgboost.py
"""
import argparse

from xgboost import XGBRegressor

from gas_common import MODELS_DIR, TARGETS, get_train_test, metrics, save_model_bundle
from gas_wrappers import DeltaRegressor

# ----------------------------------------------------- EDIT THIS PART
AUTHOR = "sokundo"
MODEL_NAME = "XGBoost (delta)"
FEATURES_USED = ["lag_1", "lag_7", "other_lag_1", "roll_mean_7"]  # must include "lag_1"; time features overfit


def make_model():
    return DeltaRegressor(XGBRegressor(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        min_child_weight=5, reg_lambda=10, random_state=42))
# ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(MODELS_DIR))
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
