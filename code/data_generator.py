"""
Semi-Synthetic Data Generator for IoT PM Sensor Calibration in Mining.

Uses REAL environmental and PM data from the KAPSARC Riyadh Air Quality
Dataset (2022-2024), collected by the General Authority of Meteorology
and Environmental Protection (GAMEP) monitoring stations in Riyadh, KSA.

The low-cost IoT sensor responses are SIMULATED using the published
PMS5003 optical particle counter error model, incorporating:
- Gain drift (optical degradation from dust coating)
- Temperature sensitivity (Mie scattering refractive index shift)
- Humidity sensitivity (hygroscopic particle growth)
- Mining dust composition bias (crystalline silica vs urban aerosol)
- Heteroscedastic noise and occasional outliers

Reference:
- Koziel et al. (2024), Measurement, DOI: 10.1016/j.measurement.2024.114529
- Tripathi et al. (2024), Sci. Reports, DOI: 10.1038/s41598-024-58021-x
- KAPSARC Data Portal: https://datasource.kapsarc.org
"""

import numpy as np
import pandas as pd
from config import *


def load_kapsarc_data():
    """
    Load and preprocess the KAPSARC Riyadh Air Quality Dataset.

    Returns a clean DataFrame with hourly reference PM2.5, PM10,
    temperature, humidity, and wind speed from Riyadh stations.
    """
    print(f"Loading KAPSARC data from {KAPSARC_PATH}...")
    df_raw = pd.read_csv(KAPSARC_PATH)

    # Filter for Riyadh (largest subset: ~72,000 records)
    df = df_raw[df_raw["city"] == CITY].copy()
    print(f"  Riyadh records: {len(df)}")

    # Parse datetime
    df["datetime"] = pd.to_datetime(df["date"])

    # Rename columns for consistency
    col_map = {
        "PM2.5": "ref_pm25",
        "PM10": "ref_pm10",
    }
    # Handle encoding issues in column names
    for col in df.columns:
        if "temperature" in col.lower():
            col_map[col] = "temperature_C"
        elif "humidity" in col.lower():
            col_map[col] = "humidity_pct"
        elif "wind_speed" in col.lower():
            col_map[col] = "wind_speed_kmh"
    df = df.rename(columns=col_map)

    # Convert wind speed from km/h to m/s
    df["wind_speed_ms"] = df["wind_speed_kmh"] / 3.6

    # Deduplicate: keep one row per datetime (aggregate across components)
    # Each datetime/station combination has multiple rows (one per component)
    agg_cols = ["datetime", "ref_pm25", "ref_pm10", "temperature_C",
                "humidity_pct", "wind_speed_ms"]
    df = df[agg_cols].drop_duplicates(subset=["datetime"]).sort_values("datetime")
    df = df.reset_index(drop=True)

    print(f"  Unique hourly records: {len(df)}")
    print(f"  Date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
    print(f"  PM2.5 range: {df['ref_pm25'].min()}-{df['ref_pm25'].max()} ug/m3")
    print(f"  Temperature range: {df['temperature_C'].min():.1f}-{df['temperature_C'].max():.1f} C")
    print(f"  Humidity range: {df['humidity_pct'].min():.1f}-{df['humidity_pct'].max():.1f} %")
    print(f"  Wind speed range: {df['wind_speed_ms'].min():.1f}-{df['wind_speed_ms'].max():.1f} m/s")

    return df


def generate_sensor_readings(ref_pm, temp, humidity, days, sensor_id, seed=RANDOM_SEED):
    """
    Simulate low-cost IoT sensor (PMS5003) readings from real reference data.

    Applies the published sensor error model:
    y_raw = x_ref * g(d) * f_T(T) * f_RH(RH) * kappa + b + epsilon

    Each sensor has unique degradation characteristics (different seed offsets).
    """
    rng = np.random.default_rng(seed + sensor_id * 100)
    n_samples = len(ref_pm)

    # 1. Gain drift: linear degradation + periodic partial recovery (cleaning)
    base_drift = SENSOR_GAIN_DRIFT_RATE * days
    # Simulate monthly cleaning events (partial recovery)
    cleaning_events = np.zeros_like(days)
    max_months = int(days.max() / 30) + 1
    for month in range(1, max_months):
        clean_day = month * 30
        mask = days >= clean_day
        cleaning_events[mask] -= 0.4 * SENSOR_GAIN_DRIFT_RATE * 30  # 40% recovery
    gain = SENSOR_GAIN_NOMINAL - base_drift - cleaning_events
    gain += rng.normal(0, 0.01, n_samples)  # Small gain jitter
    # Each sensor has slightly different degradation rate
    gain *= (1 + 0.1 * rng.standard_normal())

    # 2. Temperature effect (Mie scattering sensitivity)
    temp_ref = 30.0  # Reference temperature for KSA
    temp_effect = 1 + TEMP_COEFF * (temp - temp_ref)

    # 3. Humidity effect (hygroscopic growth overestimates PM)
    hum_ref = 30.0  # Reference humidity for KSA
    humidity_effect = 1 + HUMIDITY_COEFF * (humidity - hum_ref)

    # 4. Mining dust composition bias (silica optical properties)
    composition_bias = DUST_COMPOSITION_FACTOR + 0.05 * rng.standard_normal()

    # 5. Combined sensor reading
    sensor_pm = ref_pm * gain * temp_effect * humidity_effect * composition_bias
    sensor_pm += SENSOR_OFFSET_NOMINAL * (1 + 0.3 * rng.standard_normal())

    # 6. Random noise (heteroscedastic: proportional to concentration)
    noise = rng.normal(0, SENSOR_NOISE_STD + 0.03 * sensor_pm, n_samples)
    sensor_pm += noise

    # 7. Outliers (~1% of readings: saturation, communication glitches)
    outlier_mask = rng.random(n_samples) < 0.01
    sensor_pm[outlier_mask] *= rng.uniform(0.1, 3.0, outlier_mask.sum())

    sensor_pm = np.clip(sensor_pm, 0, 2000)

    return sensor_pm


def generate_full_dataset():
    """
    Generate the complete semi-synthetic dataset.

    Real data: reference PM concentrations + environmental conditions (KAPSARC)
    Simulated: low-cost IoT sensor responses (PMS5003 error model)
    """
    # Load real KAPSARC data
    df_real = load_kapsarc_data()

    n_samples = len(df_real)
    days = np.arange(n_samples) / 24.0  # Convert hours to days

    # Build output DataFrame
    df = pd.DataFrame({
        "timestamp": df_real["datetime"].values,
        "day": np.round(days, 4),
        "hour_of_day": df_real["datetime"].dt.hour.values.astype(float),
        "temperature_C": df_real["temperature_C"].values,
        "humidity_pct": df_real["humidity_pct"].values,
        "wind_speed_ms": np.round(df_real["wind_speed_ms"].values, 2),
        "ref_pm25": df_real["ref_pm25"].values.astype(float),
        "ref_pm10": df_real["ref_pm10"].values.astype(float),
    })

    ref_pm25 = df["ref_pm25"].values
    ref_pm10 = df["ref_pm10"].values
    temp = df["temperature_C"].values
    humidity = df["humidity_pct"].values

    # Generate simulated IoT sensor readings
    print(f"\nGenerating simulated PMS5003 sensor readings for {N_SENSORS} nodes...")
    for s in range(N_SENSORS):
        df[f"sensor{s+1}_pm25"] = np.round(
            generate_sensor_readings(ref_pm25, temp, humidity, days, s), 2
        )
        df[f"sensor{s+1}_pm10"] = np.round(
            generate_sensor_readings(ref_pm10, temp, humidity, days, s + 10), 2
        )

    # Save
    output_path = KAPSARC_DIR / "mining_pm_sensor_data.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to {output_path}")
    print(f"Shape: {df.shape}")
    print(f"  Real data (KAPSARC): reference PM, temperature, humidity, wind speed")
    print(f"  Simulated data: {N_SENSORS} low-cost sensor responses (PMS5003 model)")
    print(f"\nDescriptive Statistics:")
    print(df.describe().round(2))

    return df


if __name__ == "__main__":
    df = generate_full_dataset()
