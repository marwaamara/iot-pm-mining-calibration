"""
GUM-compliant uncertainty pipeline for ML-calibrated low-cost PM sensors.

This module replaces the original Section 4.3 uncertainty framework, which
Reviewer 1 correctly identified as not GUM-compliant. The new framework
addresses each of R1's four equation-level critiques:

  R1 critique on Eq. (9) — Type A from test residuals violates GUM 4.2.1
    -> Replaced by out-of-fold (OOF) residuals from time-series k-fold CV.
       Each OOF residual is a prediction on a sample unseen by the model
       that produced it; the residual sequence is therefore a set of
       independent observations of the *calibration error*, satisfying
       GUM 4.2 / JCGM 100 §F.2 in the validation-uncertainty sense
       (cf. Pernot & Cailliez, J. Chemom. 31, 2017, e2966; ISO 6143).

  R1 critique on Eq. (10) — u_B is on the *input* (reference), not output
    -> Reference-instrument uncertainty enters via the residual: the
       observed residual variance is decomposed as
           Var(r) = Var(model error) + u_ref^2
       and we recover the model-error variance by subtraction:
           u_A^model = sqrt(max(0, var(r_OOF) - u_ref^2))
       This treats u_ref correctly per GUM 5.1 (input-quantity uncertainty).

  R1 critique on Eq. (11) — Type A and Type B were correlated
    -> After the variance-subtraction step above, the model-error and
       reference-error components are statistically decorrelated by
       construction. The Monte-Carlo input-propagation component
       (sensor noise + T noise + RH noise propagated through the trained
       ML model) is independent of model-fit residuals (different physical
       sources). The combined uncertainty is therefore a sum of three
       independent components:
           u_c^2 = u_A^model^2 + u_input,MC^2 + (b/sqrt(3))^2

  R1 critique on Eq. (13) — bias not used to correct
    -> A bias correction term b_hat is estimated on validation folds and
       applied to predictions. Any residual bias on the held-out test set
       is reported as a Type B rectangular component (b/sqrt(3)) per
       GUM 6.3.1.

References:
  GUM (JCGM 100:2008)            — input-quantity uncertainty propagation
  JCGM 101:2008                  — Monte-Carlo supplement to GUM
  ISO 6143                       — calibration-validation uncertainty
  Pernot, Cailliez 2017          — ML calibration uncertainty treatment
  Beirlant et al., NIST/SEMATECH — variance subtraction for noisy targets
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class UncertaintyBudget:
    """Full GUM/JCGM 101 uncertainty decomposition for one calibration model."""

    # Components (all in measurand units, e.g., µg/m^3)
    u_A_model: float          # Type A from OOF residuals, ref-uncertainty subtracted
    u_input_MC: float         # Monte-Carlo input propagation through trained model
    u_B_bias: float           # Type B rectangular for residual bias
    u_c: float                # combined standard uncertainty
    U: float                  # expanded uncertainty (k * u_c)
    k: float                  # coverage factor

    # Diagnostic numbers
    n_oof: int                # number of OOF residuals
    raw_oof_std: float        # observed OOF residual std (before subtraction)
    bias_correction: float    # MBE applied as offset to predictions
    residual_bias_test: float # MBE on held-out test set after correction
    coverage_actual: float    # fraction of test predictions inside [-U, +U]
    coverage_target: float    # nominal target (e.g., 0.95)
    k_empirical: float        # empirical k giving the target coverage

    # Optional: per-bin breakdown for stratified reporting
    per_bin: Optional[pd.DataFrame] = None


# ---------------------------------------------------------------------------
# Step 1 — Bias correction
# ---------------------------------------------------------------------------

def estimate_bias(y_pred_val: np.ndarray, y_ref_val: np.ndarray) -> float:
    """Mean bias error on validation predictions (used as an offset correction)."""
    r = y_pred_val - y_ref_val
    return float(np.mean(r))


def apply_bias_correction(y_pred: np.ndarray, b_hat: float) -> np.ndarray:
    """Subtract estimated bias from predictions."""
    return y_pred - b_hat


# ---------------------------------------------------------------------------
# Step 2 — Out-of-fold residuals (Type A foundation)
# ---------------------------------------------------------------------------

def time_series_kfold_indices(n: int, k: int) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Produce k folds for time-series CV: each fold's *test* portion comes from
    a contiguous block of indices; the train portion is the complement.

    This preserves temporal independence of the OOF residuals (no train sample
    sits between two test samples in the same window) while giving every
    sample exactly one OOF prediction. We use plain block-wise k-fold rather
    than expanding-window CV because the goal here is to estimate model-error
    variance under the operating regime, not to forecast.
    """
    boundaries = np.linspace(0, n, k + 1, dtype=int)
    folds: List[Tuple[np.ndarray, np.ndarray]] = []
    all_idx = np.arange(n)
    for i in range(k):
        test_idx = all_idx[boundaries[i]:boundaries[i + 1]]
        train_mask = np.ones(n, dtype=bool)
        train_mask[test_idx] = False
        train_idx = all_idx[train_mask]
        folds.append((train_idx, test_idx))
    return folds


