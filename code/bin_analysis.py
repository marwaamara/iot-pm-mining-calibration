"""
Concentration-bin error analysis (Reviewer 2 item 18).

The submitted manuscript reports negative R^2 in some concentration bins, which
R2 reads as overfitting. The likely actual cause is the well-known
*small-sample variance trap*: R^2 is undefined when sample variance is small
relative to error variance, regardless of model quality. We investigate by:

  (a) Recomputing per-bin RMSE/MAE/MBE/R^2 with bin sample-counts
  (b) Reporting per-bin standard deviation of the *reference* (not just the
      residuals) — a small ref-std produces apparent negative R^2 even with
      modest residuals.
  (c) Adding bootstrap 95 % CIs for R^2 to flag bins where R^2 is unstable.
  (d) Recommending alternative bin metrics: NRMSE = RMSE / mean(y_ref) and
      MAE/mean(y_ref), which are well-defined regardless of sample variance.
"""

from __future__ import annotations

import os, sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

from run_revision import load_kapsarc, load_slv

TABLES = REPO_ROOT / "results" / "tables"


def per_bin_metrics(y_true, y_pred, bins):
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (y_true >= lo) & (y_true < hi)
        n = int(m.sum())
        if n < 2:
            rows.append({"bin": f"[{lo}, {hi})", "n": n})
            continue
        yt, yp = y_true[m], y_pred[m]
        r = yp - yt
        ref_std = float(np.std(yt, ddof=1)) if n > 1 else float("nan")
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        mae = float(mean_absolute_error(yt, yp))
        mbe = float(np.mean(r))
        r2 = float(r2_score(yt, yp)) if ref_std > 0 else float("nan")
        # Bootstrap 95 % CI for R^2
        rng = np.random.default_rng(0)
        boot = []
        for _ in range(500):
            idx = rng.integers(0, n, size=n)
            ytb, ypb = yt[idx], yp[idx]
            if np.std(ytb, ddof=1) > 0:
                boot.append(r2_score(ytb, ypb))
        r2_lo = float(np.quantile(boot, 0.025)) if boot else float("nan")
        r2_hi = float(np.quantile(boot, 0.975)) if boot else float("nan")
        rows.append({
            "bin": f"[{lo}, {hi})", "n": n,
            "ref_mean": float(np.mean(yt)),
            "ref_std":  ref_std,
            "RMSE":     rmse,
            "MAE":      mae,
            "MBE":      mbe,
            "R2":       r2,
            "R2_lo":    r2_lo,
            "R2_hi":    r2_hi,
            "NRMSE_pct": 100.0 * rmse / max(np.mean(yt), 1e-9),
            "NMAE_pct":  100.0 * mae  / max(np.mean(yt), 1e-9),
        })
    return pd.DataFrame(rows)


def main():
    out_rows = []
    for label, ds, bins in [
        ("kapsarc", load_kapsarc(),
         [0, 25, 50, 75, 100, 150, 1e9]),
        ("slv", load_slv(),
         [0, 20, 50, 100, 200, 1e9]),
    ]:
        X, y = ds["X"], ds["y"]
        # Use temporal split + GBR (most robust across both datasets in earlier runs)
        n = len(y)
        s = int(n * 0.8)
        Xtr, ytr, Xte, yte = X[:s], y[:s], X[s:], y[s:]
        sc = StandardScaler(); Xs_tr = sc.fit_transform(Xtr); Xs_te = sc.transform(Xte)
        m = GradientBoostingRegressor(n_estimators=200, max_depth=8,
                                      learning_rate=0.05, subsample=0.8,
                                      random_state=42)
        m.fit(Xs_tr, ytr)
        yp_te = m.predict(Xs_te)

        df_b = per_bin_metrics(yte, yp_te, bins)
        df_b.insert(0, "dataset", label)
        out_rows.append(df_b)

    full = pd.concat(out_rows, ignore_index=True)
    full.to_csv(TABLES / "concentration_bin_analysis.csv", index=False)
    print(full.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))
    print()
    print(">>> Reading: bins where ref_std is small relative to RMSE will show")
    print("    negative R^2 even with reasonable error — these flags are NOT")
    print("    overfitting evidence. Use NRMSE_pct as the bin-level metric instead.")


if __name__ == "__main__":
    main()
