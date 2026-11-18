"""Shared wrapper classes. Must be shared with the team: pickled models import from here."""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone


class DeltaRegressor(BaseEstimator, RegressorMixin):
    """Learn the CHANGE from yesterday (y - lag_1); predict() adds lag_1 back.

    Lets tree models (XGBoost, Random Forest) predict prices outside the training range.
    X must contain a 'lag_1' column.
    """
    def __init__(self, estimator=None):
        self.estimator = estimator

    def fit(self, X, y):
        self.model_ = clone(self.estimator).fit(X, np.asarray(y) - X["lag_1"].to_numpy())
        return self

    def predict(self, X):
        return X["lag_1"].to_numpy() + self.model_.predict(X)