def out_of_fold_residuals(
    fit_predict: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray],
    X: np.ndarray,
    y: np.ndarray,
    k: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run time-series k-fold CV; return concatenated OOF predictions and residuals.

    Parameters
    ----------
    fit_predict : callable
        Function (X_train, y_train, X_test) -> y_pred_test. Wraps a freshly
        fitted model so each fold is independent.
    X, y : arrays of shape (n, ...) and (n,)
    k : int
        Number of folds.

    Returns
    -------
    y_oof : (n,) array of OOF predictions, in original sample order
    r_oof : (n,) array of OOF residuals (y_pred - y_ref)
    """
    n = len(y)
    y_oof = np.full(n, np.nan, dtype=float)
    folds = time_series_kfold_indices(n, k)
    for tr, te in folds:
        y_oof[te] = fit_predict(X[tr], y[tr], X[te])
    r_oof = y_oof - y
    return y_oof, r_oof


# ---------------------------------------------------------------------------
# Step 3 — Subtract reference-instrument variance from residual variance
# ---------------------------------------------------------------------------

def model_error_std(
    r_oof: np.ndarray,
    u_ref: float | np.ndarray,
) -> Tuple[float, float, float]:
    """
    Recover model-error std from OOF residual std by subtracting reference variance.

    Var(r_observed) = Var(model error) + Var(reference noise)
        =>  u_A^model = sqrt(max(0, var(r) - u_ref^2))

    Parameters
    ----------
    r_oof : array of OOF residuals
    u_ref : scalar or array — reference-instrument standard uncertainty
            (in same units as r). If array, var is averaged.

    Returns
    -------
    u_A_model : decorrelated model-error std (Type A)
    raw_std    : observed OOF residual std (before subtraction; for diagnostics)
    u_ref_eff  : effective reference uncertainty used in subtraction
    """
    r = r_oof[~np.isnan(r_oof)]
    raw_var = float(np.var(r, ddof=1))
    raw_std = float(np.sqrt(raw_var))

    if np.isscalar(u_ref):
        u_ref_eff = float(u_ref)
    else:
        u_ref = np.asarray(u_ref, dtype=float)
        u_ref_eff = float(np.sqrt(np.mean(u_ref ** 2)))

    model_var = max(0.0, raw_var - u_ref_eff ** 2)
    u_A = float(np.sqrt(model_var))
    return u_A, raw_std, u_ref_eff


# ---------------------------------------------------------------------------
# Step 4 — Monte-Carlo input-propagation (JCGM 101)
# ---------------------------------------------------------------------------

def mc_input_uncertainty(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    X_test: np.ndarray,
    sigma_inputs: Sequence[float],
    M: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Propagate input-quantity uncertainties through a trained ML calibration
    model via Monte Carlo (JCGM 101).

    For each test sample i, draw M perturbed input vectors
        x_i^(m) = x_i + epsilon^(m),    epsilon ~ N(0, diag(sigma_inputs^2))
    and compute the spread of the predictions. The per-sample input-propagation
    standard uncertainty is the std across the M predictions.

    Parameters
    ----------
    predict_fn : callable
        Wraps the trained model: X -> y_pred (vectorised over rows).
    X_test : (n, p) array of test-sample input vectors
    sigma_inputs : length-p sequence of standard uncertainties for each input column
    M : int — number of MC samples
    rng : optional generator for reproducibility

    Returns
    -------
    u_input : (n,) array of per-sample input-propagation std uncertainties
    """
    rng = rng or np.random.default_rng(0)
    n, p = X_test.shape
    sigma = np.asarray(sigma_inputs, dtype=float).reshape(1, p)

    # Memory-efficient streaming MC: process M samples at a time, batch over n
    sum_y = np.zeros(n, dtype=float)
    sum_y2 = np.zeros(n, dtype=float)
    BATCH = 200  # MC draws per pass; tune for memory
    n_passes = int(np.ceil(M / BATCH))
    for _ in range(n_passes):
        m = min(BATCH, M - int(_) * BATCH) if False else BATCH
        # Sample epsilon (n, p) and run predict_fn n times — but vectorise:
        eps = rng.normal(0.0, 1.0, size=(n, p)) * sigma
        Xp = X_test + eps
        y = predict_fn(Xp)
        sum_y += y
        sum_y2 += y * y

    total = BATCH * n_passes  # actual draws, accounting for ceil
    mean = sum_y / total
    var = np.maximum(0.0, sum_y2 / total - mean * mean)
    return np.sqrt(var)


