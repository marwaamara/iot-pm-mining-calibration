"""
Main experimental runner.

Runs all calibration models on TWO datasets:
    * KAPSARC Riyadh + simulated PMS5003   (semi-synthetic case, PM2.5)
    * Kelly et al. 2023 Salt Lake Valley   (real co-located case, PM10)

For each (dataset, model) pair, this driver computes the GUM/JCGM-101
uncertainty budget defined in `uncertainty.py`.

Outputs (under results/{tables,figures}):
    * tables/calibration_results_kapsarc.csv     (PM2.5)
    * tables/calibration_results_slv.csv         (PM10, Salt Lake Valley)
    * tables/uncertainty_budget_full.csv         (long-format components)
    * tables/uncertainty_budget_full.tex         (LaTeX, both datasets)
    * figures/oof_residuals_<model>.csv          (per-sample OOF residuals)
"""

from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYTHONIOENCODING"] = "utf-8"

# Repo layout: this file lives under github/code/, so the repo root is one
# level up. We do not need any sys.path hacks because the other code modules
# live in the same directory as this script.
REPO_ROOT = Path(__file__).resolve().parents[1]

from config import (RANDOM_SEED, REF_UNCERTAINTY, SENSOR_NOISE_STD,
                    COVERAGE_FACTOR_K, N_FOLDS)
from models import (AffineCalibration, MLRCalibration, RFCalibration,
                    GBRCalibration, ANNCalibration,
                    compute_metrological_metrics)
from uncertainty import gum_budget, stratified_uncertainty, UncertaintyBudget


TABLES_DIR = REPO_ROOT / "tables"
CURVES_DIR = REPO_ROOT / "curves"
TABLES_DIR.mkdir(exist_ok=True)
CURVES_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Dataset loaders
# ---------------------------------------------------------------------------

KAPSARC_CSV = REPO_ROOT / "data" / "kapsarc" / "mining_pm_sensor_data.csv"
SLV_CSV = REPO_ROOT / "data" / "salt_lake_valley" / "salt_lake_valley_clean.csv"


def load_kapsarc(sensor_id: int = 1, pm: str = "pm25") -> dict:
    df = pd.read_csv(KAPSARC_CSV)
    df = df.dropna(subset=[f"sensor{sensor_id}_{pm}", f"ref_{pm}",
                           "temperature_C", "humidity_pct", "wind_speed_ms"])
    feats = np.column_stack([
        df[f"sensor{sensor_id}_{pm}"].values,
        df["temperature_C"].values,
        df["humidity_pct"].values,
        df["wind_speed_ms"].values,
        df["day"].values,
        df["hour_of_day"].values,
    ])
    y = df[f"ref_{pm}"].values

    # Per-sample reference uncertainty (2 % of x_ref per BAM spec; floor 0.5)
    u_ref = np.maximum(REF_UNCERTAINTY * y, 0.5)

    sigma_inputs = [
        SENSOR_NOISE_STD,    # raw sensor PM
        0.5,                 # T (deg C)
        2.0,                 # RH (%)
        0.5,                 # wind (m/s)
        0.0, 0.0,            # day, hour have no measurement uncertainty
    ]
    return {
        "name": "KAPSARC", "pm": pm,
        "X": feats, "y": y, "u_ref": u_ref, "sigma_inputs": sigma_inputs,
        "feature_names": ["sensor_raw", "temperature_C", "humidity_pct",
                          "wind_speed_ms", "day", "hour_of_day"],
        "df": df,
    }


def load_slv(sensor_id: int = 1) -> dict:
    df = pd.read_csv(SLV_CSV)
    df = df.dropna(subset=[f"sensor{sensor_id}_pm10", "ref_pm10",
                           "temperature_C", "humidity_pct", "wind_speed_ms"])
    feats = np.column_stack([
        df[f"sensor{sensor_id}_pm10"].values,
        df["temperature_C"].values,
        df["humidity_pct"].values,
        df["wind_speed_ms"].values,
        df["day"].values,
        df["hour_of_day"].values,
    ])
    y = df["ref_pm10"].values

    # FEM reference uncertainty: per Met One BAM-1020 / Thermo TEOM-FDMS spec,
    # ~ +/- 5 % at 24h average; we use 5 % * y, floor 1 ug/m^3.
    u_ref = np.maximum(0.05 * y, 1.0)

    sigma_inputs = [
        3.0,    # PMS5003 raw noise on PM10 channel (Plantower spec)
        0.5,    # T
        2.0,    # RH
        0.5,    # wind
        0.0, 0.0,
    ]
    return {
        "name": "SaltLakeValley", "pm": "pm10",
        "X": feats, "y": y, "u_ref": u_ref, "sigma_inputs": sigma_inputs,
        "feature_names": ["sensor_raw", "temperature_C", "humidity_pct",
                          "wind_speed_ms", "day", "hour_of_day"],
        "df": df,
    }


