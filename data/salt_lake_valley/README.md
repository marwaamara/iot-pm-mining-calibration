# Salt Lake Valley dust-event dataset (Kelly et al., 2023)

This folder contains a real co-located low-cost-sensor + reference
dataset used as a real-data validation case for the calibration
pipeline implemented in this repository.

## Source

* **Authors:** Kerry E. Kelly and Kamaljeet Kaur (Department of Chemical
  Engineering, University of Utah)
* **Repository:** *The Hive* — University of Utah Research Data Repository
* **DOI:** <https://doi.org/10.7278/S50d-xbns-3ge3>
* **Companion paper:** Kelly K., Kaur K., Sleeth M., Whitaker J.,
  Sayahi P., Butterfield A. (2023). Performance evaluation of the
  Alphasense OPC-N3 and Plantower PMS5003 sensor in measuring dust
  events in the Salt Lake Valley, Utah. *Atmospheric Measurement
  Techniques* **16**, 2455–2470.
  <https://doi.org/10.5194/amt-16-2455-2023>
* **Licence:** CC BY 3.0 — free to use and redistribute with attribution

## Files in this folder

| File | Size | What it is |
|---|---|---|
| `Data_Set_for_the_AMT.xlsx` | 740 KB | Original raw dataset from The Hive (verbatim copy). Multi-sheet workbook. |
| `Kelly_Readme20221019.txt` | 16 KB | Original variable dictionary from the dataset authors. |
| `salt_lake_valley_clean.csv` | 95 KB | Cached output of `code/load_salt_lake_valley.py`. Schema-aligned to `mining_pm_sensor_data.csv`. |

## What the cleaning script does

Run, from the repository root:

```bash
python code/load_salt_lake_valley.py
```

It performs the following operations on the raw xlsx:

1. Reads only the **Hawthorne (HW)** sheet — the only sheet that
   contains environmental covariates (T, RH, wind), FEM PM₂.₅,
   FEM PM₁₀ and three co-located PMS5003 nodes.
2. Renames the sensor columns to `sensor1_pm10`, `sensor2_pm10`,
   `sensor3_pm10` and the reference columns to `ref_pm25`, `ref_pm10`.
3. Converts temperature from °F to °C and wind speed from knots to m/s.
4. Applies the same QA rule as Kelly et al.: **excludes RH > 85 %** to
   avoid the well-known PMS5003 hygroscopic-growth artefact.
5. Drops physically impossible negative concentrations.
6. Adds `day` (days since first sample) and `hour_of_day` features so
   the schema matches the cleaned KAPSARC data.

After cleaning, **694 hourly records** remain (April 2022, FEM PM₁₀
range 0–274 µg/m³, including multiple documented dust events).

## How to cite this dataset

If you use this dataset in your own work, please cite **both** the
data repository and the Kelly et al. AMT paper:

> Kelly, K. and Kaur, K. (2022). *Dataset for: Performance evaluation
> of the Alphasense OPC-N3 and Plantower PMS5003 sensor in measuring
> dust events in the Salt Lake Valley, Utah.* The Hive: University of
> Utah Research Data Repository.
> <https://doi.org/10.7278/S50d-xbns-3ge3>

> Kelly K., Kaur K., Sleeth M., Whitaker J., Sayahi P., Butterfield A.
> (2023). Performance evaluation of the Alphasense OPC-N3 and Plantower
> PMS5003 sensor in measuring dust events in the Salt Lake Valley,
> Utah. *Atmos. Meas. Tech.* **16**, 2455–2470.
