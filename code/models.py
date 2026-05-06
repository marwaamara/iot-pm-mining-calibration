"""
ML/DL Calibration Models for IoT PM Sensor Correction.

Implements multiple calibration approaches:
1. Linear Regression (baseline — traditional affine correction)
2. Multiple Linear Regression with environmental covariates
3. Random Forest Regression
4. Artificial Neural Network (ANN)
5. 1D-CNN for temporal pattern recognition

Each model is evaluated with metrological metrics per GUM/VIM standards.

References:
- Koziel et al. (2024), Measurement, DOI: 10.1016/j.measurement.2024.114529
- Liu et al. (2025), Measurement, DOI: 10.1016/j.measurement.2025.118987
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow import keras
from config import *


def prepare_features(df, sensor_id=1, pm_type="pm25", include_temporal=False):
    """
    Prepare feature matrix for calibration models.

    Features:
    - Raw sensor reading (primary input)
    - Temperature, humidity, wind speed (environmental covariates)
    - Deployment day (drift proxy)
    - Hour of day (operational pattern)
    """
    features = {
        "sensor_raw": df[f"sensor{sensor_id}_{pm_type}"].values,
        "temperature": df["temperature_C"].values,
        "humidity": df["humidity_pct"].values,
        "wind_speed": df["wind_speed_ms"].values,
        "day": df["day"].values,
        "hour_of_day": df["hour_of_day"].values,
    }

    X = np.column_stack(list(features.values()))
    y = df[f"ref_{pm_type}"].values

    feature_names = list(features.keys())

    if include_temporal:
        # Add rolling statistics (8-sample window = 2 hours)
        raw = df[f"sensor{sensor_id}_{pm_type}"].values
        window = 8
        rolling_mean = pd.Series(raw).rolling(window, min_periods=1).mean().values
        rolling_std = pd.Series(raw).rolling(window, min_periods=1).std().fillna(0).values
        rolling_max = pd.Series(raw).rolling(window, min_periods=1).max().values
        X = np.column_stack([X, rolling_mean, rolling_std, rolling_max])
        feature_names.extend(["rolling_mean_2h", "rolling_std_2h", "rolling_max_2h"])

    return X, y, feature_names


# ============================================================
# Model 1: Simple Linear Regression (Affine Correction)
# ============================================================
class AffineCalibration:
    """
    Traditional affine correction: y = a * x + b
    Baseline method per Koziel et al. (2024).
    """
    def __init__(self):
        self.name = "Affine (Linear)"
        self.model = LinearRegression()

    def fit(self, X, y):
        self.model.fit(X[:, 0:1], y)  # Only raw sensor reading
        return self

    def predict(self, X):
        return self.model.predict(X[:, 0:1])


# ============================================================
# Model 2: Multiple Linear Regression with Covariates
# ============================================================
class MLRCalibration:
    """
    Multiple linear regression with environmental covariates.
    y = a0 + a1*sensor + a2*temp + a3*hum + a4*wind + a5*day + a6*hour
    """
    def __init__(self):
        self.name = "MLR + Covariates"
        self.model = LinearRegression()
        self.scaler = StandardScaler()

    def fit(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return self

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)


# ============================================================
# Model 3: Random Forest
# ============================================================
class RFCalibration:
    """
    Random Forest calibration with environmental covariates.
    Captures non-linear sensor response characteristics.
    """
    def __init__(self):
        self.name = "Random Forest"
        self.model = RandomForestRegressor(
            n_estimators=RF_N_ESTIMATORS,
            max_depth=RF_MAX_DEPTH,
            random_state=RANDOM_SEED,
            n_jobs=-1
        )
        self.scaler = StandardScaler()

    def fit(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return self

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def feature_importance(self, feature_names):
        return dict(zip(feature_names, self.model.feature_importances_))


# ============================================================
# Model 4: Gradient Boosting Regression
# ============================================================
class GBRCalibration:
    """Gradient Boosting Regression for sensor calibration."""
    def __init__(self):
        self.name = "Gradient Boosting"
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            random_state=RANDOM_SEED
        )
        self.scaler = StandardScaler()

    def fit(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return self

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)


# ============================================================
# Model 5: Artificial Neural Network
# ============================================================
class ANNCalibration:
    """
    ANN calibration model per Koziel et al. (2024) methodology.
    Architecture: Input -> 64 -> 32 -> 16 -> 1
    With dropout for regularization.
    """
    def __init__(self):
        self.name = "ANN"
        self.model = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.history = None

    def _build_model(self, input_dim):
        model = keras.Sequential([
            keras.layers.Input(shape=(input_dim,)),
            keras.layers.Dense(ANN_HIDDEN_LAYERS[0], activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(ANN_HIDDEN_LAYERS[1], activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.1),
            keras.layers.Dense(ANN_HIDDEN_LAYERS[2], activation="relu"),
            keras.layers.Dense(1)
        ])
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=ANN_LEARNING_RATE),
            loss="mse",
            metrics=["mae"]
        )
        return model

    def fit(self, X, y):
        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

        self.model = self._build_model(X.shape[1])

        early_stop = keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=15, restore_best_weights=True
        )
        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, min_lr=1e-6
        )

        self.history = self.model.fit(
            X_scaled, y_scaled,
            epochs=ANN_EPOCHS,
            batch_size=ANN_BATCH_SIZE,
            validation_split=VAL_SPLIT,
            callbacks=[early_stop, reduce_lr],
            verbose=0
        )
        return self

    def predict(self, X):
        X_scaled = self.scaler_X.transform(X)
        y_scaled = self.model.predict(X_scaled, verbose=0).ravel()
        return self.scaler_y.inverse_transform(y_scaled.reshape(-1, 1)).ravel()


# ============================================================
# Model 6: 1D-CNN for Temporal Pattern Recognition
# ============================================================
class CNNCalibration:
    """
    1D Convolutional Neural Network for temporal pattern recognition.
    Processes sequences of sensor readings to capture temporal drift
    and operational patterns.
    """
    def __init__(self, sequence_length=8):
        self.name = "1D-CNN"
        self.sequence_length = sequence_length
        self.model = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.history = None

    def _create_sequences(self, X, y=None):
        """Create sliding window sequences for CNN input."""
        sequences = []
        targets = []
        for i in range(self.sequence_length, len(X)):
            sequences.append(X[i - self.sequence_length:i])
            if y is not None:
                targets.append(y[i])
        sequences = np.array(sequences)
        if y is not None:
            return sequences, np.array(targets)
        return sequences

    def _build_model(self, input_shape):
        model = keras.Sequential([
            keras.layers.Input(shape=input_shape),
            keras.layers.Conv1D(32, kernel_size=3, activation="relu", padding="same"),
            keras.layers.BatchNormalization(),
            keras.layers.Conv1D(64, kernel_size=3, activation="relu", padding="same"),
            keras.layers.BatchNormalization(),
            keras.layers.GlobalAveragePooling1D(),
            keras.layers.Dense(32, activation="relu"),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dense(1)
        ])
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=ANN_LEARNING_RATE),
            loss="mse",
            metrics=["mae"]
        )
        return model

    def fit(self, X, y):
        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

        X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)

        self.model = self._build_model((self.sequence_length, X.shape[1]))

        early_stop = keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=15, restore_best_weights=True
        )

        self.history = self.model.fit(
            X_seq, y_seq,
            epochs=ANN_EPOCHS,
            batch_size=ANN_BATCH_SIZE,
            validation_split=VAL_SPLIT,
            callbacks=[early_stop],
            verbose=0
        )
        return self

    def predict(self, X):
        X_scaled = self.scaler_X.transform(X)
        X_seq = self._create_sequences(X_scaled)
        y_scaled = self.model.predict(X_seq, verbose=0).ravel()
        y_pred = self.scaler_y.inverse_transform(y_scaled.reshape(-1, 1)).ravel()
        # Pad the first sequence_length predictions with NaN
        return np.concatenate([np.full(self.sequence_length, np.nan), y_pred])


# ============================================================
# Metrological Evaluation Metrics (GUM/VIM compliant)
# ============================================================
def compute_metrological_metrics(y_true, y_pred, model_name=""):
    """
    Compute measurement science metrics per GUM/VIM standards.

    Returns dict with:
    - RMSE: Root Mean Square Error (measurement uncertainty proxy)
    - MAE: Mean Absolute Error
    - R2: Coefficient of determination
    - MBE: Mean Bias Error (systematic error / measurement bias)
    - MAPE: Mean Absolute Percentage Error
    - u_A: Type A standard uncertainty (statistical)
    - U_expanded: Expanded uncertainty (k=2, ~95% coverage)
    - max_error: Maximum absolute error
    - within_uncertainty: % of predictions within expanded uncertainty
    """
    # Remove NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    residuals = y_pred - y_true
    n = len(y_true)

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mbe = np.mean(residuals)  # Systematic error (bias)
    mape = np.mean(np.abs(residuals) / np.maximum(y_true, 1)) * 100

    # Type A uncertainty (GUM Section 4.2): standard deviation of residuals
    u_A = np.std(residuals, ddof=1)

    # Expanded uncertainty (GUM Section 6.2): U = k * u_c
    # Combined standard uncertainty u_c ≈ u_A for this case
    U_expanded = COVERAGE_FACTOR_K * u_A

    # Maximum absolute error
    max_error = np.max(np.abs(residuals))

    # Percentage within expanded uncertainty bounds
    within_U = np.mean(np.abs(residuals) <= U_expanded) * 100

    metrics = {
        "Model": model_name,
        "n": n,
        "RMSE (ug/m3)": round(rmse, 2),
        "MAE (ug/m3)": round(mae, 2),
        "R2": round(r2, 4),
        "MBE (ug/m3)": round(mbe, 2),
        "MAPE (%)": round(mape, 2),
        "u_A (ug/m3)": round(u_A, 2),
        "U_expanded (ug/m3)": round(U_expanded, 2),
        "Max Error (ug/m3)": round(max_error, 2),
        "Within U (%)": round(within_U, 2),
    }

    return metrics


def compute_concentration_bin_metrics(y_true, y_pred, bins=None):
    """
    Evaluate calibration performance across concentration ranges.
    Important for mining where PM levels span 2 orders of magnitude.
    """
    if bins is None:
        bins = [0, 50, 100, 200, 350, 500, np.inf]
    bin_labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins) - 1)]

    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    results = []
    for i in range(len(bins) - 1):
        idx = (y_true >= bins[i]) & (y_true < bins[i + 1])
        if idx.sum() == 0:
            continue
        yt = y_true[idx]
        yp = y_pred[idx]
        results.append({
            "Concentration Range": bin_labels[i],
            "n": int(idx.sum()),
            "RMSE": round(np.sqrt(mean_squared_error(yt, yp)), 2),
            "MAE": round(mean_absolute_error(yt, yp), 2),
            "R2": round(r2_score(yt, yp) if len(yt) > 1 else 0, 4),
            "MBE": round(np.mean(yp - yt), 2),
        })

    return pd.DataFrame(results)


def cross_validate_model(model_class, X, y, n_folds=N_FOLDS, **kwargs):
    """
    K-fold cross-validation with metrological metrics.
    Returns mean and std of each metric across folds.
    """
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
    fold_metrics = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        model = model_class(**kwargs)
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)

        metrics = compute_metrological_metrics(y_val, y_pred, f"Fold {fold+1}")
        fold_metrics.append(metrics)

    # Aggregate results
    df_folds = pd.DataFrame(fold_metrics)
    numeric_cols = df_folds.select_dtypes(include=[np.number]).columns
    summary = {}
    for col in numeric_cols:
        if col == "n":
            continue
        summary[f"{col} (mean)"] = round(df_folds[col].mean(), 3)
        summary[f"{col} (std)"] = round(df_folds[col].std(), 3)

    return summary, df_folds
