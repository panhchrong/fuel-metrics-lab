"""Importable estimator needed when loading the Random Tree bundles."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.tree import DecisionTreeRegressor
from sklearn.utils.validation import check_is_fitted


class RandomTreeChangeRegressor(RegressorMixin, BaseEstimator):
    """Yesterday's price plus a regularized tree estimate of its change."""

    def __init__(self, max_depth=3, min_samples_leaf=10, change_weight=0.5,
                 random_state=42, feature_mode="relative", target_clip=None,
                 history_window=None, leaf_smoothing=0.):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.change_weight = change_weight
        self.random_state = random_state
        self.feature_mode = feature_mode
        self.target_clip = target_clip
        self.history_window = history_window
        self.leaf_smoothing = leaf_smoothing

    def _tree_features(self, X):
        if self.feature_mode == "levels":
            return X
        if self.feature_mode not in ("relative", "momentum", "calendar"):
            raise ValueError("feature_mode must be levels, relative, momentum or calendar")
        # Differences transfer across price levels; no new external data is used.
        features = X.copy()
        for column in ("lag_7", "other_lag_1", "roll_mean_7"):
            if column in features:
                features[column] = X["lag_1"] - X[column]
        features = features.drop(columns="lag_1")
        if self.feature_mode == "momentum":
            features = features.drop(columns=["day_index", "month"], errors="ignore")
        if self.feature_mode == "calendar":
            dates = pd.Timestamp("2026-03-08") + pd.to_timedelta(X["day_index"], unit="D")
            features["day_of_month"] = dates.dt.day
            features["day_in_ten_day_cycle"] = dates.dt.day % 10
        return features

    def fit(self, X, y):
        if not 0 < self.change_weight <= 1:
            raise ValueError("change_weight must be positive and at most 1; no baseline fallback")
        if self.leaf_smoothing < 0:
            raise ValueError("leaf_smoothing must be nonnegative")
        if self.history_window is not None:
            X, y = X.iloc[-self.history_window:], y.iloc[-self.history_window:]
        change = y - X["lag_1"]
        if self.target_clip is not None:
            change = np.clip(change, -self.target_clip, self.target_clip)
        self.tree_ = DecisionTreeRegressor(
            splitter="random", max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf, random_state=self.random_state,
        )
        self.tree_.fit(self._tree_features(X), change)
        self.global_change_ = float(np.mean(change))
        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = X.columns.to_numpy()
        return self

    def predict(self, X):
        check_is_fitted(self, "tree_")
        features = self._tree_features(X)
        change = self.tree_.predict(features)
        if self.leaf_smoothing:
            support = self.tree_.tree_.weighted_n_node_samples[self.tree_.apply(features)]
            change = (support * change + self.leaf_smoothing * self.global_change_) / (
                support + self.leaf_smoothing)
        return X["lag_1"].to_numpy() + self.change_weight * change
