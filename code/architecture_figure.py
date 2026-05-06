"""Render the two-tier measurement-system architecture figure as PNG.

Replaces the heavyweight TikZ block in the manuscript so the document
compiles within the Overleaf-free 30 s timeout.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patheffects import withStroke

mpl.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300,
    "font.family": "serif", "font.size": 9,
})

FIGS = Path(__file__).resolve().parents[1] / "results" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
out = FIGS / "fig_architecture.png"


def box(ax, x, y, w, h, txt, fc, ec="black", lw=1.4, fs=8, fw="bold"):
    p = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle="round,pad=0.04,rounding_size=0.10",
                       fc=fc, ec=ec, lw=lw)
    ax.add_patch(p)
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs,
            fontweight=fw, linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, label=None, dashed=False, color="black",
          lw=1.2, label_pos=0.5, label_offset=(0, 0.18)):
    style = "->,head_length=4,head_width=3"
    p = FancyArrowPatch((x1, y1), (x2, y2),
                        arrowstyle=style, mutation_scale=10,
                        color=color, lw=lw,
                        linestyle="--" if dashed else "-")
    ax.add_patch(p)
    if label:
        lx = x1 + label_pos * (x2 - x1) + label_offset[0]
        ly = y1 + label_pos * (y2 - y1) + label_offset[1]
        ax.text(lx, ly, label, ha="center", va="center", fontsize=7,
                color="#404040",
                path_effects=[withStroke(linewidth=2.5, foreground="white")])


def main():
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7.0); ax.set_aspect("equal")
    ax.set_axis_off()

    # ------- Tier backgrounds (drawn first, behind content) -------
    # IoT Tier
    ax.add_patch(FancyBboxPatch((0.4, 0.4), 7.4, 1.9,
                 boxstyle="round,pad=0.05,rounding_size=0.18",
                 fc="#e6efff", ec="#5a7fc4", lw=0.9, ls="--"))
    ax.text(0.55, 1.35, "IoT Tier", rotation=90, ha="left", va="center",
            fontsize=9, fontweight="bold", color="#1f4e79")

    # Reference Tier
    ax.add_patch(FancyBboxPatch((0.4, 3.0), 2.4, 2.4,
                 boxstyle="round,pad=0.05,rounding_size=0.18",
                 fc="#ffe9e9", ec="#c45a5a", lw=0.9, ls="--"))
    ax.text(0.55, 4.2, "Reference Tier", rotation=90, ha="left", va="center",
            fontsize=9, fontweight="bold", color="#9a2424")

    # Processing
    ax.add_patch(FancyBboxPatch((3.6, 3.0), 10.0, 3.8,
                 boxstyle="round,pad=0.05,rounding_size=0.18",
                 fc="#e9f6e9", ec="#5aa05a", lw=0.9, ls="--"))
    ax.text(13.45, 4.9, "Processing", rotation=90, ha="right", va="center",
            fontsize=9, fontweight="bold", color="#246624")

    # ------- Reference Tier (BAM-1020) -------
    box(ax, 1.7, 4.2, 1.9, 1.7,
        "Reference\nBAM-1020\n\n" + r"PM$_{2.5}$/PM$_{10}$" +
        "\n$U_{rel}$ = 2%\nISO 17025",
        fc="#ffd6d6", lw=1.5, fs=7.5)

    # ------- LoRaWAN Gateway -------
    box(ax, 5.4, 4.6, 1.9, 1.1,
        "LoRaWAN\nGateway\n\nSF7, 125 kHz",
        fc="#ffd9aa", lw=1.5, fs=7.5)

    # ------- Edge Server -------
    box(ax, 8.7, 4.6, 2.2, 1.4,
        "Edge Server\n\nData fusion\nML calibration\nGUM uncertainty",
        fc="#cae5c8", lw=1.5, fs=7.5)

    # ------- Cloud / Dashboard -------
    box(ax, 11.7, 5.5, 2.0, 0.9,
        "Cloud / Dashboard\nMonitoring & alerts",
        fc="#dadada", lw=1.5, fs=7.5)

    # ------- 5 IoT sensor nodes (S1..S5) -------
    sensor_y = 1.3
    sensor_xs = [1.5, 2.7, 3.9, 5.1, 6.3]
    for i, x in enumerate(sensor_xs, start=1):
        box(ax, x, sensor_y, 1.05, 1.55,
            f"S{i}\n\nPMS5003\nBME280\nMPU-6050\n\nIP65",
            fc="#cfe0ff", lw=1.3, fs=6.5, fw="normal")

    # ------- Connections -------
    # Reference -> Gateway
    arrow(ax, 2.65, 4.4, 4.45, 4.55, label="RS-485", lw=1.4,
          label_offset=(0, 0.2))
    # Gateway -> Edge
    arrow(ax, 6.35, 4.6, 7.6, 4.6, label="Ethernet", lw=1.4,
          label_offset=(0, 0.2))
    # Edge -> Cloud
    arrow(ax, 9.1, 5.3, 11.0, 5.4, label="MQTT/TLS", lw=1.4,
          label_offset=(0.3, 0.0))

    # IoT sensors -> Gateway (wireless, dashed blue)
    for x in sensor_xs:
        arrow(ax, x, 2.05, 5.4, 4.05, dashed=True, color="#3a72bf", lw=1.0)
    ax.text(5.4, 3.5, "LoRaWAN", ha="center", fontsize=7,
            color="#3a72bf", style="italic")

    # Sampling annotation
    ax.text(3.9, 0.55,
            r"Sampling: 15 min $\rightarrow$ 96 samples/day",
            ha="center", fontsize=7, color="#444")

    plt.tight_layout()
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
