"""
Load and clean the Kelly et al. 2023 Salt Lake Valley dust-event dataset.

Source: https://doi.org/10.7278/S50d-xbns-3ge3 (Hive, U of Utah, CC BY 3.0)
Reference: Kelly K., Kaur K., et al. (2023). Performance evaluation of the
Alphasense OPC-N3 and Plantower PMS5003 sensor in measuring dust events in
the Salt Lake Valley, Utah. AMT 16, 2455-2470. doi:10.5194/amt-16-2455-2023

Output schema (mirrors mining_pm_sensor_data.csv where applicable):
    timestamp, day, hour_of_day, temperature_C, humidity_pct, wind_speed_ms,
    ref_pm10, ref_pm25, sensor1_pm10, sensor2_pm10, sensor3_pm10, site

Design notes:
    * The dataset has 3 sites (HW, RS, EQ); only HW has T, RH, wind, FEM PM2.5,
      FEM PM10, AND PMS5003 nodes co-located. We use HW as primary.
    * EQ has FEM PM10 + 4 PMS5003 nodes (no env covariates) — load separately
      and impute T/RH from HW (sites are ~5 km apart in Salt Lake Valley).
    * Sensor PMS5003 reports PM10 only (no PM2.5). Mining-relevant metric.
    * We exclude RH > 85 % rows (per dataset QA — Kelly et al. exclude these).
    * Wind in knots -> m/s (× 0.514444). Temperature in F -> C.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_XLSX = REPO_ROOT / "data" / "salt_lake_valley" / "Data_Set_for_the_AMT.xlsx"
OUT_CSV = REPO_ROOT / "data" / "salt_lake_valley" / "salt_lake_valley_clean.csv"


def _knots_to_ms(x):
    return x * 0.514444


def _f_to_c(x):
    return (x - 32.0) * 5.0 / 9.0


def load_hw():
    """Hawthorne (HW) site — has env covariates + FEM PM2.5/PM10 + 3 PMS nodes."""
    df = pd.read_excel(RAW_XLSX, sheet_name="HW", engine="openpyxl",
                       usecols="A:M")  # leftmost raw-data block; rest is RMSE bookkeeping
    df.columns = [str(c).strip() for c in df.columns]

    rename = {
        "Date": "timestamp",
        "Wind speed (Knots)": "wind_speed_knots",
        "Wind direction (degree compass)": "wind_dir_deg",
        "Temp F": "temp_F",
        "RH %": "rh_pct",
        "FEM-HW PM2.5 ug/m3": "ref_pm25",
        "FEM-HW PM10": "ref_pm10",
        "PMS-HW-1A": "sensor1_pm10",
        "PMS-HW-2A": "sensor2_pm10",
        "PMS-HW-2B": "sensor3_pm10",
    }
    df = df.rename(columns=rename)
    keep = [
        "timestamp", "wind_speed_knots", "wind_dir_deg", "temp_F", "rh_pct",
        "ref_pm25", "ref_pm10",
        "sensor1_pm10", "sensor2_pm10", "sensor3_pm10",
    ]
    df = df[[c for c in keep if c in df.columns]].copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["temperature_C"] = _f_to_c(pd.to_numeric(df["temp_F"], errors="coerce"))
    df["humidity_pct"] = pd.to_numeric(df["rh_pct"], errors="coerce")
    df["wind_speed_ms"] = _knots_to_ms(
        pd.to_numeric(df["wind_speed_knots"], errors="coerce")
    )
    for c in ["ref_pm25", "ref_pm10",
              "sensor1_pm10", "sensor2_pm10", "sensor3_pm10"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["site"] = "HW"

    return df.drop(columns=["temp_F", "rh_pct", "wind_speed_knots", "wind_dir_deg"])


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply QA rules per Kelly et al. and add temporal features."""
    n0 = len(df)

    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    required = ["ref_pm10", "sensor1_pm10", "sensor2_pm10", "sensor3_pm10",
                "temperature_C", "humidity_pct"]
    df = df.dropna(subset=required)

    # Kelly et al. QA: exclude RH > 85 %
    df = df[df["humidity_pct"] <= 85.0].copy()

    # Drop physically impossible (negative concentrations from sensor errors)
    for c in ["ref_pm25", "ref_pm10",
              "sensor1_pm10", "sensor2_pm10", "sensor3_pm10"]:
        if c in df.columns:
            df = df[(df[c].isna()) | (df[c] >= 0)]

    df = df.reset_index(drop=True)

    # Temporal features (consistent with KAPSARC schema)
    t0 = df["timestamp"].iloc[0]
    df["day"] = (df["timestamp"] - t0).dt.total_seconds() / 86400.0
    df["day"] = df["day"].round(4)
    df["hour_of_day"] = df["timestamp"].dt.hour.astype(float)

    print(f"  Rows: {n0} -> {len(df)} after cleaning")
    return df


def main():
    if not RAW_XLSX.exists():
        print(f"ERROR: {RAW_XLSX} not found. Run download step first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading Salt Lake Valley dataset from {RAW_XLSX}")
    print("Site: Hawthorne (HW) — has T, RH, wind, FEM PM2.5/PM10, 3 PMS5003 nodes")
    df_hw = load_hw()
    print(f"  HW raw rows: {len(df_hw)}")

    df = clean(df_hw)

    cols = ["timestamp", "day", "hour_of_day",
            "temperature_C", "humidity_pct", "wind_speed_ms",
            "ref_pm25", "ref_pm10",
            "sensor1_pm10", "sensor2_pm10", "sensor3_pm10",
            "site"]
    df_out = df[[c for c in cols if c in df.columns]]
    df_out.to_csv(OUT_CSV, index=False)

    print()
    print(f"Saved -> {OUT_CSV}")
    print(f"Final rows: {len(df_out)}")
    print(f"Date range: {df_out['timestamp'].min()} -> {df_out['timestamp'].max()}")
    print()
    print("Summary statistics:")
    desc = df_out[[c for c in df_out.columns
                   if c not in ("timestamp", "site")]].describe().T
    print(desc[["count", "mean", "std", "min", "50%", "max"]].round(2))

    print()
    print("Pairwise correlations (PMS sensors vs FEM PM10):")
    cor_cols = ["ref_pm10", "sensor1_pm10", "sensor2_pm10", "sensor3_pm10"]
    print(df_out[cor_cols].corr().round(3))


if __name__ == "__main__":
    main()
