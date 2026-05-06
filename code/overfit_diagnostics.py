"""
Overfitting diagnostics for tree- and ANN-based calibrators.

Produces three artefacts requested by Reviewer 2 (item 2):
  (1) Learning curves: train vs validation RMSE as a function of training-set size
  (2) Train-test RMSE gap for each model
  (3) Time-series nested cross-validation error distribution (gives an honest
      generalisation estimate that does not depend on a single split).

Outputs:
  curves/learning_curves_<dataset>.csv
  curves/train_test_gap_<dataset>.csv
  curves/nested_cv_<dataset>.csv
"""

from __future__ import annotations

import os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import tensorflow as tf
from tensorflow import keras

from run_revision import load_kapsarc, load_slv

CURVES = REPO_ROOT / "results" / "figures"
CURVES.mkdir(exist_ok=True)


def _ann(input_dim, hidden=(64, 32, 16), dropout=0.2, l2=0.0):
    reg = keras.regularizers.l2(l2) if l2 > 0 else None
    model = keras.Sequential([keras.layers.Input(shape=(input_dim,))])
    for h in hidden:
        model.add(keras.layers.Dense(h, activation="relu", kernel_regularizer=reg))
        if dropout > 0:
            model.add(keras.layers.Dropout(dropout))
    model.add(keras.layers.Dense(1))
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return model


# ---------------------------------------------------------------------------
def fit_predict_ann(X_tr, y_tr, X_te, n_seeds=1):
    sx, sy = StandardScaler(), StandardScaler()
    Xs = sx.fit_transform(X_tr)
    ys = sy.fit_transform(y_tr.reshape(-1, 1)).ravel()
    Xv = sx.transform(X_te)
    preds_te, preds_tr = [], []
    for s in range(n_seeds):
        tf.random.set_seed(42 + s); np.random.seed(42 + s)
        m = _ann(X_tr.shape[1])
        es = keras.callbacks.EarlyStopping(monitor="val_loss", patience=20,
                                           restore_best_weights=True)
        m.fit(Xs, ys, epochs=300, batch_size=64, verbose=0,
              validation_split=0.2, callbacks=[es])
        ps = m.predict(Xv, verbose=0).ravel()
        ps_tr = m.predict(Xs, verbose=0).ravel()
        preds_te.append(sy.inverse_transform(ps.reshape(-1, 1)).ravel())
        preds_tr.append(sy.inverse_transform(ps_tr.reshape(-1, 1)).ravel())
    return np.mean(preds_te, axis=0), np.mean(preds_tr, axis=0)


def fit_predict_sklearn(model_factory, X_tr, y_tr, X_te):
    sx = StandardScaler(); Xs = sx.fit_transform(X_tr)
    m = model_factory(); m.fit(Xs, y_tr)
    return m.predict(sx.transform(X_te)), m.predict(Xs)


