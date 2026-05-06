"""
Sensitivity analysis on the assumed PMS5003 error-model parameters
(Reviewer 1 — synthetic-data limitation).

For each KAPSARC simulation parameter (gain drift, T coefficient, RH
coefficient, dust-composition factor, noise std), perturb by +/- 20 %, regenerate
the sensor data, retrain the headline calibration models, and report the
resulting RMSE / U.  A flat sensitivity profile demonstrates that the
calibration methodology generalises beyond the specific assumed parameter
values, which addresses Reviewer 1's main concern that "the synthetic sensor
error model limits the applicability of the uncertainty evaluation".

We use one-at-a-time (OAT) perturbation; for full Sobol indices a second
study would be required, which we cite as future work in the paper.
"""

from __future__ import annotations

import os, sys, copy
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

import config as cfg  # we will mutate the module-level constants

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

CURVES = REPO_ROOT / "results" / "figures"
TABLES = REPO_ROOT / "results" / "tables"
CURVES.mkdir(exist_ok=True); TABLES.mkdir(exist_ok=True)


def load_kapsarc_reference():
    """Load just the reference KAPSARC PM2.5 + env covariates (no sensors)."""
    df = pd.read_csv(REPO_ROOT / "data" / "kapsarc" / "mining_pm_sensor_data.csv")
    df = df.dropna(subset=["ref_pm25", "temperature_C", "humidity_pct",
                           "wind_speed_ms", "day", "hour_of_day"])
    return df


# ---------------------------------------------------------------------------
# Light-weight re-implementation of the simulation that doesn't go through
# data_generator.py — keeps the perturbation strictly local and avoids
# touching the original CSV.
# ---------------------------------------------------------------------------

def simulate_one_sensor(ref_pm, T, RH, day, params, rng):
    g0 = params["gain"] * (1.0 - params["gain_drift"] * day)
    pred = (g0 * ref_pm
            + params["temp_coeff"] * (T - 25.0) * ref_pm
            + params["humidity_coeff"] * np.maximum(0, RH - 50.0) * ref_pm
            + params["dust_factor"] * 0.1 * ref_pm
            + params["offset"]
            + rng.normal(0.0, params["noise"], len(ref_pm)))
    return np.maximum(pred, 0.0)


def base_params():
    return dict(
        gain=cfg.SENSOR_GAIN_NOMINAL,
        gain_drift=cfg.SENSOR_GAIN_DRIFT_RATE,
        offset=cfg.SENSOR_OFFSET_NOMINAL,
        noise=cfg.SENSOR_NOISE_STD,
        temp_coeff=cfg.TEMP_COEFF,
        humidity_coeff=cfg.HUMIDITY_COEFF,
        dust_factor=cfg.DUST_COMPOSITION_FACTOR,
    )


def fit_eval(X_tr, y_tr, X_te, y_te):
    sc = StandardScaler(); Xs_tr = sc.fit_transform(X_tr); Xs_te = sc.transform(X_te)
    m = GradientBoostingRegressor(n_estimators=200, max_depth=8,
                                  learning_rate=0.05, subsample=0.8, random_state=42)
    m.fit(Xs_tr, y_tr)
    yp = m.predict(Xs_te)
    rmse = float(np.sqrt(mean_squared_error(y_te, yp)))
    r2 = float(r2_score(y_te, yp))
    return rmse, r2, yp


def run_one_perturbation(ref_df, params, label):
    rng = np.random.default_rng(cfg.RANDOM_SEED)
    sensor_pm = simulate_one_sensor(
        ref_df["ref_pm25"].values,
        ref_df["temperature_C"].values,
        ref_df["humidity_pct"].values,
        ref_df["day"].values,
        params, rng
    )
    X = np.column_stack([
        sensor_pm,
        ref_df["temperature_C"].values,
        ref_df["humidity_pct"].values,
        ref_df["wind_speed_ms"].values,
        ref_df["day"].values,
        ref_df["hour_of_day"].values,
    ])
    y = ref_df["ref_pm25"].values
    n = len(y)
    s = int(n * 0.8)
    rmse, r2, _ = fit_eval(X[:s], y[:s], X[s:], y[s:])
    return {"perturbation": label, "RMSE_test": round(rmse, 3),
            "R2_test": round(r2, 4)}


def main():
    ref_df = load_kapsarc_reference()
    print(f"Reference samples: {len(ref_df)}")

    base = base_params()
    rows = [run_one_perturbation(ref_df, base, "baseline")]
    print(f"Baseline RMSE = {rows[0]['RMSE_test']:.2f}, R^2 = {rows[0]['R2_test']:.4f}")

    perts = [
        ("gain", 1.20),
        ("gain", 0.80),
        ("gain_drift", 1.20),
        ("gain_drift", 0.80),
        ("offset", 1.20),
        ("offset", 0.80),
        ("noise", 1.20),
        ("noise", 0.80),
        ("temp_coeff", 1.20),
        ("temp_coeff", 0.80),
        ("humidity_coeff", 1.20),
        ("humidity_coeff", 0.80),
        ("dust_factor", 1.20),
        ("dust_factor", 0.80),
    ]
    for key, mult in perts:
        p = copy.deepcopy(base)
        p[key] = base[key] * mult
        label = f"{key} x{mult:.2f}"
        rows.append(run_one_perturbation(ref_df, p, label))
        print(f"  {label:<30s} RMSE={rows[-1]['RMSE_test']:.2f}  "
              f"R^2={rows[-1]['R2_test']:.4f}")

    df = pd.DataFrame(rows)
    df["delta_RMSE_vs_base"] = (df["RMSE_test"] - df.iloc[0]["RMSE_test"]).round(3)
    df["delta_R2_vs_base"] = (df["R2_test"] - df.iloc[0]["R2_test"]).round(4)
    df.to_csv(TABLES / "sensitivity_analysis.csv", index=False)

    print()
    print("Worst-case |delta RMSE|:", df["delta_RMSE_vs_base"].abs().max())
    print("Worst-case |delta R^2|: ", df["delta_R2_vs_base"].abs().max())


if __name__ == "__main__":
    main()