# ---------------------------------------------------------------------------
# Model registry — fresh-instance factories so each CV fold is independent
# ---------------------------------------------------------------------------

def model_factory(name: str):
    if name == "Affine":
        return lambda: AffineCalibration()
    if name == "MLR":
        return lambda: MLRCalibration()
    if name == "RF":
        return lambda: RFCalibration()
    if name == "GBR":
        return lambda: GBRCalibration()
    if name == "ANN":
        return lambda: ANNCalibration()
    raise ValueError(name)


MODELS = ["Affine", "MLR", "RF", "GBR", "ANN"]
# CNN is intentionally excluded: the 1D-CNN architecture requires
# sequential alignment that does not survive temporal CV folds without
# data leakage. Including it would be either unfair (no fold isolation)
# or unstable (re-running with sequence padding). We treat the exclusion
# as a model-design limitation.


def make_callbacks(name):
    """Return (fit_predict, predict_only) for a freshly fitted model on
    full training set, plus a callable that fits inside CV folds."""
    factory = model_factory(name)

    def fit_predict(X_tr, y_tr, X_te):
        m = factory()
        m.fit(X_tr, y_tr)
        return m.predict(X_te)

    return factory, fit_predict


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run_one(dataset: dict, model_name: str,
            test_split: float = 0.2, k: int = N_FOLDS, M: int = 1500,
            split_kind: str = "temporal", n_seeds: int = 1) -> dict:
    """Train one model on one dataset, compute full GUM budget.

    split_kind : "temporal" (last test_split fraction) or "random" (shuffled).
    n_seeds    : if >1, train n_seeds ANNs and average predictions
                 (only meaningful for stochastic models). Bagging-style
                 ensembling per Caruana 2004 / Lakshminarayanan 2017.
    """
    np.random.seed(RANDOM_SEED)

    X = dataset["X"]
    y = dataset["y"]
    u_ref = dataset["u_ref"]
    sigma_inputs = dataset["sigma_inputs"]

    n = len(y)
    if split_kind == "random":
        rng = np.random.default_rng(RANDOM_SEED)
        order = rng.permutation(n)
        n_te = int(n * test_split)
        te_idx = order[:n_te]
        tr_idx = order[n_te:]
    else:
        split = int(n * (1 - test_split))
        tr_idx = np.arange(split)
        te_idx = np.arange(split, n)

    X_tr, X_te = X[tr_idx], X[te_idx]
    y_tr, y_te = y[tr_idx], y[te_idx]
    if hasattr(u_ref, "__len__"):
        u_ref_tr = u_ref[tr_idx]; u_ref_te = u_ref[te_idx]
    else:
        u_ref_tr = u_ref;          u_ref_te = u_ref

    # Train final model(s) on full training set (used by predict_only)
    factory, _ = make_callbacks(model_name)
    final_models = []
    for s in range(n_seeds):
        np.random.seed(RANDOM_SEED + s)
        try:
            import tensorflow as _tf
            _tf.random.set_seed(RANDOM_SEED + s)
        except Exception:
            pass
        m = factory()
        m.fit(X_tr, y_tr)
        final_models.append(m)

    def predict_only(X_):
        preds = np.mean([fm.predict(X_) for fm in final_models], axis=0)
        return preds

    # OOF fit_predict ensembles per fold too (only for ANN; cheap models stay deterministic)
    if n_seeds > 1 and model_name == "ANN":
        def fit_predict(X_tr_f, y_tr_f, X_te_f):
            preds = []
            for s in range(n_seeds):
                np.random.seed(RANDOM_SEED + 17 * s)
                try:
                    import tensorflow as _tf
                    _tf.random.set_seed(RANDOM_SEED + 17 * s)
                except Exception:
                    pass
                m = factory()
                m.fit(X_tr_f, y_tr_f)
                preds.append(m.predict(X_te_f))
            return np.mean(preds, axis=0)
    else:
        _, fit_predict = make_callbacks(model_name)

    # Run uncertainty pipeline
    t0 = time.time()
    budget, y_pred_corr, r_oof = gum_budget(
        fit_predict=fit_predict,
        predict_only=predict_only,
        X_train=X_tr, y_train=y_tr,
        X_test=X_te, y_test=y_te,
        u_ref=u_ref_tr,
        sigma_inputs=sigma_inputs,
        k=k, M=M,
        coverage_factor=COVERAGE_FACTOR_K,
        target_coverage=0.95,
        rng_seed=RANDOM_SEED,
    )
    t_fit = time.time() - t0

    # Metrological metrics on bias-corrected test predictions
    metrics = compute_metrological_metrics(y_te, y_pred_corr, model_name)

    # Save OOF residuals (for diagnostics / overfit panel)
    pd.DataFrame({"r_oof": r_oof}).to_csv(
        CURVES_DIR / f"oof_residuals_{dataset['name']}_{model_name}_{split_kind}.csv",
        index=False
    )

    return {
        "dataset": dataset["name"],
        "pm": dataset["pm"],
        "model": model_name,
        "split": split_kind,
        "n_seeds": n_seeds,
        "n_train": int(len(tr_idx)),
        "n_test": int(len(te_idx)),
        "RMSE": metrics["RMSE (ug/m3)"],
        "MAE": metrics["MAE (ug/m3)"],
        "R2": metrics["R2"],
        "MBE_test": metrics["MBE (ug/m3)"],
        "u_A_model": round(budget.u_A_model, 3),
        "u_input_MC": round(budget.u_input_MC, 3),
        "u_B_bias": round(budget.u_B_bias, 3),
        "u_c": round(budget.u_c, 3),
        "U": round(budget.U, 3),
        "raw_oof_std": round(budget.raw_oof_std, 3),
        "bias_correction": round(budget.bias_correction, 3),
        "coverage_actual": round(budget.coverage_actual, 4),
        "coverage_target": budget.coverage_target,
        "k_empirical": round(budget.k_empirical, 3),
        "fit_seconds": round(t_fit, 1),
    }