# ---------------------------------------------------------------------------
# (1) Learning curves
# ---------------------------------------------------------------------------
def learning_curves(X, y, fractions=(0.1, 0.2, 0.4, 0.6, 0.8, 1.0),
                    test_frac=0.2, dataset_name="kapsarc"):
    n = len(y)
    rng = np.random.default_rng(42)
    order = rng.permutation(n)
    n_te = int(n * test_frac)
    te = order[:n_te]; tr_full = order[n_te:]
    X_te, y_te = X[te], y[te]

    rows = []
    factories = {
        "MLR": lambda: LinearRegression(),
        "RF":  lambda: RandomForestRegressor(n_estimators=200, max_depth=15,
                                              random_state=42, n_jobs=-1),
        "GBR": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=8,
                                                  learning_rate=0.05,
                                                  subsample=0.8, random_state=42),
    }
    for f in fractions:
        n_use = max(50, int(len(tr_full) * f))
        tr = tr_full[:n_use]
        X_tr, y_tr = X[tr], y[tr]
        for name, mf in factories.items():
            yp_te, yp_tr = fit_predict_sklearn(mf, X_tr, y_tr, X_te)
            rows.append({"dataset": dataset_name, "model": name,
                         "fraction": f, "n_train": len(tr),
                         "RMSE_train": np.sqrt(mean_squared_error(y_tr, yp_tr)),
                         "RMSE_test":  np.sqrt(mean_squared_error(y_te, yp_te)),
                         "R2_train":   r2_score(y_tr, yp_tr),
                         "R2_test":    r2_score(y_te, yp_te)})
        # ANN — heavy; only at the largest fractions
        if f >= 0.4:
            yp_te, yp_tr = fit_predict_ann(X_tr, y_tr, X_te, n_seeds=2)
            rows.append({"dataset": dataset_name, "model": "ANN",
                         "fraction": f, "n_train": len(tr),
                         "RMSE_train": np.sqrt(mean_squared_error(y_tr, yp_tr)),
                         "RMSE_test":  np.sqrt(mean_squared_error(y_te, yp_te)),
                         "R2_train":   r2_score(y_tr, yp_tr),
                         "R2_test":    r2_score(y_te, yp_te)})

    df = pd.DataFrame(rows)
    df.to_csv(CURVES / f"learning_curves_{dataset_name}.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# (2) Train-test gap (the simplest overfit signature)
# ---------------------------------------------------------------------------
def train_test_gap(X, y, test_frac=0.2, dataset_name="kapsarc"):
    n = len(y)
    rng = np.random.default_rng(42)
    order = rng.permutation(n)
    n_te = int(n * test_frac)
    te = order[:n_te]; tr = order[n_te:]
    X_tr, y_tr = X[tr], y[tr]; X_te, y_te = X[te], y[te]

    rows = []
    factories = {
        "MLR": lambda: LinearRegression(),
        "RF":  lambda: RandomForestRegressor(n_estimators=200, max_depth=15,
                                              random_state=42, n_jobs=-1),
        "GBR": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=8,
                                                  learning_rate=0.05,
                                                  subsample=0.8, random_state=42),
    }
    for name, mf in factories.items():
        yp_te, yp_tr = fit_predict_sklearn(mf, X_tr, y_tr, X_te)
        rmse_tr = float(np.sqrt(mean_squared_error(y_tr, yp_tr)))
        rmse_te = float(np.sqrt(mean_squared_error(y_te, yp_te)))
        rows.append({"dataset": dataset_name, "model": name,
                     "RMSE_train": rmse_tr, "RMSE_test": rmse_te,
                     "gap_RMSE": rmse_te - rmse_tr,
                     "R2_train": r2_score(y_tr, yp_tr),
                     "R2_test": r2_score(y_te, yp_te)})
    yp_te, yp_tr = fit_predict_ann(X_tr, y_tr, X_te, n_seeds=2)
    rmse_tr = float(np.sqrt(mean_squared_error(y_tr, yp_tr)))
    rmse_te = float(np.sqrt(mean_squared_error(y_te, yp_te)))
    rows.append({"dataset": dataset_name, "model": "ANN",
                 "RMSE_train": rmse_tr, "RMSE_test": rmse_te,
                 "gap_RMSE": rmse_te - rmse_tr,
                 "R2_train": r2_score(y_tr, yp_tr),
                 "R2_test": r2_score(y_te, yp_te)})

    df = pd.DataFrame(rows)
    df.to_csv(CURVES / f"train_test_gap_{dataset_name}.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# (3) Time-series nested CV (Beirlant-style nested k-fold)
# ---------------------------------------------------------------------------
def nested_ts_cv(X, y, outer_k=5, dataset_name="kapsarc"):
    n = len(y)
    edges = np.linspace(0, n, outer_k + 1, dtype=int)
    rows = []
    factories = {
        "MLR": lambda: LinearRegression(),
        "RF":  lambda: RandomForestRegressor(n_estimators=200, max_depth=15,
                                              random_state=42, n_jobs=-1),
        "GBR": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=8,
                                                  learning_rate=0.05,
                                                  subsample=0.8, random_state=42),
    }
    for fold in range(outer_k):
        te_lo, te_hi = edges[fold], edges[fold + 1]
        idx = np.arange(n)
        te = idx[te_lo:te_hi]
        tr = np.concatenate([idx[:te_lo], idx[te_hi:]])
        X_tr, y_tr = X[tr], y[tr]; X_te, y_te = X[te], y[te]
        for name, mf in factories.items():
            yp, _ = fit_predict_sklearn(mf, X_tr, y_tr, X_te)
            rows.append({"dataset": dataset_name, "fold": fold, "model": name,
                         "RMSE": float(np.sqrt(mean_squared_error(y_te, yp))),
                         "R2": float(r2_score(y_te, yp)),
                         "n_test": len(te)})
        yp, _ = fit_predict_ann(X_tr, y_tr, X_te, n_seeds=2)
        rows.append({"dataset": dataset_name, "fold": fold, "model": "ANN",
                     "RMSE": float(np.sqrt(mean_squared_error(y_te, yp))),
                     "R2": float(r2_score(y_te, yp)),
                     "n_test": len(te)})
    df = pd.DataFrame(rows)
    df.to_csv(CURVES / f"nested_cv_{dataset_name}.csv", index=False)
    return df


# ---------------------------------------------------------------------------
def main():
    ds_k = load_kapsarc(sensor_id=1, pm="pm25")
    ds_s = load_slv(sensor_id=1)

    for label, ds in [("kapsarc", ds_k), ("slv", ds_s)]:
        print(f"\n{'='*60}\n  Overfit diagnostics for {label}\n{'='*60}")
        print("\n[1/3] Learning curves ...")
        lc = learning_curves(ds["X"], ds["y"], dataset_name=label)
        print(lc[lc["fraction"] == 1.0].to_string(index=False))

        print("\n[2/3] Train-test gap ...")
        gap = train_test_gap(ds["X"], ds["y"], dataset_name=label)
        print(gap.to_string(index=False))

        print("\n[3/3] Nested time-series CV ...")
        nv = nested_ts_cv(ds["X"], ds["y"], outer_k=5, dataset_name=label)
        agg = nv.groupby("model")[["RMSE", "R2"]].agg(["mean", "std"]).round(3)
        print(agg)


if __name__ == "__main__":
    main()
