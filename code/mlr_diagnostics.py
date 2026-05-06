"""
MLR diagnostics for Reviewer 2 items 7 and 17:
    Replace plain R^2 with adjusted R^2; report partial correlation
    coefficients and Variance-Inflation Factors (VIF) for each predictor.

Reference framing: GUM Annex H.6 (multiple regression) + ISO 5725-3.
"""

from __future__ import annotations

import os, sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

from run_revision import load_kapsarc, load_slv

TABLES = REPO_ROOT / "results" / "tables"
TABLES.mkdir(exist_ok=True)


def adjusted_r2(r2: float, n: int, p: int) -> float:
    """Adjusted R-squared, conventional formula."""
    if n - p - 1 <= 0:
        return float("nan")
    return 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1)


def vif(X: np.ndarray) -> np.ndarray:
    """Variance Inflation Factor for each predictor column.
    VIF_j = 1 / (1 - R^2_j) where R^2_j regresses x_j on the other columns."""
    n, p = X.shape
    out = np.zeros(p)
    for j in range(p):
        others = np.column_stack([X[:, k] for k in range(p) if k != j])
        m = LinearRegression().fit(others, X[:, j])
        r2_j = m.score(others, X[:, j])
        out[j] = 1.0 / max(1.0 - r2_j, 1e-12)
    return out


def partial_corr(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Partial correlation between each x_j and y, controlling for the other xs.
    Computed via residualization: r(e_xj | -j, e_y | -j).
    """
    n, p = X.shape
    out = np.zeros(p)
    for j in range(p):
        others = np.column_stack([X[:, k] for k in range(p) if k != j])
        # Residualise x_j and y against the other predictors
        m_x = LinearRegression().fit(others, X[:, j])
        e_x = X[:, j] - m_x.predict(others)
        m_y = LinearRegression().fit(others, y)
        e_y = y - m_y.predict(others)
        out[j] = float(np.corrcoef(e_x, e_y)[0, 1])
    return out


def run(dataset: dict, label: str) -> pd.DataFrame:
    X = dataset["X"]; y = dataset["y"]; names = dataset["feature_names"]

    n_total = len(y)
    n_tr = int(n_total * 0.8)
    X_tr, y_tr = X[:n_tr], y[:n_tr]
    X_te, y_te = X[n_tr:], y[n_tr:]

    sc = StandardScaler(); Xs_tr = sc.fit_transform(X_tr); Xs_te = sc.transform(X_te)
    m = LinearRegression().fit(Xs_tr, y_tr)
    yp_tr = m.predict(Xs_tr); yp_te = m.predict(Xs_te)

    r2_tr = r2_score(y_tr, yp_tr); r2_te = r2_score(y_te, yp_te)
    p = X.shape[1]
    adj_tr = adjusted_r2(r2_tr, len(y_tr), p)
    adj_te = adjusted_r2(r2_te, len(y_te), p)

    pcorrs = partial_corr(Xs_tr, y_tr)
    vifs = vif(Xs_tr)

    rows = []
    for j, nm in enumerate(names):
        rows.append({
            "dataset": label, "feature": nm,
            "coef_std": float(m.coef_[j]),
            "partial_corr": float(pcorrs[j]),
            "VIF": float(vifs[j]),
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / f"mlr_partial_corr_{label}.csv", index=False)

    print(f"\n{label}: MLR — train n={len(y_tr)}, test n={len(y_te)}, p={p}")
    print(f"  R^2 (train) = {r2_tr:.4f}    Adjusted R^2 = {adj_tr:.4f}")
    print(f"  R^2 (test)  = {r2_te:.4f}    Adjusted R^2 = {adj_te:.4f}")
    print()
    print(summary.to_string(index=False, float_format=lambda x: f"{x:8.4f}"))

    # Also append a summary row
    summary_row = pd.DataFrame([{
        "dataset": label, "feature": "_summary",
        "R2_train": r2_tr, "AdjR2_train": adj_tr,
        "R2_test": r2_te, "AdjR2_test": adj_te,
        "n_train": len(y_tr), "n_test": len(y_te), "p": p,
    }])
    summary_row.to_csv(TABLES / f"mlr_summary_{label}.csv", index=False)
    return summary


if __name__ == "__main__":
    dk = load_kapsarc(); ds = load_slv()
    run(dk, "kapsarc")
    run(ds, "slv")
