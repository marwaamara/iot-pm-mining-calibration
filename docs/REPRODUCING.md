# Reproducing the manuscript results

This document is a step-by-step recipe for reproducing every numerical
claim and every figure in the manuscript. Total time on a recent laptop
(no GPU required): **~15 minutes**.

---

## 0. Prerequisites

* **Python 3.10 or newer.** (Tested on 3.10, 3.11, 3.12, 3.13.)
* About **2 GB of RAM** for the ANN and Monte-Carlo passes.
* No GPU required.

Optional but recommended:
* A clean virtual environment (`python -m venv .venv && .venv\Scripts\activate`
  on Windows, or `source .venv/bin/activate` on Linux/macOS).

---

## 1. Clone and install

```bash
git clone https://github.com/marwaamara/iot-pm-mining-calibration.git
cd iot-pm-mining-calibration
pip install -r requirements.txt
```

Expected install time: 1–3 minutes.

If the TensorFlow install is slow on your machine, you can skip the ANN
runs by editing `code/run_revision.py` and removing `"ANN"` from the
`MODELS` list. The other four calibrators (Affine, MLR, RF, GBR) do not
require TensorFlow.

---

## 2. Sanity-check the metrology pipeline

```bash
python code/uncertainty.py
```

Expected output (last few lines):

```
True noise std = 1.000;  recovered u_A_model = 0.977
Empirical coverage = 0.957 (target = 0.95)
```

If you see numbers outside this range, please open an issue before
proceeding.

---

## 3. Generate / refresh the cleaned datasets

The cleaned CSVs are already cached in `data/`, but you can regenerate
them deterministically from the raw sources.

```bash
# Re-generate the semi-synthetic KAPSARC sensor signals
python code/data_generator.py

# Re-clean the Salt Lake Valley raw xlsx
python code/load_salt_lake_valley.py
```

Both scripts are deterministic given `RANDOM_SEED = 42` in `code/config.py`.

---

## 4. Reproduce Tables 3 and 5 (the headline results)

```bash
python code/run_revision.py
```

Expected runtime: 5–8 minutes. The script prints progress for each
(dataset × model) pair and writes the following CSVs to `results/tables/`:

* `calibration_results_kapsarc.csv` — Table 3 of the manuscript
* `calibration_results_slv.csv` — Table 5 (random + temporal splits)
* `calibration_results_slv_random.csv` — Table 5 random subset alone
* `calibration_results_slv_temporal.csv` — Table 5 temporal subset alone
* `uncertainty_budget_full.csv` — full long-format budget for both datasets
* `uncertainty_budget_full.tex` — LaTeX-ready version of the same

Headline numbers you should see (KAPSARC ANN row):

```
RMSE = 9.23, R^2 = 0.952, U = 20.07, coverage = 97.4 %
```

and (Salt Lake Valley random-split ANN row):

```
RMSE = 12.48, R^2 = 0.766, U = 32.76, coverage = 97.1 %
```

---

## 5. Reproduce the auxiliary diagnostics

Each of these is a standalone script. Run them in any order.

```bash
# Section 5.7 — sensitivity analysis (R1's main rebuttal)
python code/sensitivity_analysis.py

# Section 5.8 — overfitting diagnostics (R2 item 2)
python code/overfit_diagnostics.py

# Section 5.9 — hyperparameter validation curves (R2 item 21)
python code/hyperparam_curves.py

# Section 5.10 — adjusted R^2 + partial correlations (R2 items 7, 17)
python code/mlr_diagnostics.py

# R2 item 18 — concentration-bin analysis with bootstrap CIs
python code/bin_analysis.py
```

Outputs land in `results/tables/` (CSVs) and `results/figures/` (PNGs
once you also run the next step).

---

## 6. Reproduce all figures

```bash
# Manuscript figures (faceted Fig 3, decomposition, schematic, sensitivity)
python code/plotting.py

# Diagnostic figures (learning curves, train/test gap, hparam, bin analysis)
python code/diagnostic_figs.py

# Two-tier system architecture (replaces the original TikZ diagram)
python code/architecture_figure.py
```

After this, `results/figures/` should contain about 15 PNG files. The
key ones referenced in the manuscript are listed below.

| Manuscript figure | File |
|---|---|
| Fig. 3 | `fig3_faceted_per_sensor.png` |
| Fig. 4 (architecture) | `fig_architecture.png` |
| Fig. 5 (co-location schematic) | `fig_colocation_schematic.png` |
| Salt Lake Valley faceted | `fig_slv_faceted_raw.png` |
| Uncertainty decomposition (KAPSARC) | `fig_uncertainty_decomp_kapsarc.png` |
| Uncertainty decomposition (SLV) | `fig_uncertainty_decomp_saltlakevalley.png` |
| Sensitivity analysis | `fig_sensitivity_analysis.png` |
| Train/test gap (KAPSARC) | `fig_train_test_gap_kapsarc.png` |
| Learning curves (KAPSARC) | `fig_learning_kapsarc.png` |
| Hyperparameter sweeps | `fig_hparam_kapsarc.png` |
| Concentration-bin analysis | `fig_bin_analysis.png` |

---

## 7. Verify your reproduction matches the published numbers

Run:

```bash
diff -u <(cut -d, -f1-5 results/tables/calibration_results_kapsarc.csv) \
        <(cut -d, -f1-5 results_published/calibration_results_kapsarc.csv)
```

(if you have a `results_published/` snapshot from the supplementary
material). Any difference of more than ±0.01 in RMSE / R² indicates a
non-determinism (most likely a TensorFlow random-seed issue with the
ANN). Open an issue if you see this.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'tensorflow'` | TensorFlow install failed (common on Apple Silicon) | `pip install tensorflow-macos tensorflow-metal` (Mac) or skip ANN as in §1 |
| `KeyError: 'Wind speed (Knots)'` when loading SLV | Excel file moved or renamed | Re-download from <https://doi.org/10.7278/S50d-xbns-3ge3> and place at `data/salt_lake_valley/Data_Set_for_the_AMT.xlsx` |
| `MemoryError` during `run_revision.py` | <2 GB RAM available | Reduce `M = 1500` to `M = 500` in `code/run_revision.py` (Monte-Carlo draws); slight loss of input-uncertainty precision |
| Plots appear empty / blank | Matplotlib backend issue on a headless machine | `MPLBACKEND=Agg python code/plotting.py` |
| Numbers differ from the manuscript by ~5–10 % | Different random seed in TensorFlow | Confirm `RANDOM_SEED = 42` in `code/config.py`; see §7 above |

---

## Optional: getting a Zenodo DOI for your own fork

If you fork this repository and want a citable DOI for your own work,
follow the workflow in [`UPLOAD_GUIDE.md`](../UPLOAD_GUIDE.md) (steps 4
onwards). It takes ~5 minutes via the Zenodo–GitHub web integration.