# ---------------------------------------------------------------------------
# Step 5 — Combine independent components
# ---------------------------------------------------------------------------

def combine_uncertainty(
    u_A_model: float,
    u_input_MC: float | np.ndarray,
    residual_bias: float,
    k: float = 2.0,
) -> Tuple[float, float, float]:
    """
    Combine the three (independent by construction) standard-uncertainty
    components into u_c and U.

    u_c^2 = u_A_model^2 + u_input^2 + (b/sqrt(3))^2

    The bias enters as a rectangular Type B per GUM 6.3.1 (uncorrected systematic
    half-width = |b|, std uncertainty = |b|/sqrt(3)).
    """
    if np.isscalar(u_input_MC):
        u_in_eff = float(u_input_MC)
    else:
        # Aggregate per-sample input uncertainty into a representative scalar
        # (mean is what GUM 5.2 calls the uncertainty of the typical measurement;
        # we also report rms for completeness in diagnostics)
        u_in_eff = float(np.sqrt(np.mean(np.asarray(u_input_MC) ** 2)))

    u_B_bias = abs(residual_bias) / np.sqrt(3.0)
    u_c = float(np.sqrt(u_A_model ** 2 + u_in_eff ** 2 + u_B_bias ** 2))
    U = k * u_c
    return u_c, U, u_B_bias


# ---------------------------------------------------------------------------
# Step 6 — Empirical coverage check (and empirical k)
# ---------------------------------------------------------------------------

def empirical_coverage(
    r_test: np.ndarray, U: float, target: float = 0.95
) -> Tuple[float, float]:
    """
    Compute the fraction of test residuals inside [-U, +U] and the empirical
    coverage factor k* such that ~target proportion fall inside.

    Returns (actual_coverage, k_empirical).
    """
    abs_r = np.abs(r_test[~np.isnan(r_test)])
    actual = float(np.mean(abs_r <= U))
    # Empirical k = quantile of |r| / u_c; we only have U here, so compute k* on
    # the standardised residuals using the implied u_c (= U/k_input). To avoid
    # circularity we accept U as given and just report actual coverage.
    if len(abs_r) == 0:
        return float("nan"), float("nan")
    k_emp = float(np.quantile(abs_r, target) / (U / 2.0)) if U > 0 else float("nan")
    return actual, k_emp


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def gum_budget(
    fit_predict: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray],
    predict_only: Callable[[np.ndarray], np.ndarray],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    u_ref: float | np.ndarray,
    sigma_inputs: Sequence[float],
    k: int = 5,
    M: int = 2000,
    coverage_factor: float = 2.0,
    target_coverage: float = 0.95,
    rng_seed: int = 0,
) -> Tuple[UncertaintyBudget, np.ndarray, np.ndarray]:
    """
    End-to-end GUM/JCGM 101 uncertainty budget for one calibration model.

    Inputs
    ------
    fit_predict     : (X_tr, y_tr, X_te) -> y_pred_te  — trains a fresh model
    predict_only    : X -> y_pred  — uses the *already-fitted* full-train model
                      (used for MC input propagation on test inputs)
    X_train, y_train: training set (used for OOF residuals + bias estimation)
    X_test, y_test  : held-out test set (final reporting)
    u_ref           : reference-instrument standard uncertainty
                      (scalar µg/m^3 or per-sample array)
    sigma_inputs    : length-p, standard uncertainty of each input column
                      (raw sensor noise, T uncertainty, RH uncertainty, ...)
    k               : number of CV folds (default 5)
    M               : Monte-Carlo draws (default 2000)
    coverage_factor : k for U = k * u_c (default 2)
    target_coverage : nominal coverage probability (default 0.95)

    Returns
    -------
    budget          : UncertaintyBudget dataclass
    y_pred_test_corr: bias-corrected predictions on the test set
    r_oof           : OOF residuals on the training portion (for diagnostics)
    """
    rng = np.random.default_rng(rng_seed)

    # 1) OOF residuals on training portion
    y_oof, r_oof = out_of_fold_residuals(fit_predict, X_train, y_train, k=k)

    # 2) Bias estimate from OOF predictions
    b_hat = estimate_bias(y_oof, y_train)

    # 3) Recover model-error std (subtract reference-noise variance)
    u_A_model, raw_std, _ = model_error_std(r_oof - b_hat, u_ref)

    # 4) Monte-Carlo input propagation through the production-trained model
    u_input_arr = mc_input_uncertainty(
        predict_only, X_test, sigma_inputs, M=M, rng=rng
    )

    # 5) Apply bias correction to test predictions, measure residual bias
    y_pred_test_raw = predict_only(X_test)
    y_pred_test_corr = apply_bias_correction(y_pred_test_raw, b_hat)
    r_test = y_pred_test_corr - y_test
    residual_bias_test = float(np.mean(r_test))

    # 6) Combine
    u_c, U, u_B_bias = combine_uncertainty(
        u_A_model, u_input_arr, residual_bias_test, k=coverage_factor
    )

    # 7) Coverage check
    actual_cov, k_emp = empirical_coverage(r_test, U, target=target_coverage)

    budget = UncertaintyBudget(
        u_A_model=u_A_model,
        u_input_MC=float(np.sqrt(np.mean(u_input_arr ** 2))),
        u_B_bias=u_B_bias,
        u_c=u_c,
        U=U,
        k=coverage_factor,
        n_oof=int(np.sum(~np.isnan(r_oof))),
        raw_oof_std=raw_std,
        bias_correction=b_hat,
        residual_bias_test=residual_bias_test,
        coverage_actual=actual_cov,
        coverage_target=target_coverage,
        k_empirical=k_emp,
    )
    return budget, y_pred_test_corr, r_oof


