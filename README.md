# AI-enhanced calibration of IoT particulate matter sensors in open-pit mining

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![Data: CC0 / CC BY](https://img.shields.io/badge/Data-CC0%20%7C%20CC%20BY-orange.svg)](data/)

Reproducibility package for the manuscript:

> **Amara, M.** (2026). *AI-enhanced calibration of IoT particulate matter
> sensors in open-pit mining: a metrological approach to environmental
> cross-sensitivity compensation.* **Measurement** (Elsevier, IMEKO),
> manuscript MEAS-D-26-03768 (under review, major revision).

This repository contains every script, dataset reference and JCGM-101
uncertainty pipeline used to produce the results in the manuscript.
A reviewer with Python 3.10+ should be able to clone this repository
and reproduce **every numerical claim and every figure** in the paper
in under fifteen minutes.

---

## Why this repository exists

Reviewer 1 of the original submission raised four equation-level critiques
of the uncertainty framework (GUM 4.2.1 independence; reference uncertainty
as input vs output; correlation between Type A and Type B; bias correction)
and one applicability concern (synthetic sensor data limits real-world
applicability of the uncertainty evaluation). This repository is the
*executable* answer to those concerns:

* The **`code/uncertainty.py`** module implements the full
  JCGM-101-compliant pipeline (out-of-fold residuals, reference-variance
  subtraction, Monte-Carlo input propagation, bias correction) and includes
  a self-test against a synthetic linear case.
* The **`code/sensitivity_analysis.py`** script perturbs every parameter of
  the assumed PMS5003 error model by ±20 % and shows that the calibration
  RMSE changes by at most 2.4 µg/m³.
* The **Salt Lake Valley case study** (`code/load_salt_lake_valley.py`,
  `data/salt_lake_valley/`) validates the methodology on real co-located
  Plantower PMS5003 + FEM PM₁₀ measurements (Kelly et al., AMT 16,
  2455 (2023); CC BY 3.0).

Together they make the central methodological contribution of the paper
verifiable by anyone with a laptop and an hour of free time.

---

## Quick start (3 commands)

```bash
git clone https://github.com/<your-username>/iot-pm-mining-calibration.git
cd iot-pm-mining-calibration
pip install -r requirements.txt

# 1. Clean the Salt Lake Valley raw data (cached CSV is also provided)
python code/load_salt_lake_valley.py

# 2. Run the full pipeline on both datasets — produces all paper tables
python code/run_revision.py
```

Expected runtime: ~5 minutes (KAPSARC) + ~3 minutes (Salt Lake Valley) on
a recent laptop CPU. The full pipeline produces every CSV referenced in
Tables 3, 5 and 7 of the manuscript.

---

## Repository layout

```
.
├── README.md                         <- this file
├── LICENSE                           <- MIT (code) — see data/ for data licences
├── CITATION.cff                      <- machine-readable citation for GitHub & Zenodo
├── requirements.txt                  <- pinned Python dependencies
├── docs/
│   ├── METHODOLOGY.md                <- high-level description of the GUM pipeline
│   ├── REPRODUCING.md                <- step-by-step reproducibility recipe
│   └── REVIEWER_VERIFICATION.md      <- R1/R2 comments → exact code lines
├── code/                             <- production Python modules
│   ├── config.py                     <- all paths, seeds, model hyperparameters
│   ├── data_generator.py             <- KAPSARC loader + PMS5003 simulator
│   ├── load_salt_lake_valley.py      <- real-data loader (Kelly et al. 2023)
│   ├── models.py                     <- 5 calibrators: Affine | MLR | RF | GBR | ANN
│   ├── uncertainty.py                <- JCGM-101 pipeline (the metrology core)
│   ├── run_revision.py               <- main entry point (reproduces Tables 3 & 5)
│   ├── sensitivity_analysis.py       <- ±20 % perturbations (R1 main rebuttal)
│   ├── overfit_diagnostics.py        <- learning curves + nested CV (R2 item 2)
│   ├── mlr_diagnostics.py            <- adjusted R², partial corr, VIF (R2 item 7)
│   ├── bin_analysis.py               <- per-concentration NRMSE (R2 item 18)
│   ├── hyperparam_curves.py          <- B and max_depth sweeps (R2 item 21)
│   ├── plotting.py                   <- publication figure generator
│   ├── architecture_figure.py        <- two-tier system architecture diagram
│   └── diagnostic_figs.py            <- learning/gap/hparam/bin diagnostic figs
├── data/
│   ├── kapsarc/
│   │   ├── README.md                 <- source (KAPSARC CC0) and cleaning notes
│   │   ├── riyadh_air_quality_2021_2023.csv   <- raw KAPSARC reference data
│   │   └── mining_pm_sensor_data.csv          <- cached output of data_generator.py
│   └── salt_lake_valley/
│       ├── README.md                 <- citation: Kelly et al. AMT 2023 (CC BY)
│       ├── Data_Set_for_the_AMT.xlsx          <- raw dataset from Hive
│       ├── Kelly_Readme20221019.txt           <- original dataset readme
│       └── salt_lake_valley_clean.csv         <- cached output of load_salt_lake_valley.py
└── results/
    ├── tables/                       <- all CSVs produced by run_revision.py
    └── figures/                      <- 11 key figures used in the manuscript
```

---

## Headline results (verifiable by running `python code/run_revision.py`)

### KAPSARC (semi-synthetic, primary case study, PM₂.₅, n = 23,742)

| Model | RMSE (µg/m³) | R² | U at k = 2 (µg/m³) | Empirical coverage |
|---|---|---|---|---|
| Uncalibrated | 24.97 | 0.646 | 49.95 | 95.1 % |
| Affine | 24.85 | 0.650 | 47.76 | 92.8 % |
| MLR + covariates | 16.85 | 0.839 | 33.12 | 95.2 % |
| Random Forest | 10.79 | 0.934 | 21.36 | 95.6 % |
| Gradient Boosting | 9.99 | 0.943 | 21.05 | 96.6 % |
| **ANN** | **9.23** | **0.952** | **20.07** | **97.4 %** |

### Salt Lake Valley (real co-located PMS5003 + FEM, PM₁₀, n = 694)

| Model | RMSE (µg/m³) | R² | U at k = 2 (µg/m³) | Empirical coverage |
|---|---|---|---|---|
| Uncalibrated | 29.47 | -0.30 | 45.94 | 92.0 % |
| Affine | 19.48 | 0.43 | 47.65 | 94.9 % |
| MLR + covariates | 16.98 | 0.57 | 40.75 | 97.8 % |
| Random Forest | 17.00 | 0.57 | 30.35 | 92.8 % |
| Gradient Boosting | 15.10 | 0.66 | 29.45 | 94.9 % |
| **ANN** (avg of 3 seeds) | **12.48** | **0.766** | **32.76** | **97.1 %** |

### Sensitivity to PMS5003 error-model parameters

| Perturbation | Worst case |
|---|---|
| `\|ΔRMSE\|` over ±20 % of any parameter | **≤ 2.34 µg/m³** |
| `\|ΔR²\|` over ±20 % of any parameter | **≤ 0.030** |
| Range of R² across all 14 perturbations | [0.913, 0.960] |

---

## How to reproduce a specific paper claim

| Manuscript claim | Script to run | Output |
|---|---|---|
| Table 3 (KAPSARC results) | `python code/run_revision.py` | `results/tables/calibration_results_kapsarc.csv` |
| Table 5 (Salt Lake Valley results) | `python code/run_revision.py` | `results/tables/calibration_results_slv.csv` |
| Section 5.7 sensitivity | `python code/sensitivity_analysis.py` | `results/tables/sensitivity_analysis.csv` |
| Section 5.8 overfit diagnostics | `python code/overfit_diagnostics.py` | `results/figures/learning_curves_*.csv` etc. |
| Section 5.9 hyperparameter curves | `python code/hyperparam_curves.py` | `results/figures/hyperparam_curves_*.csv` |
| Section 5.10 MLR partial correlations | `python code/mlr_diagnostics.py` | `results/tables/mlr_partial_corr_*.csv` |
| R2 item 18 negative-R² investigation | `python code/bin_analysis.py` | `results/tables/concentration_bin_analysis.csv` |
| Figure 4 (architecture) | `python code/architecture_figure.py` | `results/figures/fig_architecture.png` |

---

## Citation

If you use this code or any of its derived results, please cite both
the manuscript and the code:

```bibtex
@article{Amara2026Measurement,
  author  = {Amara, Marwa},
  title   = {AI-enhanced calibration of IoT particulate matter sensors
             in open-pit mining: a metrological approach to environmental
             cross-sensitivity compensation},
  journal = {Measurement},
  year    = {2026},
  note    = {Manuscript MEAS-D-26-03768, under review.}
}

@software{Amara2026Code,
  author  = {Amara, Marwa},
  title   = {Reproducibility code for AI-enhanced calibration of IoT
             particulate matter sensors in open-pit mining},
  year    = {2026},
  url     = {https://github.com/<your-username>/iot-pm-mining-calibration},
  doi     = {10.5281/zenodo.XXXXXXX}
}
```

The Zenodo DOI will be assigned automatically once the first release is
published (see `docs/REPRODUCING.md` for the workflow).

---

## Licences

* **Code** (`code/`): MIT — see [`LICENSE`](LICENSE).
* **KAPSARC reference data** (`data/kapsarc/`): CC0 (public domain). Source:
  King Abdullah Petroleum Studies and Research Center, Riyadh Air Quality
  Dataset 2022–2024, <https://datasource.kapsarc.org>.
* **Salt Lake Valley dataset** (`data/salt_lake_valley/`): CC BY 3.0.
  Source: Kelly K. and Kaur K. (2022), *The Hive*, University of Utah,
  <https://doi.org/10.7278/S50d-xbns-3ge3>. If you use this dataset
  please cite Kelly et al. 2023, AMT 16, 2455 in addition to this code.

---

## Funding and acknowledgments

This work was supported by the Deanship of Scientific Research at
Northern Border University, Arar, Kingdom of Saudi Arabia, through
project number **NBU-FFR-2026-2729-04**.

---

## Contact

Dr Marwa Amara · Faculty of Computing and Information Technology ·
Northern Border University · Arar 91431, Kingdom of Saudi Arabia ·
[Marwa.amara@nbu.edu.sa](mailto:Marwa.amara@nbu.edu.sa)