def run_dataset(dataset: dict, split_kind: str = "temporal",
                n_seeds_ann: int = 1) -> pd.DataFrame:
    print(f"\n{'='*72}")
    print(f"  Running models on {dataset['name']}  ({dataset['pm'].upper()})  "
          f"split={split_kind}  ann_seeds={n_seeds_ann}")
    print(f"  Samples: {len(dataset['y'])}    "
          f"y range: [{dataset['y'].min():.1f}, {dataset['y'].max():.1f}] ug/m^3")
    print(f"{'='*72}")

    rows = []
    n = len(dataset["y"])
    if split_kind == "random":
        rng = np.random.default_rng(RANDOM_SEED)
        order = rng.permutation(n)
        n_te = int(n * 0.2)
        te_idx = order[:n_te]
        raw_te = dataset["X"][te_idx, 0]; y_te = dataset["y"][te_idx]
        n_train = n - n_te; n_test = n_te
    else:
        split = int(n * 0.8)
        raw_te = dataset["X"][split:, 0]; y_te = dataset["y"][split:]
        n_train = split; n_test = n - split

    base = compute_metrological_metrics(y_te, raw_te, "Uncalibrated")
    rows.append({
        "dataset": dataset["name"], "pm": dataset["pm"], "model": "Uncalibrated",
        "split": split_kind, "n_seeds": 1,
        "n_train": n_train, "n_test": n_test,
        "RMSE": base["RMSE (ug/m3)"], "MAE": base["MAE (ug/m3)"],
        "R2": base["R2"], "MBE_test": base["MBE (ug/m3)"],
        "u_A_model": base["u_A (ug/m3)"], "u_input_MC": 0.0, "u_B_bias": 0.0,
        "u_c": base["u_A (ug/m3)"], "U": base["U_expanded (ug/m3)"],
        "raw_oof_std": base["u_A (ug/m3)"], "bias_correction": 0.0,
        "coverage_actual": base["Within U (%)"] / 100.0,
        "coverage_target": 0.95, "k_empirical": np.nan, "fit_seconds": 0.0,
    })

    for m_name in MODELS:
        seeds = n_seeds_ann if m_name == "ANN" else 1
        print(f"\n[{m_name}] training + GUM budget (seeds={seeds}) ...", flush=True)
        try:
            r = run_one(dataset, m_name, split_kind=split_kind, n_seeds=seeds)
            rows.append(r)
            print(f"  RMSE={r['RMSE']:.2f}  R2={r['R2']:.4f}  "
                  f"u_A={r['u_A_model']:.2f}  u_in={r['u_input_MC']:.2f}  "
                  f"U={r['U']:.2f}  cov={r['coverage_actual']:.1%}  "
                  f"({r['fit_seconds']:.0f}s)")
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback; traceback.print_exc()
            rows.append({"dataset": dataset["name"], "model": m_name,
                         "error": str(e)})

    return pd.DataFrame(rows)


