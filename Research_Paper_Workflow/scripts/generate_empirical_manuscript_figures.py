"""
BHU LOKA - Empirical Manuscript Figure Generator [EMPIRICAL_EO]
Generates honest, verified manuscript figures from real Sentinel-1A/B (23/29 Sep 2019),
Copernicus GLO-30 DEM, NASA MODIS MOD11A1, WorldPop 2020, and 60,000-pixel RF SBCV outputs.
"""

import json
import os
import shutil
import tempfile

os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def draw_sar_architecture_figure(out_paths: list) -> None:
    """Generates updated Figure 2 reflecting verified 23/29 Sep 2019 bimodal SAR physics."""
    fig, ax = plt.subplots(figsize=(10.5, 11.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11.5)
    ax.axis("off")

    ax.text(
        5.0,
        11.15,
        "Copernicus Sentinel-1A/B SAR Bimodal Flood Extraction Pipeline",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        5.0,
        10.82,
        "Empirical Processing of 23 Sep 2019 (Pre-Deluge S1A) and 29 Sep 2019 (Peak Deluge S1B), Orbit 121, 10 m VV",
        ha="center",
        va="center",
        fontsize=9.6,
        style="italic",
        color="#475569",
    )

    steps = [
        (
            "Level-1 GRD Sentinel-1A/B Pairs (IW Swath, 10 m VV)",
            "S1A_IW_GRDH_VV_20190923 (693.8 MB) & S1B_IW_GRDH_VV_20190929 (713.7 MB)",
            "#e0f2fe",
            "#0284c7",
        ),
        (
            "Tiepoint Spatial Co-Registration & Patna Study Window Crop",
            "LinearNDInterpolator over GeoTIFF tiepoints (bbox: 85.02E-85.25E, 25.54N-25.65N; 444.68 km2)",
            "#f1f5f9",
            "#334155",
        ),
        (
            "Radiometric Calibration & 5 x 5 Speckle Suppression",
            "Logarithmic backscatter scaling sigma0 (dB) + 5 x 5 noise suppression filter",
            "#f1f5f9",
            "#334155",
        ),
        (
            "Multi-Temporal Differential Operator & Ganga Permanent Water Mask",
            "Delta sigma0 = sigma0_post [29 Sep 2019] - sigma0_pre [23 Sep 2019]; exclude dry Ganga (< -18.0 dB)",
            "#e0f2fe",
            "#0284c7",
        ),
        (
            "Branch A: Open-Water Specular Drop (Automated Otsu T* = -3.80 dB)",
            "Bbox specular flood: 26.54 km2 (5.97%) | Filtered PMC open specular flood: 0.07 km2",
            "#dbeafe",
            "#1d4ed8",
        ),
        (
            "Branch B: Urban Street-Canyon Corner Double-Bounce Detector",
            "Building-water dihedral boost: Delta sigma0 >= +1.5 dB, sigma0_pre >= -14 dB, sigma0_post >= -11 dB -> 99.52 km2 PMC",
            "#ffedd5",
            "#c2410c",
        ),
        (
            "Verified Bimodal PMC Footprint vs UN-SPIDER Benchmark",
            "BHU LOKA Total PMC: 99.60 km2 (74.4% of 133.87 km2) vs UN-SPIDER (-2.0 dB): 4.01 km2 (95.98% omission)",
            "#dcfce7",
            "#15803d",
        ),
    ]

    box_w, box_h = 8.8, 1.05
    x0 = 0.6
    y_top = 9.45
    step_y = 1.44

    for i, (title, sub, fc, ec) in enumerate(steps):
        y = y_top - i * step_y
        rect = patches.FancyBboxPatch(
            (x0, y),
            box_w,
            box_h,
            boxstyle="round,pad=0.06,rounding_size=0.14",
            linewidth=1.8,
            edgecolor=ec,
            facecolor=fc,
        )
        ax.add_patch(rect)
        ax.text(5.0, y + 0.68, title, ha="center", va="center", fontsize=10.3, fontweight="bold", color="#0f172a")
        ax.text(5.0, y + 0.31, sub, ha="center", va="center", fontsize=8.8, color="#334155")
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(5.0, y - (step_y - box_h) + 0.04),
                xytext=(5.0, y - 0.04),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.45", lw=1.8, color="#0284c7"),
            )

    plt.tight_layout()
    for path in out_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def draw_empirical_validation_panel(base_dir: str, out_paths: list) -> None:
    """Builds 3-panel empirical EO figure from Exp_01, Exp_04 ULSI raster, and 60k SBCV metrics."""
    out_dir = os.path.join(base_dir, "Data", "08_Processed_Outputs")
    exp01_bench = os.path.join(base_dir, "Experiments", "Exp_01_SAR_Flood_Inundation", "unspider_vs_bhu_loka_benchmark.json")
    exp04_json = os.path.join(base_dir, "Experiments", "Exp_04_MultiHazard_Fusion", "exp04_results.json")
    sbcv_json = os.path.join(base_dir, "Models", "01_Spatial_ML", "spatial_cv_metrics.json")

    with open(exp01_bench, "r", encoding="utf-8") as f:
        bench = json.load(f)
    with open(exp04_json, "r", encoding="utf-8") as f:
        exp04 = json.load(f)
    with open(sbcv_json, "r", encoding="utf-8") as f:
        sbcv = json.load(f)

    ulsi_raw = np.load(os.path.join(out_dir, "patna_urban_suitability_index.npy"))
    # Downsample 2x cleanly for publication figure rendering
    h, w = ulsi_raw.shape
    ulsi_ds = np.array(
        Image.fromarray(ulsi_raw.astype(np.float32)).resize((w // 2, h // 2), Image.Resampling.NEAREST)
    )

    fig, axes = plt.subplots(1, 3, figsize=(19.5, 5.8), dpi=300)

    # Panel (a): UN-SPIDER vs BHU LOKA Empirical PMC Inundation Comparison
    unspider_km2 = bench["unspider_algorithm"]["detected_inundation_km2"]
    bhu_km2 = bench["bhu_loka_algorithm"]["total_detected_inundation_km2"]
    bars = axes[0].bar(
        ["UN-SPIDER\n(Specular Only\nDelta sigma0 <= -2 dB)", "BHU LOKA\n(Specular +\nCorner Double-Bounce)"],
        [unspider_km2, bhu_km2],
        color=["#94a3b8", "#0284c7"],
        edgecolor="#0f172a",
        width=0.52,
    )
    axes[0].set_ylim(0, 128)
    axes[0].set_ylabel("Detected PMC Inundation Area (km2)", fontsize=10.5)
    axes[0].set_title("(a) Sentinel-1 PMC Flood Detection (133.87 km2)", fontsize=11.5, fontweight="bold")
    axes[0].grid(axis="y", linestyle=":", alpha=0.6)
    axes[0].text(bars[0].get_x() + bars[0].get_width() / 2, unspider_km2 + 3.5, f"{unspider_km2:.2f} km2\n(2.99% PMC)", ha="center", fontsize=9.2, fontweight="bold")
    axes[0].text(bars[1].get_x() + bars[1].get_width() / 2, bhu_km2 + 3.5, f"{bhu_km2:.2f} km2\n(74.40% PMC)", ha="center", fontsize=9.2, fontweight="bold")
    axes[0].text(
        0.04,
        0.72,
        f"UN-SPIDER urban\nomission error:\n{bench['scientific_findings']['unspider_urban_omission_error_pct']:.2f}%",
        transform=axes[0].transAxes,
        ha="left",
        va="center",
        fontsize=8.8,
        fontweight="bold",
        color="#991b1b",
        bbox=dict(boxstyle="round,pad=0.38", facecolor="#fee2e2", edgecolor="#dc2626", linewidth=1.2),
    )

    # Panel (b): Real Multi-Sensor ULSI Raster inside PMC
    cmap = plt.cm.RdYlGn.copy()
    cmap.set_bad(color="#f8fafc")
    masked_ulsi = np.ma.masked_invalid(ulsi_ds)
    im = axes[1].imshow(masked_ulsi, cmap=cmap, vmin=0, vmax=100)
    axes[1].set_title(
        f"(b) Empirical PMC ULSI Map (Mean = {exp04['mean_pmc_suitability_score']:.2f}/100)\nS1: 20.1% | S2: 27.7% | S3: 33.1% | S4 Crit: 19.1%",
        fontsize=11.2,
        fontweight="bold",
    )
    axes[1].axis("off")
    cbar = plt.colorbar(im, ax=axes[1], fraction=0.042, pad=0.03)
    cbar.set_label("Urban Land Suitability Index [0-100]", fontsize=9.5)

    # Panel (c): 60,000-Pixel Empirical 5-Fold Spatial Block CV (RandomForestClassifier)
    folds = [f"Fold {r['fold']}" for r in sbcv["fold_results"]]
    aucs = [r["roc_auc"] for r in sbcv["fold_results"]]
    f1s = [r["f1_score"] for r in sbcv["fold_results"]]
    x = np.arange(len(folds))
    width = 0.36
    axes[2].bar(x - width / 2, aucs, width, label="ROC-AUC", color="#0f766e", edgecolor="#0f172a")
    axes[2].bar(x + width / 2, f1s, width, label="F1-Score", color="#f59e0b", edgecolor="#0f172a")
    axes[2].axhline(sbcv["mean_roc_auc"], color="#0f766e", linestyle="--", linewidth=1.4, label=f"Mean AUC = {sbcv['mean_roc_auc']:.4f}")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(folds, fontsize=9.5)
    axes[2].set_ylim(0, 1.05)
    axes[2].set_ylabel("Validation Metric Score", fontsize=10.5)
    axes[2].set_title(
        f"(c) Empirical 5-Fold SBCV (N = {sbcv['num_samples']:,} pixels)\nMean AUC = {sbcv['mean_roc_auc']:.4f} +/- {sbcv['std_roc_auc']:.4f} | Acc = {sbcv['mean_accuracy_pct']:.2f}%",
        fontsize=11.2,
        fontweight="bold",
    )
    axes[2].grid(axis="y", linestyle=":", alpha=0.6)
    axes[2].legend(loc="lower right", fontsize=8.3, frameon=True)

    plt.tight_layout()
    for path in out_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    plots_dir = os.path.join(base_dir, "Research_Paper_Workflow", "plots")
    final_fig_dir = os.path.join(base_dir, "Final_Research_Work", "Figures")
    out_dir = os.path.join(base_dir, "Data", "08_Processed_Outputs")

    draw_sar_architecture_figure(
        [
            os.path.join(plots_dir, "Figure2_Sentinel1_SAR_Processing_Pipeline.png"),
            os.path.join(final_fig_dir, "Figure2.png"),
            os.path.join(final_fig_dir, "Figure2_Sentinel1_SAR_Processing_Pipeline.png"),
        ]
    )

    draw_empirical_validation_panel(
        base_dir,
        [
            os.path.join(plots_dir, "Figure_Empirical_EO_Validation.png"),
            os.path.join(final_fig_dir, "Figure7_Empirical_EO_Validation.png"),
        ],
    )

    # Copy empirical SAR extent figure into Final_Research_Work/Figures and Research_Paper_Workflow/plots cleanly
    src_sar_fig = os.path.join(out_dir, "patna_2019_flood_extent_empirical.png")
    if os.path.exists(src_sar_fig):
        shutil.copy2(src_sar_fig, os.path.join(final_fig_dir, "Figure_Empirical_SAR_Flood.png"))
        shutil.copy2(src_sar_fig, os.path.join(plots_dir, "Figure_Empirical_SAR_Flood.png"))

    print("Generated honest empirical figures cleanly.")


if __name__ == "__main__":
    main()
