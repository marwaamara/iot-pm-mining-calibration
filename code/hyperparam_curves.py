"""
Hyperparameter validation curves for tree-based calibrators.

Justifies the chosen hyperparameters (n_estimators / B = 200, max_depth) by
sweeping each one and plotting validation RMSE. The chosen value should sit on
the plateau, not on the climbing edge of the bias-variance trade-off.
"""

from __future__ import annotations

import os, sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import KFold

from run_revision import load_kapsarc, load_slv

CURVES = REPO_ROOT / "results" / "figures"
CURVES.mkdir(exist_ok=True)


def cv_rmse(model_factory, X, y, k=5, seed=42):
    kf = KFold(n_splits=k, shuffle=True, random_state=seed)
    rmses = []
    for tr, te in kf.split(X):
        sc = StandardScaler(); Xs_tr = sc.fit_transform(X[tr]); Xs_te = sc.transform(X[te])
        m = model_factory(); m.fit(Xs_tr, y[tr])
        yp = m.predict(Xs_te)
        rmses.append(np.sqrt(mean_squared_error(y[te], yp)))
    return float(np.mean(rmses)), float(np.std(rmses))


def sweep_rf_n(X, y, n_grid=(10, 25, 50, 100, 200, 400, 800), depth=15):
    rows = []
    for n in n_grid:
        mu, sd = cv_rmse(
            lambda: RandomForestRegressor(n_estimators=n, max_depth=depth,
                                          random_state=42, n_jobs=-1),
            X, y)
        rows.append({"sweep": "RF_n_estimators", "value": n,
                     "RMSE_mean": mu, "RMSE_std": sd})
    return pd.DataFrame(rows)


def sweep_rf_depth(X, y, d_grid=(2, 4, 6, 8, 10, 15, 20, 30, None), n=200):
    rows = []
    for d in d_grid:
        mu, sd = cv_rmse(
            lambda: RandomForestRegressor(n_estimators=n, max_depth=d,
                                          random_state=42, n_jobs=-1),
            X, y)
        rows.append({"sweep": "RF_max_depth",
                     "value": -1 if d is None else d,
                     "RMSE_mean": mu, "RMSE_std": sd})
    return pd.DataFrame(rows)


def sweep_gbr_n(X, y, n_grid=(50, 100, 200, 400, 800), depth=8):
    rows = []
    for n in n_grid:
        mu, sd = cv_rmse(
            lambda: GradientBoostingRegressor(n_estimators=n, max_depth=depth,
                                              learning_rate=0.05, subsample=0.8,
                                              random_state=42),
            X, y)
        rows.append({"sweep": "GBR_n_estimators", "value": n,
                     "RMSE_mean": mu, "RMSE_std": sd})
    return pd.DataFrame(rows)


def sweep_gbr_depth(X, y, d_grid=(2, 4, 6, 8, 10, 12, 16), n=200):
    rows = []
    for d in d_grid:
        mu, sd = cv_rmse(
            lambda: GradientBoostingRegressor(n_estimators=n, max_depth=d,
                                              learning_rate=0.05, subsample=0.8,
                                              random_state=42),
            X, y)
        rows.append({"sweep": "GBR_max_depth", "value": d,
                     "RMSE_mean": mu, "RMSE_std": sd})
    return pd.DataFrame(rows)


def main():
    for label, ds in [("kapsarc", load_kapsarc()), ("slv", load_slv())]:
        # KAPSARC is 23k rows; subsample for speed (still representative)
        X, y = ds["X"], ds["y"]
        if len(y) > 5000:
            rng = np.random.default_rng(42)
            idx = rng.choice(len(y), 5000, replace=False)
            X = X[idx]; y = y[idx]
            sub = " (subsampled to 5k for speed)"
        else:
            sub = ""
        print(f"\n{'='*72}\n  Hyperparameter sweeps for {label}{sub}\n{'='*72}")

        df = pd.concat([
            sweep_rf_n(X, y),
            sweep_rf_depth(X, y),
            sweep_gbr_n(X, y),
            sweep_gbr_depth(X, y),
        ], ignore_index=True)
        df.insert(0, "dataset", label)
        df.to_csv(CURVES / f"hyperparam_curves_{label}.csv", index=False)
        for sweep_name in df["sweep"].unique():
            sub_df = df[df["sweep"] == sweep_name].copy()
            print(f"\n[{sweep_name}]")
            print(sub_df[["value", "RMSE_mean", "RMSE_std"]]
                  .to_string(index=False, float_format=lambda x: f"{x:8.3f}"))


if __name__ == "__main__":
    main()