def main():
    overall_t0 = time.time()
    print("Loading datasets ...")
    ds_kapsarc = load_kapsarc(sensor_id=1, pm="pm25")
    ds_slv = load_slv(sensor_id=1)
    print(f"  KAPSARC: {len(ds_kapsarc['y'])} samples")
    print(f"  SLV:     {len(ds_slv['y'])} samples")

    # KAPSARC: temporal split (large dataset; events distributed; matches submission)
    df_k = run_dataset(ds_kapsarc, split_kind="temporal", n_seeds_ann=1)

    # SLV: report BOTH splits (R2 item 1 explicitly asks for this).
    # Headline numbers use random split — small dataset (n=693) with dust events
    # concentrated April 1-25 makes temporal split structurally biased
    # (P95(train)=84 vs P95(test)=48 ug/m^3). ANN trained over 3 seeds
    # for stability per standard small-data practice.
    print("\n>>> SLV pass 1: random split (headline)")
    df_s_rand = run_dataset(ds_slv, split_kind="random", n_seeds_ann=3)
    print("\n>>> SLV pass 2: temporal split (for R2 item 1 comparison)")
    df_s_temp = run_dataset(ds_slv, split_kind="temporal", n_seeds_ann=3)
    df_s = pd.concat([df_s_rand, df_s_temp], ignore_index=True)

    # Save per-dataset tables
    df_k.to_csv(TABLES_DIR / "calibration_results_kapsarc.csv", index=False)
    df_s.to_csv(TABLES_DIR / "calibration_results_slv.csv", index=False)
    df_s_rand.to_csv(TABLES_DIR / "calibration_results_slv_random.csv", index=False)
    df_s_temp.to_csv(TABLES_DIR / "calibration_results_slv_temporal.csv", index=False)

    # Combined long-format budget
    combined = pd.concat([df_k, df_s], ignore_index=True)
    combined.to_csv(TABLES_DIR / "uncertainty_budget_full.csv", index=False)

    # LaTeX (compact)
    cols_tex = ["dataset", "split", "model", "RMSE", "R2", "MBE_test",
                "u_A_model", "u_input_MC", "u_B_bias", "u_c", "U",
                "coverage_actual"]
    df_tex = combined[cols_tex].copy()
    df_tex["coverage_actual"] = (df_tex["coverage_actual"] * 100).round(2)
    with open(TABLES_DIR / "uncertainty_budget_full.tex", "w",
              encoding="utf-8") as f:
        f.write("% GUM/JCGM-101 uncertainty budget — full revision pipeline\n")
        f.write(df_tex.to_latex(index=False, float_format="%.2f"))

    print(f"\n{'='*72}")
    print(f"  Done. Total time: {time.time() - overall_t0:.0f}s")
    print(f"  Tables -> {TABLES_DIR}")
    print(f"  OOF residuals -> {CURVES_DIR}")
    print(f"{'='*72}")
    print()
    print("Headline (KAPSARC, PM2.5, temporal split):")
    print(df_k[["model", "RMSE", "R2", "u_c", "U", "coverage_actual"]]
          .to_string(index=False))
    print("\nHeadline (Salt Lake Valley, PM10, RANDOM split, ANN 3 seeds):")
    print(df_s_rand[["model", "RMSE", "R2", "u_c", "U", "coverage_actual"]]
          .to_string(index=False))
    print("\nFor R2 item 1 (Salt Lake Valley, temporal split):")
    print(df_s_temp[["model", "RMSE", "R2", "u_c", "U", "coverage_actual"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
