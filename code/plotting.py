"""
Publication-quality figure regeneration for the major revision.

Addresses Reviewer 2 figure items 13-16, 24-26:
    * Fig 3 split into 5 sub-panels, one per sensor (item 14)
    * Identical x/y axis limits per 1:1 panel (item 15)
    * Padded axis ranges above the data max (items 13, 24, 25)
    * Co-location site description figure for the main text (item 26)
    * Sensor / instrument photographs in the main text (item 26)

Plus new figures driven by Reviewer 1's GUM rewrite:
    * Uncertainty Monte-Carlo distribution figure
    * Sensitivity analysis figure (PMS5003 error-model perturbations)
    * Salt Lake Valley calibration scatter (real-data validation)

All figures are saved as 300 DPI PNGs into major_revision/curves/figures/.
"""

from __future__ import annotations

import os, sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

FIGS = REPO_ROOT / "results" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

KAPSARC_CSV = REPO_ROOT / "data" / "kapsarc" / "mining_pm_sensor_data.csv"
SLV_CSV = REPO_ROOT / "data" / "salt_lake_valley" / "salt_lake_valley_clean.csv"


def _pad_lim(values, pad_frac=0.08, floor_zero=True):
    a = np.nanmin(values); b = np.nanmax(values)
    span = b - a
    lo = a - pad_frac * span if not floor_zero else max(0.0, a - pad_frac * span)
    hi = b + pad_frac * span
    return lo, hi


def _matched_lim(*arrays, pad_frac=0.10, floor_zero=True):
    cat = np.concatenate([np.asarray(a).ravel() for a in arrays])
    lo, hi = _pad_lim(cat, pad_frac=pad_frac, floor_zero=floor_zero)
    return lo, hi


# ---------------------------------------------------------------------------
# Figure 3: faceted scatter — one panel per sensor (R2 items 14, 15)
# ---------------------------------------------------------------------------

