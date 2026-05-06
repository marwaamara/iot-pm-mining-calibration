# KAPSARC Riyadh Air Quality Dataset (2022–2024)

This folder contains the reference environmental and PM data used as the
ground truth for the semi-synthetic primary case study in the manuscript.

## Source

* **Provider:** King Abdullah Petroleum Studies and Research Center
  (KAPSARC), Riyadh, Kingdom of Saudi Arabia
* **Portal:** <https://datasource.kapsarc.org>
* **Dataset:** Riyadh Air Quality 2022–2024
* **Underlying network:** General Authority of Meteorology and
  Environmental Protection (GAMEP) reference monitoring stations in Riyadh
* **Licence:** CC0 (public domain dedication)

## Files in this folder

| File | Size | What it is |
|---|---|---|
| `riyadh_air_quality_2021_2023.csv` | 11 MB | Raw KAPSARC export. Used as input to `code/data_generator.py`. |
| `mining_pm_sensor_data.csv` | 2.9 MB | Cached output of `code/data_generator.py`. Includes the 5 simulated PMS5003 sensor signals used in the experiments. **Deterministic given `RANDOM_SEED = 42` in `code/config.py`.** |

## How the cached file was produced

Run, from the repository root:

```bash
python code/data_generator.py
```

This loads `riyadh_air_quality_2021_2023.csv`, filters to the Riyadh
subset, aligns the timestamp index, and adds five simulated low-cost
sensor channels per the published Plantower PMS5003 error model with
the parameter values listed in `code/config.py`. Output is written to
`mining_pm_sensor_data.csv` (replacing the cached copy).

You can perturb any parameter (gain, drift, offset, noise, T-coefficient,
RH-coefficient, dust-composition factor) in `code/config.py` and rerun to
study the methodology's sensitivity to those choices — this is what
`code/sensitivity_analysis.py` does in an automated way (see
Section 5.7 of the manuscript).

## How to cite the KAPSARC reference data

> King Abdullah Petroleum Studies and Research Center (KAPSARC), Riyadh
> Air Quality Dataset 2022–2024, KAPSARC Data Portal, 2024.
> <https://datasource.kapsarc.org>
