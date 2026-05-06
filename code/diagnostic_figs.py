"""Generate diagnostic figures (learning curves, train-test gap, hparam sweeps,
SLV scatter etc.) from CSVs already produced."""
from __future__ import annotations
import os, sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300,
    "font.family": "serif", "font.size": 10,
    "axes.grid": True, "grid.alpha": 0.25,
    "axes.spines.top": False, "axes.spines.right": False,
})

REPO_ROOT = Path(__file__).resolve().parents[1]
# (REV no longer needed in flat repo layout)

CURVES = REPO_ROOT / "results" / "figures"
FIGS = CURVES / "figures"
TABLES = REPO_ROOT / "results" / "tables"
FIGS.mkdir(parents=True, exist_ok=True)


def fig_learning_curves(label="kapsarc"):
    csv = CURVES / f"learning_curves_{label}.csv"
    if not csv.exists():
        print(f"  (skip) no {csv.name}"); return
    df = pd.read_csv(csv)
    fig, ax = plt.subplots(figsize=(6, 4))
    for name, sub in df.groupby("model"):
        sub = sub.sort_values("n_train")
        ax.plot(sub["n_train"], sub["RMSE_train"], "--", label=f"{name} (train)")
        ax.plot(sub["n_train"], sub["RMSE_test"],  "-", label=f"{name} (test)")
    ax.set_xlabel("Training samples"); ax.set_ylabel(r"RMSE, $\mu$g/m$^3$")
    ax.set_title(f"Learning curves ({label.upper()})")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    out = FIGS / f"fig_learning_{label}.png"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print(f"  -> {out.name}")


def fig_train_test_gap(label="kapsarc"):
    csv = CURVES / f"train_test_gap_{label}.csv"
    if not csv.exists():
        print(f"  (skip) no {csv.name}"); return
    df = pd.read_csv(csv)
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    x = np.arange(len(df))
    w = 0.4
    ax.bar(x - w/2, df["RMSE_train"], w, label="Train RMSE", color="#2c7fb8")
    ax.bar(x + w/2, df["RMSE_test"],  w, label="Test RMSE",  color="#7fbc41")
    ax.set_xticks(x); ax.set_xticklabels(df["model"])
    ax.set_ylabel(r"RMSE, $\mu$g/m$^3$")
    ax.set_title(f"Train vs Test RMSE ({label.upper()})")
    ax.legend()
    fig.tight_layout()
    out = FIGS / f"fig_train_test_gap_{label}.png"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print(f"  -> {out.name}")


def fig_hparam_curves(label="kapsarc"):
    csv = CURVES / f"hyperparam_curves_{label}.csv"
    if not csv.exists():
        print(f"  (skip) no {csv.name}"); return
    df = pd.read_csv(csv)
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.0), sharey=False)
    sweeps = ["RF_n_estimators", "RF_max_depth", "GBR_n_estimators", "GBR_max_depth"]
    for ax, sw in zip(axes.flat, sweeps):
        sub = df[df["sweep"] == sw].sort_values("value")
        if len(sub) == 0: continue
        ax.errorbar(sub["value"], sub["RMSE_mean"], yerr=sub["RMSE_std"],
                    fmt="o-", capsize=3, color="#1f4e79")
        ax.set_title(sw.replace("_", " "))
        ax.set_xlabel("hyperparameter value")
        ax.set_ylabel(r"5-fold CV RMSE, $\mu$g/m$^3$")
    fig.suptitle(f"Hyperparameter sweeps ({label.upper()})", y=1.02)
    fig.tight_layout()
    out = FIGS / f"fig_hparam_{label}.png"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print(f"  -> {out.name}")


def fig_bin_analysis():
    csv = TABLES / "concentration_bin_analysis.csv"
    if not csv.exists():
        print(f"  (skip) no {csv.name}"); return
    df = pd.read_csv(csv)
    df = df[~df["RMSE"].isna()]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for label, ax in zip(["kapsarc", "slv"], axes):
        sub = df[df["dataset"] == label].copy()
        if len(sub) == 0: continue
        x = np.arange(len(sub))
        ax.bar(x, sub["NRMSE_pct"], color="#3a72bf", label="NRMSE [%]")
        ax2 = ax.twinx()
        ax2.errorbar(x, sub["R2"], yerr=[sub["R2"] - sub["R2_lo"],
                                         sub["R2_hi"] - sub["R2"]],
                     fmt="ro-", capsize=3, label=r"$R^2$ (95% CI)")
        ax.set_xticks(x); ax.set_xticklabels(sub["bin"], rotation=20)
        ax.set_ylabel("NRMSE (%)"); ax2.set_ylabel(r"$R^2$ with 95% CI")
        ax2.axhline(0, color="black", lw=0.5)
        ax.set_title(label.upper())
    fig.tight_layout()
    out = FIGS / "fig_bin_analysis.png"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print(f"  -> {out.name}")


if __name__ == "__main__":
    print("Generating diagnostic figures ...")
    for ds in ("kapsarc", "slv"):
        fig_learning_curves(ds)
        fig_train_test_gap(ds)
        fig_hparam_curves(ds)
    fig_bin_analysis()
    print("Done.")