def fig3_faceted_per_sensor(df_kapsarc: pd.DataFrame,
                            n_sensors: int = 5,
                            pm: str = "pm25",
                            outpath: Path | None = None):
    """KAPSARC: one panel per simulated sensor, matched axes per panel
    (x-axis = sensor reading, y-axis = reference). 1:1 line per panel."""
    fig, axes = plt.subplots(1, n_sensors, figsize=(3.0 * n_sensors, 3.2),
                             sharey=False)
    ref = df_kapsarc[f"ref_{pm}"].values
    for i, ax in enumerate(axes, start=1):
        sensor = df_kapsarc[f"sensor{i}_{pm}"].values
        # Padded axis range — max of (sensor, ref) for both axes (item 15)
        lo, hi = _matched_lim(sensor, ref, pad_frac=0.05)
        ax.scatter(sensor, ref, s=4, alpha=0.20, color="#333", rasterized=True)
        ax.plot([lo, hi], [lo, hi], "r-", lw=1.0, label="1:1")
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(f"Sensor S{i}")
        ax.set_xlabel(rf"Raw {pm.upper()}, $\mu$g/m$^3$")
        if i == 1:
            ax.set_ylabel(rf"Reference {pm.upper()}, $\mu$g/m$^3$")
        # Annotate Pearson r and bias
        r = np.corrcoef(sensor, ref)[0, 1]
        bias = float(np.mean(sensor - ref))
        ax.text(0.04, 0.96, f"r = {r:.2f}\nMBE = {bias:+.1f}",
                transform=ax.transAxes, va="top", ha="left",
                fontsize=8, bbox=dict(boxstyle="round,pad=0.3",
                                      fc="white", ec="0.7", alpha=0.85))
    fig.tight_layout()
    out = outpath or (FIGS / "fig3_faceted_per_sensor.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Calibration scatter for predicted vs reference, all models — matched axes
# ---------------------------------------------------------------------------

def fig_calibration_scatter(y_true, predictions: dict, dataset_label: str,
                            pm_label: str, outpath: Path | None = None):
    n = len(predictions)
    cols = min(n, 3); rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.0 * rows),
                             squeeze=False)
    all_vals = [y_true]
    for v in predictions.values():
        all_vals.append(np.asarray(v).ravel())
    lo, hi = _matched_lim(*all_vals, pad_frac=0.06)
    for k, (name, yp) in enumerate(predictions.items()):
        r = k // cols; c = k % cols
        ax = axes[r][c]
        ax.scatter(yp, y_true, s=5, alpha=0.25, color="#1f4e79", rasterized=True)
        ax.plot([lo, hi], [lo, hi], "r-", lw=1.0)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(name)
        ax.set_xlabel(rf"Predicted {pm_label}")
        if c == 0:
            ax.set_ylabel(rf"Reference {pm_label}")
        rmse = float(np.sqrt(np.mean((y_true - yp) ** 2)))
        r2 = 1.0 - np.sum((y_true - yp) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2)
        ax.text(0.04, 0.96, f"RMSE = {rmse:.1f}\n$R^2$ = {r2:.3f}",
                transform=ax.transAxes, va="top", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85))
    # Hide leftover axes
    for k in range(n, rows * cols):
        axes[k // cols][k % cols].set_visible(False)
    fig.suptitle(f"{dataset_label}: predicted vs reference ({pm_label})")
    fig.tight_layout()
    out = outpath or (FIGS / f"fig_scatter_{dataset_label.lower()}.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Uncertainty MC distribution figure (R1 / new framework)
# ---------------------------------------------------------------------------

def fig_uncertainty_decomposition(budgets_df: pd.DataFrame, dataset_label: str,
                                  outpath: Path | None = None):
    """Stacked bar of u_A_model, u_input_MC, u_B_bias for each model."""
    df = budgets_df[budgets_df["model"] != "Uncalibrated"].copy()
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    x = np.arange(len(df))
    ax.bar(x, df["u_A_model"], label=r"$u_A^\mathrm{model}$ (OOF residuals)")
    ax.bar(x, df["u_input_MC"], bottom=df["u_A_model"],
           label=r"$u_\mathrm{input}^\mathrm{MC}$ (JCGM 101)")
    ax.bar(x, df["u_B_bias"], bottom=df["u_A_model"] + df["u_input_MC"],
           label=r"$u_B^\mathrm{bias}$ (rectangular)")
    # Mark expanded uncertainty
    ax.scatter(x, df["U"], color="black", marker="o", zorder=4,
               label=r"$U = k\,u_c$ (k=2)")
    ax.set_xticks(x); ax.set_xticklabels(df["model"])
    ax.set_ylabel(r"Standard uncertainty, $\mu$g/m$^3$")
    ax.set_title(f"{dataset_label}: GUM/JCGM-101 uncertainty decomposition")
    ax.legend(loc="upper right", framealpha=0.95)
    fig.tight_layout()
    out = outpath or (FIGS / f"fig_uncertainty_decomp_{dataset_label.lower()}.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Sensitivity analysis figure (R1 — methodology robust to synthetic params)
# ---------------------------------------------------------------------------

def fig_sensitivity(sens_df: pd.DataFrame, outpath: Path | None = None):
    base_rmse = float(sens_df.iloc[0]["RMSE_test"])
    others = sens_df.iloc[1:].copy()
    others["delta_RMSE"] = others["RMSE_test"] - base_rmse
    others["sign"] = np.where(others["delta_RMSE"] > 0, "increases RMSE",
                              "decreases RMSE")
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    y = np.arange(len(others))
    ax.barh(y, others["delta_RMSE"],
            color=np.where(others["delta_RMSE"] > 0, "#bf3939", "#3a72bf"))
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels(others["perturbation"])
    ax.set_xlabel(r"$\Delta$RMSE relative to baseline ($\mu$g/m$^3$)")
    ax.set_title(rf"Sensitivity to PMS5003 error-model parameters "
                 rf"(baseline RMSE = {base_rmse:.2f} $\mu$g/m$^3$)")
    ax.invert_yaxis()
    fig.tight_layout()
    out = outpath or (FIGS / "fig_sensitivity_analysis.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Salt Lake Valley faceted (3 PMS nodes + reference)
# ---------------------------------------------------------------------------

def fig_slv_faceted(outpath: Path | None = None):
    df = pd.read_csv(SLV_CSV)
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 3.2), sharey=False)
    ref = df["ref_pm10"].values
    for i, ax in enumerate(axes, start=1):
        s = df[f"sensor{i}_pm10"].values
        lo_x, hi_x = _matched_lim(s, pad_frac=0.05)
        lo_y, hi_y = _matched_lim(ref, pad_frac=0.05)
        ax.scatter(s, ref, s=8, alpha=0.55, color="#333", rasterized=True)
        # 1:1 line on the x range, since axes differ greatly
        common_lo = min(lo_x, lo_y); common_hi = max(hi_x, hi_y)
        ax.plot([common_lo, common_hi], [common_lo, common_hi], "r-", lw=1.0)
        ax.set_xlim(lo_x, hi_x); ax.set_ylim(lo_y, hi_y)
        ax.set_title(f"PMS5003 node {i}  (HW)")
        ax.set_xlabel(r"PMS PM$_{10}$, $\mu$g/m$^3$")
        if i == 1:
            ax.set_ylabel(r"FEM PM$_{10}$, $\mu$g/m$^3$")
        r = np.corrcoef(s, ref)[0, 1]
        bias = float(np.mean(s - ref))
        ax.text(0.04, 0.96, f"r = {r:.2f}\nMBE = {bias:+.1f}",
                transform=ax.transAxes, va="top", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7"))
    fig.suptitle("Salt Lake Valley (Kelly et al., 2023): raw PMS5003 vs FEM PM$_{10}$",
                 y=1.02)
    fig.tight_layout()
    out = outpath or (FIGS / "fig_slv_faceted_raw.png")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Co-location site description figure (composite / schematic)
# ---------------------------------------------------------------------------

def fig_colocation_schematic(outpath: Path | None = None):
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_aspect("equal")
    ax.set_axis_off()

    # Box: KAPSARC (semi-synthetic, primary)
    ax.add_patch(plt.Rectangle((0.3, 3.2), 4.4, 2.5,
                               fill=True, fc="#cce5ff", ec="black", lw=1.2))
    ax.text(2.5, 5.4, "Case study A (primary): KAPSARC Riyadh",
            ha="center", fontweight="bold", fontsize=10)
    ax.text(2.5, 4.85, "GAMEP reference station",
            ha="center", fontsize=9)
    ax.text(2.5, 4.45, "PM$_{2.5}$, T, RH, wind  (real)",
            ha="center", fontsize=9)
    ax.text(2.5, 3.95, "5 simulated PMS5003 sensors",
            ha="center", fontsize=9, color="#aa3300")
    ax.text(2.5, 3.55, "Period: 2022–2024  (n = 23,742)",
            ha="center", fontsize=9)

    # Box: Salt Lake Valley (real, secondary)
    ax.add_patch(plt.Rectangle((5.3, 3.2), 4.4, 2.5,
                               fill=True, fc="#d4f4d4", ec="black", lw=1.2))
    ax.text(7.5, 5.4, "Case study B (real): Hawthorne, SLV",
            ha="center", fontweight="bold", fontsize=10)
    ax.text(7.5, 4.85, "Kelly et al. 2023 — AMT 16, 2455",
            ha="center", fontsize=9)
    ax.text(7.5, 4.45, "FEM PM$_{2.5}$/PM$_{10}$, T, RH, wind",
            ha="center", fontsize=9)
    ax.text(7.5, 3.95, "3 real PMS5003 nodes co-located",
            ha="center", fontsize=9, color="#006600")
    ax.text(7.5, 3.55, "Period: April 2022  (n = 694)",
            ha="center", fontsize=9)

    # Pipeline arrows
    ax.annotate("", xy=(2.5, 2.3), xytext=(2.5, 3.2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
    ax.annotate("", xy=(7.5, 2.3), xytext=(7.5, 3.2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
    ax.text(5.0, 2.7, "Identical calibration + uncertainty pipeline",
            ha="center", fontsize=10, fontweight="bold", color="#333")

    # Pipeline box
    ax.add_patch(plt.Rectangle((1.2, 0.8), 7.6, 1.4,
                               fill=True, fc="#fff3cd", ec="black", lw=1.2))
    ax.text(5.0, 1.85,
            "ML calibration: Affine | MLR | RF | GBR | ANN",
            ha="center", fontweight="bold", fontsize=10)
    ax.text(5.0, 1.4,
            "GUM uncertainty: bias correction + OOF residuals + JCGM-101 MC",
            ha="center", fontsize=9)
    ax.text(5.0, 1.0, "+ time-series CV, learning curves, sensitivity",
            ha="center", fontsize=9, color="#444")

    fig.tight_layout()
    out = outpath or (FIGS / "fig_colocation_schematic.png")
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    print("Generating revision figures ...")

    # Fig 3 faceted (R2 items 14, 15)
    df_k = pd.read_csv(KAPSARC_CSV)
    out = fig3_faceted_per_sensor(df_k, n_sensors=5, pm="pm25")
    print(f"  -> {out.name}")

    # SLV faceted raw scatter
    out = fig_slv_faceted()
    print(f"  -> {out.name}")

    # Co-location schematic (R2 item 26)
    out = fig_colocation_schematic()
    print(f"  -> {out.name}")

    # Uncertainty decomposition (per dataset)
    df_kb = pd.read_csv(REPO_ROOT / "results" / "tables" / "calibration_results_kapsarc.csv")
    out = fig_uncertainty_decomposition(df_kb, "KAPSARC")
    print(f"  -> {out.name}")

    if (REPO_ROOT / "results" / "tables" / "calibration_results_slv.csv").exists():
        df_sb = pd.read_csv(REPO_ROOT / "results" / "tables" / "calibration_results_slv.csv")
        # If split column exists, plot the random-split block
        if "split" in df_sb.columns:
            df_sb = df_sb[df_sb["split"] == "random"].copy()
        if len(df_sb) > 0:
            out = fig_uncertainty_decomposition(df_sb, "SaltLakeValley")
            print(f"  -> {out.name}")

    # Sensitivity (R1)
    sens = pd.read_csv(REPO_ROOT / "results" / "tables" / "sensitivity_analysis.csv")
    out = fig_sensitivity(sens)
    print(f"  -> {out.name}")

    print("\nDone. Figures in:", FIGS)


if __name__ == "__main__":
    main()
