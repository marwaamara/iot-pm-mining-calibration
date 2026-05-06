# Reviewer-verification map

This document is provided specifically to make the reviewers' job easy.
Every comment in the original review (Reviewer 1: 7 items; Reviewer 2:
26 items) is mapped to the **exact** code file, function, and line(s)
where the response is implemented, and to the script that, when run,
produces the numerical evidence.

Use this document as a checklist while reading the response letter — every
claim made in the response is independently verifiable here.

---

## Reviewer 1 — metrology critiques

### R1.1 — "Equation (9) Type A from test residuals violates GUM 4.2.1"

* **Code answer:** [`code/uncertainty.py`](../code/uncertainty.py) functions
  `out_of_fold_residuals` and `model_error_std`.
* **Run to verify:** `python code/uncertainty.py` — built-in self-test
  recovers the true noise standard deviation of a synthetic case to
  within 3 % using the OOF method.
* **Manuscript section:** §4.3.2.

### R1.2 — "Reference uncertainty is associated with the input quantity"

* **Code answer:** `model_error_std` performs the variance subtraction
  `u_A^model² = max(0, Var(r_OOF) − u_ref²)` (the reference uncertainty
  enters as an *input* to the residual computation, not as an additive
  output term).
* **Run to verify:** Edit `u_ref` in `gum_budget` and rerun —
  `u_A^model` shrinks accordingly. The relationship is exact and
  observable.
* **Manuscript section:** §4.3.2, equation (8).

### R1.3 — "Type A and Type B are correlated"

* **Code answer:** After Step 2 above, the Type A model-error component
  and the reference Type B are decorrelated by construction. The
  Monte-Carlo input-propagation component (`mc_input_uncertainty`) is
  *independent* of the model-fit residuals because it conditions on a
  fixed trained model. The combined-uncertainty assembly in
  `combine_uncertainty` therefore correctly sums three independent
  components.
* **Manuscript section:** §4.3.4, equation (11).

### R1.4 — "The bias is not used to correct"

* **Code answer:** `estimate_bias` is called on the validation portion
  (`gum_budget` line ~261), and `apply_bias_correction` is applied to
  *all* predictions before they are used downstream. The residual bias
  on the test set is then computed and entered into the budget as
  `u_B^bias` (rectangular Type B per GUM 6.3.1).
* **Run to verify:** the `bias_correction` field of the returned
  `UncertaintyBudget` reports `b̂`; the `residual_bias_test` field
  reports the small remaining bias on the held-out test set after
  correction.
* **Manuscript section:** §4.3.1, equation (7).

### R1.5 — "Training data must represent application statistics"

* **Code answer:** the methodology is also evaluated on the
  Kelly et al. 2023 Salt Lake Valley dataset
  ([`code/load_salt_lake_valley.py`](../code/load_salt_lake_valley.py)),
  which provides real co-located PMS5003 + FEM measurements in an arid
  dust-event environment closely analogous to KSA mining conditions.
* **Run to verify:** `python code/run_revision.py` — produces
  `results/tables/calibration_results_slv.csv` showing ANN achieves
  `R² = 0.766`, `U = 32.76` µg/m³, coverage 97.1 %.
* **Manuscript section:** §5.6.

### R1.6 — "Couldn't the inverse be calculated analytically?"

* **Manuscript answer:** §6.3 — each individual cross-sensitivity admits
  a closed-form inverse, but the four mechanisms act jointly through
  coupled non-linear interactions, so there is no general analytical
  solution. ML solves the joint inversion + parameter estimation in one
  step.
