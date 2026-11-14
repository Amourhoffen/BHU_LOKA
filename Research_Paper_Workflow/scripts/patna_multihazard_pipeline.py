"""
BHU LOKA (bhuloka) - Hydro-Thermodynamic Simulation Proxy Pipeline [DERIVED_SIMULATION_PROXY]
Title: Spatial Autocorrelation Penalty and Quantile Tail Shift Sensitivity Benchmark (Patna Bounds)
Framework: Coupled Horton/Thermal Desiccation Proxy, Spatial ML (sklearn RF & Quantile GBR), & 5-Block SBCV
Methodological Foundation:
  - Ganguli et al. (2025, GRL): Heatwave-preconditioned pluvial flood amplification
  - Singh et al. (2026, Land): Quantile gradient boosting & tail-risk feature shift
  - Roberts et al. (2017, Ecography): Spatial Block Cross-Validation against spatial leakage
  - Jato-Espino et al. (2025, IJDRR): Compact multi-hazard metric construction
  - Pedregosa et al. (2011, JMLR): scikit-learn RandomForestRegressor & GradientBoostingRegressor
"""

import json
import os
import shutil
import tempfile

# Ensure matplotlib uses a writable temp cache directory on Windows
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold

# Fixed random seed for reproducible sensitivity analysis
SEED = 42
np.random.seed(SEED)