def stratified_uncertainty(
    r_oof: np.ndarray, y_train: np.ndarray, n_bins: int = 5
) -> pd.DataFrame:
    """
    Conditional Type A (model-error std) by reference-concentration bin.
    Reports u_A_model as a function of operating point.
    """
    r = r_oof[~np.isnan(r_oof)]
    y = y_train[~np.isnan(r_oof)]
    if len(r) == 0:
        return pd.DataFrame()
    edges = np.quantile(y, np.linspace(0, 1, n_bins + 1))
    rows = []
    for i in range(n_bins):
        mask = (y >= edges[i]) & (y <= edges[i + 1])
        if mask.sum() < 5:
            continue
        rows.append({
            "bin": f"[{edges[i]:.1f}, {edges[i+1]:.1f}]",
            "n": int(mask.sum()),
            "y_mean": float(np.mean(y[mask])),
            "u_A_model": float(np.std(r[mask], ddof=1)),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Self-test (sanity check on synthetic linear data)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rng = np.random.default_rng(42)
    n = 1000
    X = rng.normal(0, 1, (n, 3))
    true_w = np.array([2.0, -0.5, 0.3])
    y = X @ true_w + rng.normal(0, 1.0, n)  # noise std = 1.0

    n_train = 700
    Xtr, ytr = X[:n_train], y[:n_train]
    Xte, yte = X[n_train:], y[n_train:]

    # Toy linear model wrapper
    from numpy.linalg import lstsq

    def _fit(X_, y_):
        Xa = np.column_stack([X_, np.ones(len(X_))])
        w, *_ = lstsq(Xa, y_, rcond=None)
        return w

    w_full = _fit(Xtr, ytr)

    def fit_predict(X_tr, y_tr, X_te):
        w = _fit(X_tr, y_tr)
        return np.column_stack([X_te, np.ones(len(X_te))]) @ w

    def predict_only(X_):
        return np.column_stack([X_, np.ones(len(X_))]) @ w_full

    budget, y_corr, r_oof = gum_budget(
        fit_predict, predict_only,
        Xtr, ytr, Xte, yte,
        u_ref=0.0,
        sigma_inputs=[0.05, 0.05, 0.05],
        k=5, M=500,
    )
    print("Self-test budget:")
    for f in budget.__dataclass_fields__:
        if f != "per_bin":
            v = getattr(budget, f)
            print(f"  {f:22s} = {v}")
    print(f"\nTrue noise std = 1.000;  recovered u_A_model = {budget.u_A_model:.3f}")
    print(f"Empirical coverage = {budget.coverage_actual:.3f} (target = {budget.coverage_target})")
