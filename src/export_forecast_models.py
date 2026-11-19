"""Export the fitted notebook estimators for forecasting in the static Vue dashboard."""
import json

from gas_common import (PROJECT_ROOT, START_DATE, STUDY_MODEL_AUTHORS, TARGETS,
                        load_model_bundle, model_bundle_path)


def pack_tree(left, right, features, thresholds, leaves, node=0):
    """Each branch holds a feature index, threshold and two child nodes."""
    if left[node] < 0:
        return float(leaves[node])
    return [int(features[node]), float(thresholds[node]),
            pack_tree(left, right, features, thresholds, leaves, left[node]),
            pack_tree(left, right, features, thresholds, leaves, right[node])]


def export_estimator(name, model):
    if name == "Linear Regression":
        scaler, regression = model.steps[0][1], model.steps[1][1]
        return dict(mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(),
                    coefficients=regression.coef_.tolist(), intercept=float(regression.intercept_))
    if name == "Random Tree":
        if model.feature_mode != "levels":
            raise ValueError("Expected the notebook's level-input Random Tree")
        tree = model.tree_.tree_
        support = tree.weighted_n_node_samples
        change = ((support * tree.value[:, 0, 0] + model.leaf_smoothing * model.global_change_)
                  / (support + model.leaf_smoothing))
        return dict(tree=pack_tree(tree.children_left, tree.children_right, tree.feature,
                                   tree.threshold, model.change_weight * change))
    if name == "XGBoost":
        learner = json.loads(model.model_.get_booster().save_raw(raw_format="json"))["learner"]
        booster = learner["gradient_booster"]
        if booster["name"] != "gbtree" or learner["objective"]["name"] != "reg:squarederror":
            raise ValueError("Expected the notebook's squared-error boosted trees")
        trees = []
        for tree in booster["model"]["trees"]:
            if any(tree["split_type"]):
                raise ValueError("Expected numeric splits")
            trees.append(pack_tree(tree["left_children"], tree["right_children"], tree["split_indices"],
                                   tree["split_conditions"], tree["split_conditions"]))
        return dict(base=json.loads(learner["learner_model_param"]["base_score"])[0], trees=trees)
    raise ValueError(f"Unsupported notebook model {name}")


def main():
    models = {}
    for name, author in STUDY_MODEL_AUTHORS.items():
        models[name] = {}
        for target in TARGETS:
            path = model_bundle_path(target, name, author)
            bundle = load_model_bundle(path)
            if (bundle["model_name"], bundle["author"], bundle["target"]) != (name, author, target):
                raise ValueError(f"{path.name}: bundle metadata does not match its filename")
            models[name][target] = {
                "author": author, "features": bundle["features"],
                **export_estimator(name, bundle["model"]),
            }
    output = PROJECT_ROOT / "dashboard/public/study/forecast-models.json"
    output.write_text(json.dumps({"startDate": START_DATE.date().isoformat(), "models": models},
                                 separators=(",", ":"), allow_nan=False) + "\n")
    print(f"Exported six fitted estimators to {output}")


if __name__ == "__main__":
    main()