def generate_patna_spatial_grid(n_samples: int = 3200) -> pd.DataFrame:
    """
    [DERIVED_SIMULATION_PROXY]
    Synthesizes N=3,200 geo-located simulation units across Patna bounding coordinates:
      Latitude: 25.30N to 25.70N | Longitude: 84.85E to 85.35E
      Seven biophysical & exposure covariates derived from Patna calibrated regimes:
        Elevation_m, Slope_deg, Dist_River_km, Impervious_Frac,
        LST_Celsius, Rainfall_mm, Pop_Density
    """
    lats = np.random.uniform(25.30, 25.70, n_samples)
    lons = np.random.uniform(84.85, 85.35, n_samples)

    # Distance to Ganges (northern channel ~25.65N) and Punpun (southern perimeter ~25.40N)
    dist_ganges_km = np.clip(np.abs(lats - 25.65) * 111.0 + np.random.normal(0, 0.5, n_samples), 0.1, 40.0)
    dist_punpun_km = np.clip(np.abs(lats - 25.40) * 111.0 + np.random.normal(0, 0.8, n_samples), 0.2, 35.0)
    min_dist_river = np.minimum(dist_ganges_km, dist_punpun_km)

    # Elevation gradient (42m to 58m a.m.s.l.)
    elevation_m = 54.0 - (lats - 25.30) * 8.0 - (lons - 84.85) * 6.0 + np.random.normal(0, 1.2, n_samples)
    elevation_m = np.clip(elevation_m, 42.0, 58.0)

    # Micro-topographic slope (degrees)
    slope_deg = np.clip(np.abs(np.random.exponential(1.1, n_samples)), 0.1, 8.5)

    # Radial distance from Patna Urban Core (~25.61N, 85.14E)
    dist_to_urban_center = np.sqrt(((lats - 25.61) * 111.0) ** 2 + ((lons - 85.14) * 102.0) ** 2)

    # Urban impervious surface fraction [0.04, 0.94]
    impervious_frac = np.clip(
        0.88 * np.exp(-dist_to_urban_center / 9.0) + np.random.normal(0.08, 0.04, n_samples),
        0.04,
        0.94,
    )

    # Pre-monsoon Land Surface Temperature (LST, Celsius)
    lst_base = 36.5 + 9.5 * impervious_frac - 1.2 * np.log1p(min_dist_river) + np.random.normal(0, 0.9, n_samples)
    lst_celsius = np.clip(lst_base, 33.0, 48.0)

    # Convective design storm precipitation proxy (mm)
    rainfall_mm = (
        160.0
        + 35.0 * np.sin((lons - 84.85) * 8.0)
        + 1.2 * (lst_celsius - 38.0)
        + np.random.normal(0, 12.0, n_samples)
    )
    rainfall_mm = np.clip(rainfall_mm, 110.0, 275.0)

    # Log-normal population density proxy (persons/km^2)
    pop_density = np.exp(np.clip(9.8 - 0.22 * dist_to_urban_center + np.random.normal(0, 0.4, n_samples), 4.5, 11.2))

    # Coupled thermal desiccation factor above 40.0 C threshold (Ganguli et al., 2025 mechanism)
    soil_desiccation_factor = 1.0 + 0.35 * np.maximum(0.0, (lst_celsius - 40.0) / 5.0)

    # Effective runoff coefficient C_runoff
    c_runoff = np.clip(0.20 + 0.65 * impervious_frac * soil_desiccation_factor, 0.15, 0.96)

    # Pluvial Flood Hazard Index (PFHI)
    pluvial_hazard = (rainfall_mm / 200.0) * c_runoff * (1.0 / (elevation_m - 39.0)) * (1.0 / (slope_deg + 0.8)) * 18.0
    pluvial_hazard = np.clip(pluvial_hazard + np.random.normal(0, 0.05, n_samples), 0.05, 1.0)

    # Thermal Hazard Index (THI)
    thermal_hazard = np.clip((lst_celsius - 34.0) / (48.0 - 34.0), 0.0, 1.0)

    # Non-linear coupled compound risk target (CHI)
    joint_hazard = np.sqrt(0.55 * (pluvial_hazard ** 2) + 0.45 * (thermal_hazard ** 2)) + 0.25 * (
        pluvial_hazard * thermal_hazard
    )
    exposure_norm = np.clip((np.log1p(pop_density) - 4.5) / (11.5 - 4.5), 0.0, 1.0)
    compound_risk_index = np.clip(0.65 * joint_hazard + 0.35 * exposure_norm, 0.02, 0.98)

    # Five contiguous spatial blocks centered on Patna bounds (25.50N, 85.10E)
    # 0: NW Danapur Plain | 1: NE Ganga Riparian | 2: Central Urban Core (<7.5 km) | 3: SW Son Plain | 4: SE Punpun Lowlands
    mid_lat, mid_lon = 25.50, 85.10
    spatial_blocks = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        if dist_to_urban_center[i] < 7.5:
            spatial_blocks[i] = 2
        elif lats[i] >= mid_lat and lons[i] < mid_lon:
            spatial_blocks[i] = 0
        elif lats[i] >= mid_lat and lons[i] >= mid_lon:
            spatial_blocks[i] = 1
        elif lats[i] < mid_lat and lons[i] < mid_lon:
            spatial_blocks[i] = 3
        else:
            spatial_blocks[i] = 4

    df = pd.DataFrame(
        {
            "Lat": lats,
            "Lon": lons,
            "Elevation_m": elevation_m,
            "Slope_deg": slope_deg,
            "Dist_River_km": min_dist_river,
            "Impervious_Frac": impervious_frac,
            "LST_Celsius": lst_celsius,
            "Rainfall_mm": rainfall_mm,
            "Pop_Density": pop_density,
            "Runoff_Coeff": c_runoff,
            "Pluvial_Hazard": pluvial_hazard,
            "Thermal_Hazard": thermal_hazard,
            "Compound_Risk_Index": compound_risk_index,
            "Spatial_Block": spatial_blocks,
        }
    )
    return df


def compute_vif(df: pd.DataFrame, features: list) -> dict:
    vifs = {}
    for col in features:
        others = [c for c in features if c != col]
        X_o = np.column_stack([np.ones(len(df)), df[others].values])
        beta, *_ = np.linalg.lstsq(X_o, df[col].values, rcond=None)
        pred = X_o @ beta
        r2 = r2_score(df[col].values, pred)
        vifs[col] = round(float(1.0 / max(1.0 - r2, 1e-9)), 3)
    return vifs


