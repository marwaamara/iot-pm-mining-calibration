# Methodology — JCGM-101-compliant uncertainty pipeline

This document gives a high-level walkthrough of the metrology pipeline
implemented in [`code/uncertainty.py`](../code/uncertainty.py). It is
intended for a reader who wants to *understand* what the code is doing
without first reading the manuscript.

For the full mathematical treatment, see Section 4.3 of the manuscript.

---

## The measurement function

The calibrated estimate of the measurand for a single test sample i is

```
x̂_i = f_θ(s_raw_i, T_i, RH_i, v_i, d_i, h_i) − b̂
```

where:

* `f_θ` is the trained ML calibration model (Affine, MLR, RF, GBR or ANN)
  with parameters θ;
* the inputs are the raw sensor reading, temperature, relative humidity,
  wind speed, deployment day, and hour of day;
* `b̂` is a bias-correction offset estimated from validation folds.

Each input quantity carries a known standard uncertainty
(see [Step 3](#step-3--input-quantity-uncertainty-by-jcgm-101-monte-carlo) below).

---

## Step 1 — Bias correction

`b̂` = mean OOF residual from the validation folds. We *apply* this as an
offset correction to all predictions, so the residuals on the held-out
test set are zero-mean by construction. Any residual mean bias on the
test set after correction enters the budget as a rectangular Type B
contribution per GUM 6.3.1.

Code: [`uncertainty.py:estimate_bias`](../code/uncertainty.py),
[`uncertainty.py:apply_bias_correction`](../code/uncertainty.py).

> **What this answers:** Reviewer 1's critique that the bias was reported
> but not used to correct the model.

---

## Step 2 — Type A from out-of-fold residuals

The Type A standard uncertainty is computed from out-of-fold (OOF)
residuals of a five-fold time-series partition of the *training* set.
Each OOF residual is a prediction on a sample that was *unseen by the
model that produced it*. The OOF residual sequence therefore constitutes
independent samples of the calibration error under the operating regime,
satisfying GUM 4.2 in the validation-uncertainty sense (Pernot &
Cailliez, J. Chemom. 2017; ISO 6143).

Because the residual is computed against a noisy reference, its observed
variance over-estimates the model-error variance by the variance of the
reference noise:

```
Var(r_observed) = Var(e_model) + u²_ref
```

We recover the true model-error standard uncertainty by subtraction:

```
u_A^model = √( max(0, Var(r_OOF) − u²_ref) )
```

Code: [`uncertainty.py:out_of_fold_residuals`](../code/uncertainty.py),
[`uncertainty.py:model_error_std`](../code/uncertainty.py).

> **What this answers:** Reviewer 1's critiques that test-set residuals
> are not "n independent observations of the same quantity" (GUM 4.2.1)
> and that the reference uncertainty is on the *input*, not the output.

---

## Step 3 — Input-quantity uncertainty by JCGM 101 Monte-Carlo

Each input to the trained calibration model carries a measurement
uncertainty:

| Input | Standard uncertainty | Source |
|---|---|---|
| Raw sensor PM | 5 µg/m³ | Plantower PMS5003 datasheet noise floor |
| Temperature | 0.5 °C | Bosch BME280 datasheet |
| Relative humidity | 2 % | Bosch BME280 datasheet |
| Wind speed | 0.5 m/s | Cup anemometer typical |
| Deployment day, hour of day | 0 | not measurement quantities |

For each test sample we draw M = 1500 perturbed input vectors

```
x_i^(m) = x_i + ε^(m),    ε ~ N(0, diag(σ²))
```

and compute

```
u²_input(x̂_i) = Var_m( f_θ(x_i + ε^(m)) )
```

The aggregate input-propagation uncertainty is the root-mean-square of
the per-sample values across the test set.

Code: [`uncertainty.py:mc_input_uncertainty`](../code/uncertainty.py).

> **What this answers:** the JCGM-101 supplement to the GUM (the
> Monte-Carlo method) is the explicit machinery for propagating input
> distributions through a non-linear measurement function.

---

## Step 4 — Combined and expanded uncertainty

The three components

* `u_A^model` — model-fit Type A from OOF residuals (Step 2)
* `u_input^MC` — input-quantity Type A from Monte-Carlo propagation (Step 3)
* `u_B^bias` — uncorrected residual bias as Type B rectangular,
  `|b_residual| / √3` (Step 1)

are independent by construction (the OOF residual variance is a property
of the model fit; the MC propagation conditions on a fixed model; the
rectangular bias term acts on the corrected output). They therefore
combine as

```
u_c² = (u_A^model)² + (u_input^MC)² + (u_B^bias)²
```

The expanded uncertainty at coverage factor k = 2 is `U = k · u_c`.

Empirical coverage — the fraction of held-out test predictions inside
[x̂ − U, x̂ + U] — is reported alongside U to verify the coverage
assumption when the OOF residual distribution is non-Gaussian.

Code: [`uncertainty.py:combine_uncertainty`](../code/uncertainty.py),
[`uncertainty.py:empirical_coverage`](../code/uncertainty.py).

> **What this answers:** Reviewer 1's critique that the original
> Type A and Type B were correlated (residuals computed against the
> same reference). Here they are decorrelated *by construction*: the
> reference variance has been subtracted from u_A^model in Step 2,
> u_input^MC conditions on a fixed model, and u_B^bias acts on the
> bias-corrected output.

---

## Sanity check (built into the module)

`uncertainty.py` runs a self-test when invoked directly:

```bash
python code/uncertainty.py
```

It generates a synthetic linear regression with known noise std = 1.0,
runs the full pipeline, and reports the recovered values. Expected output:

```
True noise std = 1.000;  recovered u_A^model ≈ 0.97
Empirical coverage ≈ 0.95 (target = 0.95)
```

If your reproduction produces values outside (0.95, 1.05) for the
recovered std, or outside (0.93, 0.97) for the empirical coverage,
something is wrong with your installation — please open an issue.

---

## Where the manuscript equations live in the code

| Manuscript equation | Code location |
|---|---|
| Eq. (5) — measurement function with bias | `uncertainty.py:gum_budget` lines for `predict_only` + `apply_bias_correction` |
| Eq. (7) — bias estimate | `estimate_bias` |
| Eq. (8) — variance decomposition | `model_error_std` |
| Eq. (9) — recovered model-error std | `model_error_std` (return value) |
| Eq. (10) — Monte-Carlo propagation | `mc_input_uncertainty` |
| Eq. (11) — combined uncertainty | `combine_uncertainty` |
| Eq. (12) — expanded uncertainty | `combine_uncertainty` (return value `U`) |

If you are reviewing the manuscript, opening `uncertainty.py` side by
side with Section 4.3 of the paper is the fastest way to verify that the
code does what the paper says.
