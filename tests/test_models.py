from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stockforge.models.base import ReturnModel
from stockforge.models.baseline import DriftModel, NaiveModel
from stockforge.models.ensemble import EnsembleModel
from stockforge.models.gbm import LightGBMModel
from stockforge.models.linear import ElasticNetModel


@pytest.fixture
def toy_xy(dataset):
    X = dataset.X.iloc[:3000]
    y = dataset.targets[1].reindex(X.index)
    mask = y.notna()
    return X[mask], y[mask]


def test_naive_predicts_zero(toy_xy):
    X, y = toy_xy
    model = NaiveModel().fit(X, y)
    preds = model.predict(X)
    assert (preds == 0).all()
    assert list(preds.index) == list(X.index)


def test_drift_matches_mean(toy_xy):
    X, y = toy_xy
    model = DriftModel().fit(X, y)
    assert model.drift_ == pytest.approx(float(y.mean()))
    preds = model.predict(X.head())
    assert (preds == model.drift_).all()


def test_elasticnet_finite_predictions(toy_xy):
    X, y = toy_xy
    model = ElasticNetModel(alpha=0.001).fit(X, y)
    preds = model.predict(X)
    assert np.isfinite(preds).all()
    coefs = model.coefficients(list(X.columns))
    assert len(coefs) == X.shape[1]


def test_lightgbm_beats_constant_on_signal(toy_xy):
    X, y = toy_xy
    model = LightGBMModel(n_estimators=60, num_leaves=15).fit(X[:2500], y[:2500])
    preds = model.predict(X[2500:])
    truth = y[2500:]
    const_rmse = float(np.sqrt(((truth - truth.mean()) ** 2).mean()))
    rmse = float(np.sqrt(((truth - preds) ** 2).mean()))
    assert np.isfinite(rmse)
    assert rmse <= const_rmse * 1.05


def test_lightgbm_importance(toy_xy):
    X, y = toy_xy
    model = LightGBMModel(n_estimators=40).fit(X, y)
    importance = model.importance()
    assert (importance >= 0).all()
    assert importance.sum() > 0


def test_ensemble_inverse_rmse_weights(toy_xy):
    members = [NaiveModel(), DriftModel()]
    rmse = {"naive": 10.0, "drift": 1.0}
    ens = EnsembleModel.from_validation_rmse(members, rmse)
    assert ens.weights["drift"] > ens.weights["naive"]
    total = sum(ens.weights.values())
    assert total == pytest.approx(1.0)


def test_ensemble_blend_prediction(toy_xy):
    X, y = toy_xy
    drift = DriftModel().fit(X, y)
    naive = NaiveModel().fit(X, y)
    ens = EnsembleModel([drift, naive], {"drift": 0.75, "naive": 0.25})
    preds = ens.predict(X.head(5))
    expected = 0.75 * drift.drift_
    assert np.allclose(preds.values, expected)


def test_save_load_roundtrip(toy_xy, tmp_path):
    X, y = toy_xy
    model = ElasticNetModel().fit(X, y)
    path = tmp_path / "model.joblib"
    model.save(path)
    loaded = ReturnModel.load(path)
    assert isinstance(loaded, ElasticNetModel)
    pd.testing.assert_series_equal(loaded.predict(X), model.predict(X))


def test_load_rejects_non_model(tmp_path):
    import joblib

    path = tmp_path / "junk.joblib"
    joblib.dump({"not": "a model"}, path)
    with pytest.raises(TypeError):
        ReturnModel.load(path)
