"""
Configuration constants for the IoT PM sensor calibration experiment.

Companion code for:
    Amara, M. (2026). AI-enhanced calibration of IoT particulate matter
    sensors in open-pit mining: a metrological approach to environmental
    cross-sensitivity compensation. Measurement (under review,
    MEAS-D-26-03768).

All paths are relative to the repository root, so the code runs unchanged
on any machine after `git clone`.
"""

from pathlib import Path

# === Repository layout ======================================================
# code/config.py is two levels below repo root, so repo root = parents[1].
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
KAPSARC_DIR = DATA_DIR / "kapsarc"
SLV_DIR = DATA_DIR / "salt_lake_valley"

# Where the cleaned KAPSARC CSV lives once the user has downloaded it
# (see data/kapsarc/README.md for the source URL and the cleaning rules).
KAPSARC_PATH = KAPSARC_DIR / "riyadh_air_quality_2021_2023.csv"
SLV_CLEAN_PATH = SLV_DIR / "salt_lake_valley_clean.csv"

# Outputs
RESULTS_DIR = REPO_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"

for d in (DATA_DIR, KAPSARC_DIR, SLV_DIR,
          RESULTS_DIR, TABLES_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# === Reproducibility ========================================================
RANDOM_SEED = 42

# === Dataset metadata =======================================================
N_SENSORS = 5                   # Simulated PMS5003 nodes co-located in KAPSARC
CITY = "Riyadh"                 # Primary KAPSARC subset
SAMPLING_INTERVAL_MIN = 60      # KAPSARC native resolution (hourly)

# === Reference-instrument uncertainty =======================================
# BAM-1020 manufacturer spec: relative standard uncertainty 2% of reading
# (with a per-sample floor of 0.5 ug/m^3 applied at runtime).
REF_UNCERTAINTY = 0.02

# === PMS5003 simulated error-model parameters ===============================
# These are the published Plantower / Koziel et al. 2024 + Tripathi et al. 2024
# values used to generate the semi-synthetic KAPSARC sensor signals.
# The sensitivity_analysis.py script perturbs each by +/- 20% to test
# robustness of the calibration methodology to parameter uncertainty.
SENSOR_GAIN_NOMINAL = 1.0
SENSOR_GAIN_DRIFT_RATE = 0.0005     # per day (cumulative dust-coating drift)
SENSOR_OFFSET_NOMINAL = 2.0         # ug/m^3 baseline offset
SENSOR_NOISE_STD = 5.0              # ug/m^3 white-noise standard deviation
HUMIDITY_COEFF = 0.015              # hygroscopic growth coefficient
TEMP_COEFF = -0.008                 # photodiode/laser thermal-drift coefficient
DUST_COMPOSITION_FACTOR = 1.15      # silica vs urban-aerosol Mie-bias factor

# === Train/test/CV ==========================================================
TEST_SPLIT = 0.2                # Last 20% temporal split (KAPSARC primary)
VAL_SPLIT = 0.1                 # Used only by ANN early-stopping callback
N_FOLDS = 5                     # k-fold CV (also used for OOF residuals)

# === ANN architecture ========================================================
ANN_HIDDEN_LAYERS = [64, 32, 16]
ANN_EPOCHS = 200
ANN_BATCH_SIZE = 64
ANN_LEARNING_RATE = 0.001

# === Tree ensembles =========================================================
RF_N_ESTIMATORS = 200           # Validated on the plateau via hyperparam_curves.py
RF_MAX_DEPTH = 15

# === Metrology constants ====================================================
CONFIDENCE_LEVEL = 0.95         # Nominal coverage for the expanded uncertainty
COVERAGE_FACTOR_K = 2           # k = 2 -> ~95% coverage (GUM 6.2)

# === Figure styling =========================================================
FIG_DPI = 300
FIG_FORMAT = "png"
FIG_FONT_SIZE = 12
FIG_FONT_FAMILY = "serif"
COLUMN_WIDTH_INCHES = 3.5       # Elsevier single-column
DOUBLE_COLUMN_WIDTH_INCHES = 7.0  # Elsevier double-column
