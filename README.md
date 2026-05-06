# IoT PM mining calibration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![Data: CC0 / CC BY](https://img.shields.io/badge/Data-CC0%20%7C%20CC%20BY-orange.svg)](data/)

Open-source Python pipeline for the calibration of low-cost IoT
particulate-matter (PM) sensors against a reference instrument, with a
JCGM-101-compliant uncertainty budget.

The full description of the methodology and the corresponding
peer-reviewed publication will be linked here once the article is
published. Until then, this repository is provided as a reproducibility
artefact only; please contact the author for citation guidance if you
plan to use the code in your own work.

---

## Quick start

```bash
git clone https://github.com/marwaamara/iot-pm-mining-calibration.git
cd iot-pm-mining-calibration
pip install -r requirements.txt

# Sanity-check the metrology pipeline (5 seconds)
python code/uncertainty.py

# Re-clean the Salt Lake Valley raw data (cached CSV is also provided)
python code/load_salt_lake_valley.py

# Run the full calibration pipeline on both case studies
python code/run_revision.py
```

Expected runtime: about 5 minutes (KAPSARC) plus 3 minutes (Salt Lake
Valley) on a recent laptop CPU. No GPU required.

---

## Repository layout

```
.
├── README.md
├── LICENSE                 MIT (code) — see data/ folders for data licences
├── CITATION.cff            machine-readable citation
├── requirements.txt        pinned Python dependencies
├── code/                   production Python modules
│   ├── config.py           paths, seeds, hyperparameters
│   ├── data_generator.py   KAPSARC loader + PMS5003 simulator
│   ├── load_salt_lake_valley.py    real-data loader
│   ├── models.py           5 calibrators (Affine, MLR, RF, GBR, ANN)
│   ├── uncertainty.py      JCGM-101 uncertainty pipeline
│   ├── run_revision.py     main entry point
│   ├── sensitivity_analysis.py
│   ├── overfit_diagnostics.py
│   ├── mlr_diagnostics.py
│   ├── bin_analysis.py
│   ├── hyperparam_curves.py
│   ├── plotting.py
│   ├── architecture_figure.py
│   └── diagnostic_figs.py
├── data/
│   ├── kapsarc/                     reference dataset (CC0)
│   └── salt_lake_valley/            real PMS5003 + FEM dataset (CC BY 3.0)
└── results/
    ├── tables/             CSV outputs
    └── figures/            PNG outputs
```

---

## Licences

* **Code** (`code/`): MIT — see [`LICENSE`](LICENSE).
* **KAPSARC reference data** (`data/kapsarc/`): CC0. Source: KAPSARC,
  Riyadh Air Quality Dataset, <https://datasource.kapsarc.org>.
* **Salt Lake Valley dataset** (`data/salt_lake_valley/`): CC BY 3.0.
  Source: <https://doi.org/10.7278/S50d-xbns-3ge3>. If you use this
  dataset, please cite the original authors as documented in
  `data/salt_lake_valley/`.

---

## Contact

Dr Marwa Amara — Department of Computer Sciences, College of Sciences,
Northern Border University, Arar 91431, Kingdom of Saudi Arabia —
[Marwa.amara@nbu.edu.sa](mailto:Marwa.amara@nbu.edu.sa)