* **Code reference:** `code/data_generator.py:simulate_sensor_response`
  (in the manuscript's `data_generator.py` reference) shows the
  multiplicative coupling.

### R1.7 — synthetic-data limitation (preamble)

* **Code answers (three lines of evidence):**
  1. **Real-data validation** on Kelly et al. 2023 — see R1.5.
  2. **Sensitivity analysis** on the assumed PMS5003 error model:
     [`code/sensitivity_analysis.py`](../code/sensitivity_analysis.py)
     perturbs each parameter by ±20 % and reports `|ΔRMSE| ≤ 2.34` µg/m³,
     `|ΔR²| ≤ 0.030`.
  3. **Strengthened limitation paragraph** in §6.4 of the manuscript.
* **Run to verify:** `python code/sensitivity_analysis.py` (~2 min)
  produces `results/tables/sensitivity_analysis.csv`.

---

## Reviewer 2 — specific comments

### R2.1 — Random vs. temporal split

* **Code answer:**
  [`code/run_revision.py`](../code/run_revision.py) `run_dataset(...)`
  takes a `split_kind` argument (`"random"` or `"temporal"`) and runs
  both for the SLV dataset.
* **Run to verify:** the SLV table includes both splits side-by-side.
* **Manuscript section:** §5.6, Table 5.

### R2.2 — Overfitting diagnostics

* **Code answer:**
  [`code/overfit_diagnostics.py`](../code/overfit_diagnostics.py)
  produces (i) train/test gap, (ii) learning curves, (iii) 5-fold
  nested time-series CV.
* **Run to verify:** `python code/overfit_diagnostics.py` writes
  `learning_curves_*.csv`, `train_test_gap_*.csv`, `nested_cv_*.csv`.
* **Manuscript section:** §5.8.

### R2.3 — Post-calibration reliability

* The Salt Lake Valley validation (§5.6) is post-calibration reliability
  on out-of-distribution real data; empirical coverage 97.1 % (vs nominal
  95 %).

### R2.4 — Co-location site description

* **Code:**
  [`code/architecture_figure.py`](../code/architecture_figure.py),
  [`code/plotting.py`](../code/plotting.py) `fig_colocation_schematic`.
* **Manuscript:** new Figure 5.

### R2.5 — Negative bias of S1

* MBE in the new Table 3 is close to zero for all calibrated models
  thanks to the bias-correction step. Remaining sign reflects stochastic
  initialisation.

### R2.6 — Section 5.1 phrasing

* Manuscript: rewritten first paragraph of Section 5.

### R2.7 / R2.17 — Adjusted R² and partial correlations

* **Code:** [`code/mlr_diagnostics.py`](../code/mlr_diagnostics.py)
  `adjusted_r2`, `partial_corr`, `vif`.
* **Run to verify:** `python code/mlr_diagnostics.py` writes
  `mlr_partial_corr_*.csv` and `mlr_summary_*.csv`.
* **Manuscript section:** §5.10.

### R2.8 — Keyword abbreviations

* Manuscript front matter: "GUM" expanded, "IoT" expanded.

### R2.9 — Highlights numerics

* `response/highlights.tex` (in the submission package): R² and RMSE on
  separate lines.

### R2.10 — Citation numbering

* Manuscript reference list rebuilt with `elsarticle-num`; first citation
  in Introduction is now [1].

### R2.11 — Photodiode-temperature citation

* Sayahi 2019 + Pietrenko-Dabrowska 2024 added to that sentence.

### R2.12 — Recent mining LCS literature

* 5 new bibitems (Penchala 2025 ×3, Pradhan 2025 ×2). New columns in
  Table 1 (literature comparison).

### R2.13 / R2.24 / R2.25 — Padded axes / matched scales

* **Code:** [`code/plotting.py`](../code/plotting.py) helper functions
  `_pad_lim` and `_matched_lim` enforce padded, matched axis limits on
  every figure.

### R2.14 / R2.15 — Faceted Fig. 3

* **Code:** `plotting.py:fig3_faceted_per_sensor` produces one panel per
  sensor with matched x/y limits and a separate 1:1 line per panel.
* **Manuscript:** Fig. 3.

### R2.16 — Fig. 2(d) PM₂.₅ vs PM₁₀ density

* Caption rewritten to explain that KDEs are area-normalised so curves
  can cross freely.

### R2.18 — Negative R² in concentration bins

* **Code:** [`code/bin_analysis.py`](../code/bin_analysis.py) reports
  per-bin RMSE, NRMSE, and bootstrap 95 % CI for R². Demonstrates that
  the negative R² is a small reference-variance artefact, not
  overfitting.
* **Run to verify:** `python code/bin_analysis.py`.
* **Manuscript section:** §5.5, Table 4.

### R2.19 — Comparison table missing studies

* Three new column entries in Table 1 for the Patra-group studies +
  four new criterion rows.

### R2.20 — Grammar correction "based no" → "based on"

* Done; full grammar pass performed.

### R2.21 — Hyperparameter justification

* **Code:** [`code/hyperparam_curves.py`](../code/hyperparam_curves.py)
  sweeps `n_estimators` and `max_depth` for both RF and GBR.
* **Run to verify:** `python code/hyperparam_curves.py` produces
  `hyperparam_curves_*.csv` showing the plateau.
* **Manuscript section:** §5.9.

### R2.22 — Section 5.5 missing number

* Fixed: all `\ref{}` pointers now resolve at compile time.

### R2.23 — "Cross-sensitivity structure" terminology

* Replaced with "multivariate cross-sensitivity dependence" on first
  introduction in §6.2.

### R2.26 — Co-location experiment figure in main text

* New Fig. 5 (`fig_colocation_schematic`) added to main text.

---

## Quickest path to verifying everything

```bash
# (after pip install -r requirements.txt)
python code/uncertainty.py            # 5 s — sanity self-test
python code/run_revision.py           # 5–8 min — Tables 3 & 5
python code/sensitivity_analysis.py   # 2 min — R1 main rebuttal
python code/overfit_diagnostics.py    # 3 min — R2 item 2
python code/mlr_diagnostics.py        # 5 s — R2 items 7, 17
python code/bin_analysis.py           # 5 s — R2 item 18
python code/hyperparam_curves.py      # 2 min — R2 item 21
python code/plotting.py               # 30 s — Figs 3, 5, slv, decomp, sens
python code/diagnostic_figs.py        # 5 s — Figs gap, learning, hparam, bin
```

**Total: ~13 minutes** for a complete reproduction of every numerical
claim and every figure in the manuscript.