def run_spatial_cross_validation(df: pd.DataFrame, features: list, target_col: str) -> dict:
    """
    Compares:
      1. Standard Random 5-Fold CV (sklearn.ensemble.RandomForestRegressor)
      2. Five-Block Spatial Block Cross-Validation (Roberts et al., 2017)
      3. Full-grid Quantile GradientBoostingRegressor (alpha = 0.50 and alpha = 0.90)
    """
    X = df[features].values
    y = df[target_col].values
    blocks = df["Spatial_Block"].values

    block_names = {
        0: "Block 0: Northwest (Danapur Plain)",
        1: "Block 1: Northeast (Ganga Riparian)",
        2: "Block 2: Central (PMC Urban Core)",
        3: "Block 3: Southwest (Son Alluvial)",
        4: "Block 4: Southeast (Punpun Lowland)",
    }

    # --- Protocol A: Random 5-Fold CV ---
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    random_folds = []
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X), 1):
        rf_random = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=SEED)
        rf_random.fit(X[train_idx], y[train_idx])
        preds = rf_random.predict(X[test_idx])
        random_folds.append(
            {
                "fold": fold_idx,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "r2": round(float(r2_score(y[test_idx], preds)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(y[test_idx], preds))), 4),
                "mae": round(float(mean_absolute_error(y[test_idx], preds)), 4),
            }
        )

    # --- Protocol B: 5-Block Spatial Block Cross-Validation (SBCV) ---
    spatial_folds = []
    for b in sorted(np.unique(blocks)):
        test_mask = blocks == b
        train_mask = ~test_mask
        rf_spatial = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=SEED)
        rf_spatial.fit(X[train_mask], y[train_mask])
        preds = rf_spatial.predict(X[test_mask])
        spatial_folds.append(
            {
                "block": int(b),
                "label": block_names.get(int(b), f"Block {b}"),
                "n_train": int(np.sum(train_mask)),
                "n_test": int(np.sum(test_mask)),
                "r2": round(float(r2_score(y[test_mask], preds)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(y[test_mask], preds))), 4),
                "mae": round(float(mean_absolute_error(y[test_mask], preds)), 4),
            }
        )

    # --- Quantile Gradient Boosting (sklearn.ensemble.GradientBoostingRegressor) ---
    fitted_rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=SEED).fit(X, y)
    q50_model = GradientBoostingRegressor(loss="quantile", alpha=0.50, n_estimators=120, max_depth=6, random_state=SEED)
    q90_model = GradientBoostingRegressor(loss="quantile", alpha=0.90, n_estimators=120, max_depth=6, random_state=SEED)
    q50_model.fit(X, y)
    q90_model.fit(X, y)

    return {
        "Random_CV_Folds": random_folds,
        "Spatial_CV_Blocks": spatial_folds,
        "Random_CV_R2": float(np.mean([f["r2"] for f in random_folds])),
        "Random_CV_RMSE": float(np.mean([f["rmse"] for f in random_folds])),
        "Random_CV_MAE": float(np.mean([f["mae"] for f in random_folds])),
        "Spatial_CV_R2": float(np.mean([f["r2"] for f in spatial_folds])),
        "Spatial_CV_RMSE": float(np.mean([f["rmse"] for f in spatial_folds])),
        "Spatial_CV_MAE": float(np.mean([f["mae"] for f in spatial_folds])),
        "Q50_Model": q50_model,
        "Q90_Model": q90_model,
        "Fitted_RF": fitted_rf,
    }


def generate_publication_figures(df: pd.DataFrame, cv_results: dict, features: list, output_dir: str, final_fig_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(final_fig_dir, exist_ok=True)
    sns.set_theme(style="whitegrid", font="sans-serif")

    # 1. Figure 1: Simulated Spatial Multi-Hazard Surface
    fig, axes = plt.subplots(1, 3, figsize=(21, 6), dpi=300)
    sc1 = axes[0].scatter(df["Lon"], df["Lat"], c=df["Pluvial_Hazard"], cmap="YlGnBu", s=20, alpha=0.85, edgecolors="none")
    axes[0].set_title("(a) Simulated Pluvial Hazard Index (PFHI)", fontsize=12.5, fontweight="bold")
    axes[0].set_xlabel("Longitude (E)", fontsize=11)
    axes[0].set_ylabel("Latitude (N)", fontsize=11)
    plt.colorbar(sc1, ax=axes[0], fraction=0.046, pad=0.04).set_label("Hazard Score [0-1]", fontsize=10)

    sc2 = axes[1].scatter(df["Lon"], df["Lat"], c=df["Thermal_Hazard"], cmap="magma", s=20, alpha=0.85, edgecolors="none")
    axes[1].set_title("(b) Pre-Monsoon Thermal Stress Index (THI)", fontsize=12.5, fontweight="bold")
    axes[1].set_xlabel("Longitude (E)", fontsize=11)
    axes[1].set_ylabel("Latitude (N)", fontsize=11)
    plt.colorbar(sc2, ax=axes[1], fraction=0.046, pad=0.04).set_label("Thermal Score [0-1]", fontsize=10)

    sc3 = axes[2].scatter(df["Lon"], df["Lat"], c=df["Compound_Risk_Index"], cmap="turbo", s=20, alpha=0.85, edgecolors="none")
    axes[2].set_title("(c) Coupled Compound Risk Proxy (CHI)", fontsize=12.5, fontweight="bold")
    axes[2].set_xlabel("Longitude (E)", fontsize=11)
    axes[2].set_ylabel("Latitude (N)", fontsize=11)
    plt.colorbar(sc3, ax=axes[2], fraction=0.046, pad=0.04).set_label("Composite Risk [0-1]", fontsize=10)

    plt.suptitle(
        "BHU LOKA Simulation Proxy (N = 3,200): Spatial Multi-Hazard Sensitivity over Patna Bounds",
        fontsize=14.5,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "Figure1_Patna_MultiHazard_Spatial_Map.png")
    plt.savefig(fig1_path, bbox_inches="tight")
    plt.close()
    shutil.copy2(fig1_path, os.path.join(final_fig_dir, "Figure1.png"))
    shutil.copy2(fig1_path, os.path.join(final_fig_dir, "Figure1_Patna_MultiHazard_Risk_Map.png"))

    # 2. Figure 3 (Architecture): Actual 5-Fold Random vs 5-Block SBCV Partition Comparison
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    rng = np.random.default_rng(SEED)
    rand_folds = rng.integers(0, 5, size=len(df))
    fold_palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    for f in range(5):
        m = rand_folds == f
        ax_l.scatter(df["Lon"][m], df["Lat"][m], c=fold_palette[f], s=10, alpha=0.65, label=f"Fold {f+1}")
    ax_l.set_title(
        f"(a) Random 5-Fold CV (Spatial Leakage)\nMean R2 = {cv_results['Random_CV_R2']:.4f} | RMSE = {cv_results['Random_CV_RMSE']:.4f}",
        fontsize=11.5,
        fontweight="bold",
        color="#991b1b",
    )
    ax_l.set_xlabel("Longitude (E)")
    ax_l.set_ylabel("Latitude (N)")
    ax_l.legend(loc="lower left", fontsize=8.5, ncol=3, frameon=True)

    block_labels = {
        0: "B0: NW Danapur (n=756)",
        1: "B1: NE Riparian (n=598)",
        2: "B2: Central Urban (n=258)",
        3: "B3: SW Son Plain (n=831)",
        4: "B4: SE Punpun (n=757)",
    }
    for b in range(5):
        m = df["Spatial_Block"].values == b
        ax_r.scatter(df["Lon"][m], df["Lat"][m], c=fold_palette[b], s=11, alpha=0.75, label=block_labels[b])
    ax_r.axvline(85.10, color="#1f2937", linestyle="--", linewidth=1.2, alpha=0.7)
    ax_r.axhline(25.50, color="#1f2937", linestyle="--", linewidth=1.2, alpha=0.7)
    ax_r.set_title(
        f"(b) Five-Block Spatial Block CV (Disjoint Holdout)\nMean R2 = {cv_results['Spatial_CV_R2']:.4f} | Central Urban Core R2 = {cv_results['Spatial_CV_Blocks'][2]['r2']:.4f}",
        fontsize=11.5,
        fontweight="bold",
        color="#065f46",
    )
    ax_r.set_xlabel("Longitude (E)")
    ax_r.set_ylabel("Latitude (N)")
    ax_r.legend(loc="lower left", fontsize=8.2, frameon=True)

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "Figure3_Spatial_Block_Cross_Validation_Architecture.png")
    plt.savefig(fig3_path, bbox_inches="tight")
    plt.close()
    shutil.copy2(fig3_path, os.path.join(final_fig_dir, "Figure3.png"))
    shutil.copy2(fig3_path, os.path.join(final_fig_dir, "Figure3_Spatial_Block_Cross_Validation_Architecture.png"))

    # 3. Figure 4: Hydro-Thermodynamic Runoff / Hazard Escalation
    fig, ax = plt.subplots(figsize=(9.5, 6), dpi=300)
    tiers = pd.qcut(df["Impervious_Frac"], q=3, labels=["Rural (<25% Impervious Proxy)", "Peri-Urban Transition", "Dense Urban Core"])
    df_plot = df.copy()
    df_plot["Urban_Tier"] = tiers
    palette = ["#2b83ba", "#fdae61", "#d7191c"]
    sns.scatterplot(data=df_plot, x="LST_Celsius", y="Pluvial_Hazard", hue="Urban_Tier", palette=palette, alpha=0.62, s=26, ax=ax)
    for cat, col in zip(tiers.cat.categories, palette):
        sub = df_plot[df_plot["Urban_Tier"] == cat]
        sns.regplot(data=sub, x="LST_Celsius", y="Pluvial_Hazard", scatter=False, ax=ax, color=col, order=2, line_kws={"linewidth": 2.4})
    ax.axvline(40.0, color="#dc2626", linestyle="--", linewidth=1.6, alpha=0.85, label="Thermal Desiccation Threshold (40.0 C)")
    ax.set_title("Simulated Compound Amplification: Pre-Monsoon LST vs Pluvial Hazard (N = 3,200)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Simulated Pre-Monsoon Land Surface Temperature (C)", fontsize=11)
    ax.set_ylabel("Simulated Pluvial Flood Hazard Index (PFHI)", fontsize=11)
    ax.legend(title="Land Cover Regime", frameon=True, loc="upper left")
    plt.tight_layout()
    fig4_path = os.path.join(output_dir, "Figure2_Heatwave_Preconditioned_Flood_Amplification.png")
    plt.savefig(fig4_path, bbox_inches="tight")
    plt.close()
    shutil.copy2(fig4_path, os.path.join(final_fig_dir, "Figure4.png"))
    shutil.copy2(fig4_path, os.path.join(final_fig_dir, "Figure4_Heatwave_Preconditioned_Runoff_Amplification.png"))

    # 4. Figure 5: Spearman Rank Correlation Matrix
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    corr_cols = features + ["Pluvial_Hazard", "Thermal_Hazard", "Compound_Risk_Index"]
    corr_matrix = df[corr_cols].corr(method="spearman")
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap=cmap,
        vmax=1.0,
        vmin=-1.0,
        center=0,
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )
    ax.set_title("Spearman Rank Correlation Matrix Across Simulated Covariates (N = 3,200)", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    fig5_path = os.path.join(output_dir, "Figure3_Covariate_Correlation_Matrix.png")
    plt.savefig(fig5_path, bbox_inches="tight")
    plt.close()
    shutil.copy2(fig5_path, os.path.join(final_fig_dir, "Figure5.png"))
    shutil.copy2(fig5_path, os.path.join(final_fig_dir, "Figure5_Covariate_Correlation_Matrix.png"))

    # 5. Figure 6: Random Forest Gini & Quantile GBR Feature Importance
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    rf_importances = pd.Series(cv_results["Fitted_RF"].feature_importances_, index=features).sort_values(ascending=True)
    ax1.barh(rf_importances.index, rf_importances.values, color="#2563eb", edgecolor="#1e293b", alpha=0.88)
    ax1.set_title("(a) Mean Impurity Importance (sklearn RandomForest)", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("Relative Gini Importance", fontsize=10.5)
    for i, val in enumerate(rf_importances.values):
        ax1.text(val + 0.008, i, f"{val:.4f}", va="center", fontsize=8.5)
    ax1.set_xlim(0, max(rf_importances.values) * 1.16)

    q50_imp = cv_results["Q50_Model"].feature_importances_
    q90_imp = cv_results["Q90_Model"].feature_importances_
    bar_df = pd.DataFrame(
        {"Feature": features, "Median Risk (q = 0.50)": q50_imp, "Tail Risk (q = 0.90)": q90_imp}
    ).set_index("Feature").reindex(rf_importances.index)
    bar_df.plot(kind="barh", ax=ax2, color=["#0ea5e9", "#dc2626"], edgecolor="#1e293b", width=0.72)
    ax2.set_title("(b) Quantile GBR Feature Importance (q = 0.50 vs q = 0.90)", fontsize=11.5, fontweight="bold")
    ax2.set_xlabel("Gradient Boosting Split Weight", fontsize=10.5)
    ax2.set_ylabel("")
    ax2.legend(title="Quantile Objective", loc="lower right")

    plt.suptitle("Simulation Proxy Feature Contributions: sklearn Random Forest vs Quantile GBR", fontsize=13.5, fontweight="bold", y=0.98)
    plt.tight_layout()
    fig6_path = os.path.join(output_dir, "Figure4_Explainable_AI_Feature_Attributions.png")
    plt.savefig(fig6_path, bbox_inches="tight")
    plt.close()
    shutil.copy2(fig6_path, os.path.join(final_fig_dir, "Figure6.png"))
    shutil.copy2(fig6_path, os.path.join(final_fig_dir, "Figure6_Explainable_AI_Feature_Attributions.png"))
    # Clean obsolete Tree-SHAP misnamed figure alias if present
    old_shap_alias = os.path.join(final_fig_dir, "Figure6_Tree_SHAP_Feature_Attributions.png")
    if os.path.exists(old_shap_alias):
        os.remove(old_shap_alias)


def main() -> None:
    print("=" * 72)
    print("BHU LOKA - Hydro-Thermodynamic Simulation Proxy Pipeline")
    print("=" * 72)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    plots_dir = os.path.join(base_dir, "plots")
    final_fig_dir = os.path.join(os.path.dirname(base_dir), "Final_Research_Work", "Figures")
    os.makedirs(data_dir, exist_ok=True)

    df = generate_patna_spatial_grid(n_samples=3200)
    csv_path = os.path.join(data_dir, "patna_multihazard_dataset.csv")
    df.to_csv(csv_path, index=False)

    features = [
        "Elevation_m",
        "Slope_deg",
        "Dist_River_km",
        "Impervious_Frac",
        "LST_Celsius",
        "Rainfall_mm",
        "Pop_Density",
    ]
    target_col = "Compound_Risk_Index"

    cv_results = run_spatial_cross_validation(df, features, target_col)
    vifs = compute_vif(df, features)
    corr_matrix = df[features + ["Pluvial_Hazard", "Thermal_Hazard", "Compound_Risk_Index"]].corr(method="spearman")

    # Thermal desiccation controlled vs regional statistics
    lst = df["LST_Celsius"].values
    imp = df["Impervious_Frac"].values
    cool_mask = lst < 40.0
    hot_mask = lst >= 40.0
    urb_cool = (imp > 0.60) & cool_mask
    urb_hot = (imp > 0.60) & hot_mask

    mean_c_cool = float(df.loc[cool_mask, "Runoff_Coeff"].mean())
    mean_c_hot = float(df.loc[hot_mask, "Runoff_Coeff"].mean())
    mean_c_urb_cool = float(df.loc[urb_cool, "Runoff_Coeff"].mean())
    mean_c_urb_hot = float(df.loc[urb_hot, "Runoff_Coeff"].mean())

    delta_r2 = cv_results["Spatial_CV_R2"] - cv_results["Random_CV_R2"]
    delta_r2_pct = (delta_r2 / cv_results["Random_CV_R2"]) * 100.0
    delta_rmse = cv_results["Spatial_CV_RMSE"] - cv_results["Random_CV_RMSE"]
    delta_rmse_pct = (delta_rmse / cv_results["Random_CV_RMSE"]) * 100.0
    delta_mae = cv_results["Spatial_CV_MAE"] - cv_results["Random_CV_MAE"]
    delta_mae_pct = (delta_mae / cv_results["Random_CV_MAE"]) * 100.0

    # Save tabular validation metrics
    metrics_df = pd.DataFrame(
        [
            {
                "Validation_Method": "Random 5-Fold CV (Optimistic Baseline)",
                "R2": round(cv_results["Random_CV_R2"], 4),
                "RMSE": round(cv_results["Random_CV_RMSE"], 4),
                "MAE": round(cv_results["Random_CV_MAE"], 4),
            },
            {
                "Validation_Method": "Spatial Block CV 5-Block Mean (Roberts et al. 2017)",
                "R2": round(cv_results["Spatial_CV_R2"], 4),
                "RMSE": round(cv_results["Spatial_CV_RMSE"], 4),
                "MAE": round(cv_results["Spatial_CV_MAE"], 4),
            },
        ]
    )
    metrics_df.to_csv(os.path.join(data_dir, "spatial_model_metrics.csv"), index=False)

    summary_json = {
        "provenance_tier": "DERIVED_SIMULATION_PROXY",
        "n_samples": int(len(df)),
        "model_families": {
            "cv_regressor": "sklearn.ensemble.RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)",
            "quantile_regressor": "sklearn.ensemble.GradientBoostingRegressor(loss='quantile', alpha=[0.50, 0.90], n_estimators=120, max_depth=6, random_state=42)",
        },
        "random_cv_folds": cv_results["Random_CV_Folds"],
        "spatial_cv_blocks": cv_results["Spatial_CV_Blocks"],
        "summary_metrics": {
            "random_mean_r2": round(cv_results["Random_CV_R2"], 4),
            "random_mean_rmse": round(cv_results["Random_CV_RMSE"], 4),
            "random_mean_mae": round(cv_results["Random_CV_MAE"], 4),
            "sbcv_mean_r2": round(cv_results["Spatial_CV_R2"], 4),
            "sbcv_mean_rmse": round(cv_results["Spatial_CV_RMSE"], 4),
            "sbcv_mean_mae": round(cv_results["Spatial_CV_MAE"], 4),
            "delta_r2": round(delta_r2, 4),
            "delta_r2_pct": round(delta_r2_pct, 1),
            "delta_rmse": round(delta_rmse, 4),
            "delta_rmse_pct": round(delta_rmse_pct, 1),
            "delta_mae": round(delta_mae, 4),
            "delta_mae_pct": round(delta_mae_pct, 1),
        },
        "thermal_desiccation_sensitivity": {
            "count_lst_ge_40C": int(np.sum(hot_mask)),
            "count_lst_lt_40C": int(np.sum(cool_mask)),
            "max_lst_celsius": round(float(np.max(lst)), 2),
            "district_mean_c_runoff_lt_40C": round(mean_c_cool, 4),
            "district_mean_c_runoff_ge_40C": round(mean_c_hot, 4),
            "district_rel_increase_pct": round(((mean_c_hot - mean_c_cool) / mean_c_cool) * 100.0, 1),
            "dense_urban_count_lt_40C": int(np.sum(urb_cool)),
            "dense_urban_count_ge_40C": int(np.sum(urb_hot)),
            "dense_urban_mean_c_runoff_lt_40C": round(mean_c_urb_cool, 4),
            "dense_urban_mean_c_runoff_ge_40C": round(mean_c_urb_hot, 4),
            "dense_urban_rel_increase_pct": round(((mean_c_urb_hot - mean_c_urb_cool) / mean_c_urb_cool) * 100.0, 1),
        },
        "vif": vifs,
        "spearman_with_chi": {c: round(float(corr_matrix.loc[c, "Compound_Risk_Index"]), 4) for c in features},
        "spearman_selected_pairs": {
            "LST_vs_Impervious": round(float(corr_matrix.loc["LST_Celsius", "Impervious_Frac"]), 4),
            "Pluvial_vs_Slope": round(float(corr_matrix.loc["Pluvial_Hazard", "Slope_deg"]), 4),
            "Pop_vs_Impervious": round(float(corr_matrix.loc["Pop_Density", "Impervious_Frac"]), 4),
            "LST_vs_Dist_River": round(float(corr_matrix.loc["LST_Celsius", "Dist_River_km"]), 4),
        },
        "feature_importances": {
            "rf_gini": {f: round(float(v), 4) for f, v in zip(features, cv_results["Fitted_RF"].feature_importances_)},
            "quantile_gbr_q50": {f: round(float(v), 4) for f, v in zip(features, cv_results["Q50_Model"].feature_importances_)},
            "quantile_gbr_q90": {f: round(float(v), 4) for f, v in zip(features, cv_results["Q90_Model"].feature_importances_)},
        },
    }

    summary_path = os.path.join(data_dir, "simulation_proxy_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary_json, fh, indent=2)

    generate_publication_figures(df, cv_results, features, plots_dir, final_fig_dir)

    print(f"Random 5-Fold CV : R2={summary_json['summary_metrics']['random_mean_r2']:.4f} | RMSE={summary_json['summary_metrics']['random_mean_rmse']:.4f} | MAE={summary_json['summary_metrics']['random_mean_mae']:.4f}")
    print(f"Spatial Block CV : R2={summary_json['summary_metrics']['sbcv_mean_r2']:.4f} | RMSE={summary_json['summary_metrics']['sbcv_mean_rmse']:.4f} | MAE={summary_json['summary_metrics']['sbcv_mean_mae']:.4f}")
    print(f"SBCV Penalty     : Delta R2={delta_r2:.4f} ({delta_r2_pct:.1f}%) | Central Urban R2={cv_results['Spatial_CV_Blocks'][2]['r2']:.4f}")
    print(f"Saved summary    : {summary_path}")


if __name__ == "__main__":
    main()
