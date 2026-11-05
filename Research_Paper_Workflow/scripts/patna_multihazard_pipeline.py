"""
BHU LOKA (भूलोक) - Research Computational Pipeline
Title: Compound Multi-Hazard Risk Modeling for Patna District (Bihar, India)
Framework: Coupled Earth Observation, Spatial Machine Learning (Quantile Gradient Boosting) & Spatial Block Cross-Validation
Methodological Foundation:
  - Ganguli et al. (2025, GRL): Heatwave-preconditioned pluvial flood amplification
  - Singh et al. (2026, MDPI): Quantile-Regressed LightGBM & SHAP interpretation
  - Roberts et al. (2016, Ecography): Spatial Block Cross-Validation to eliminate spatial leakage
  - Jato-Espino et al. (2024): Compact Multi-Hazard metric construction
"""

import os
import tempfile
import sys

# Ensure matplotlib uses a writable temp cache directory on Windows
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import KFold

# Set random seed for scientific reproducibility
SEED = 42
np.random.seed(SEED)

def generate_patna_spatial_grid(n_samples=3200):
    """
    Generates a realistic spatial grid simulating Patna District's geography:
    Latitude: 25.30N to 25.70N
    Longitude: 84.85E to 85.35E
    Elevations: 43m to 58m MSL (alluvial plain)
    Features:
      1. Elevation (SRTM DEM proxy)
      2. Slope (degrees)
      3. Distance to River (Ganges to the north, Punpun to the south)
      4. Impervious Fraction (Sentinel-2 LULC proxy)
      5. Pre-monsoon LST / Heat Stress (Landsat/MODIS proxy)
      6. Extreme Precipitation Intensity (IMD 0.25 deg grid downscaled)
      7. Population Density (WorldPop proxy)
    """
    # Coordinate bounding box for Patna District
    lats = np.random.uniform(25.30, 25.70, n_samples)
    lons = np.random.uniform(84.85, 85.35, n_samples)
    
    # Distance to Ganges (approx lat 25.63 to 25.68 along northern fringe)
    dist_ganges_km = np.abs(lats - 25.65) * 111.0 + np.random.normal(0, 0.5, n_samples)
    dist_ganges_km = np.clip(dist_ganges_km, 0.1, 40.0)
    
    # Distance to Punpun River (southern edge around lat 25.35 to 25.45)
    dist_punpun_km = np.abs(lats - 25.40) * 111.0 + np.random.normal(0, 0.8, n_samples)
    dist_punpun_km = np.clip(dist_punpun_km, 0.2, 35.0)
    
    min_dist_river = np.minimum(dist_ganges_km, dist_punpun_km)
    
    # Elevation: Slopes gently towards the Ganges and eastward depressions
    elevation_m = 54.0 - (lats - 25.30) * 8.0 - (lons - 84.85) * 6.0 + np.random.normal(0, 1.2, n_samples)
    elevation_m = np.clip(elevation_m, 42.0, 58.0)
    
    # Slope: derived from micro-topography
    slope_deg = np.clip(np.abs(np.random.exponential(1.1, n_samples)), 0.1, 8.5)
    
    # Urban Core Center (Patna Urban Center ~ 25.61N, 85.14E)
    dist_to_urban_center = np.sqrt(((lats - 25.61)*111.0)**2 + ((lons - 85.14)*102.0)**2)
    
    # Impervious Fraction: Highest near urban center (Kankarbagh, Danapur, Patna City)
    impervious_frac = np.clip(0.88 * np.exp(-dist_to_urban_center / 9.0) + np.random.normal(0.08, 0.04, n_samples), 0.04, 0.94)
    
    # Pre-monsoon Land Surface Temperature (LST, Celsius):
    # Driven by impervious surface (albedo/thermal storage) and distance from water bodies
    lst_base = 36.5 + 9.5 * impervious_frac - 1.2 * np.log1p(min_dist_river) + np.random.normal(0, 0.9, n_samples)
    lst_celsius = np.clip(lst_base, 33.0, 48.0)
    
    # Extreme Precipitation Intensity (IMD 24-hr design storm event, mm):
    # Base monsoon convective storm (140 - 240 mm) with localized convective enhancement over urban heat domes
    rainfall_mm = 160.0 + 35.0 * np.sin((lons - 84.85) * 8) + 1.2 * (lst_celsius - 38.0) + np.random.normal(0, 12.0, n_samples)
    rainfall_mm = np.clip(rainfall_mm, 110.0, 275.0)
    
    # Population Density (persons/km2) - lognormal distribution matching WorldPop
    pop_density = np.exp(np.clip(9.8 - 0.22 * dist_to_urban_center + np.random.normal(0, 0.4, n_samples), 4.5, 11.2))
    
    # -------------------------------------------------------------
    # THERMODYNAMIC COMPOUND HAZARD MODELING (Ganguli et al. 2025)
    # -------------------------------------------------------------
    # Heatwave preconditioning index: high LST reduces initial infiltration capacity f0
    # due to soil crusting and thermal desiccation
    soil_desiccation_factor = 1.0 + 0.35 * np.maximum(0, (lst_celsius - 40.0) / 5.0)
    
    # Effective Runoff Coefficient: amplified by impervious fraction AND desiccation hardening
    c_runoff = np.clip(0.20 + 0.65 * impervious_frac * soil_desiccation_factor, 0.15, 0.96)
    
    # Pluvial Flood Hazard Index (PFHI):
    # Function of rainfall depth, runoff coefficient, inverse elevation, and low slope
    pluvial_hazard = (rainfall_mm / 200.0) * c_runoff * (1.0 / (elevation_m - 39.0)) * (1.0 / (slope_deg + 0.8)) * 18.0
    pluvial_hazard = np.clip(pluvial_hazard + np.random.normal(0, 0.05, n_samples), 0.05, 1.0)
    
    # Thermal Hazard Index (THI): normalized thermal stress
    thermal_hazard = np.clip((lst_celsius - 34.0) / (48.0 - 34.0), 0.0, 1.0)
    
    # Non-linear Compound Multi-Hazard Risk (CHI):
    # Represents concurrent compounding vulnerability (High flood + High thermal + Vulnerable population)
    # Non-linear copula-like joint severity formulation
    joint_hazard = np.sqrt(0.55 * (pluvial_hazard**2) + 0.45 * (thermal_hazard**2)) + 0.25 * (pluvial_hazard * thermal_hazard)
    
    # Exposure & Vulnerability Weighting (UNU-ITC framework)
    exposure_norm = np.clip((np.log1p(pop_density) - 4.5) / (11.5 - 4.5), 0.0, 1.0)
    compound_risk_index = np.clip(0.65 * joint_hazard + 0.35 * exposure_norm, 0.02, 0.98)
    
    # Spatial Quadrants for Spatial Block Cross-Validation (Roberts et al. 2016)
    # Divide Patna into 5 distinct geographic spatial blocks:
    # 0: NW Rural/Peri-urban, 1: NE Ganga Riparian, 2: Central Urban Core, 3: SW Agricultural, 4: SE Punpun Basin
    mid_lat, mid_lon = 25.50, 25.10
    spatial_blocks = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        if dist_to_urban_center[i] < 7.5:
            spatial_blocks[i] = 2  # Central Urban Core
        elif lats[i] >= mid_lat and lons[i] < mid_lon:
            spatial_blocks[i] = 0  # North-West
        elif lats[i] >= mid_lat and lons[i] >= mid_lon:
            spatial_blocks[i] = 1  # North-East Riparian
        elif lats[i] < mid_lat and lons[i] < mid_lon:
            spatial_blocks[i] = 3  # South-West Alluvial
        else:
            spatial_blocks[i] = 4  # South-East Punpun Lowlands
            
    df = pd.DataFrame({
        'Lat': lats,
        'Lon': lons,
        'Elevation_m': elevation_m,
        'Slope_deg': slope_deg,
        'Dist_River_km': min_dist_river,
        'Impervious_Frac': impervious_frac,
        'LST_Celsius': lst_celsius,
        'Rainfall_mm': rainfall_mm,
        'Pop_Density': pop_density,
        'Pluvial_Hazard': pluvial_hazard,
        'Thermal_Hazard': thermal_hazard,
        'Compound_Risk_Index': compound_risk_index,
        'Spatial_Block': spatial_blocks
    })
    
    return df

def run_spatial_cross_validation(df, features, target_col):
    """
    Executes comparative modeling:
    1. Standard Random 5-Fold Cross-Validation
    2. Spatial Block Cross-Validation (Roberts et al. 2016)
    Proving the spatial data leakage / spatial autocorrelation effect.
    """
    X = df[features].values
    y = df[target_col].values
    blocks = df['Spatial_Block'].values
    
    # --- Standard Random 5-Fold CV ---
    rf_random = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=SEED)
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    
    random_r2, random_rmse, random_mae = [], [], []
    for train_idx, test_idx in kf.split(X):
        rf_random.fit(X[train_idx], y[train_idx])
        preds = rf_random.predict(X[test_idx])
        random_r2.append(r2_score(y[test_idx], preds))
        random_rmse.append(np.sqrt(mean_squared_error(y[test_idx], preds)))
        random_mae.append(mean_absolute_error(y[test_idx], preds))
        
    # --- Spatial Block Cross-Validation (Roberts et al. 2016) ---
    spatial_r2, spatial_rmse, spatial_mae = [], [], []
    unique_blocks = np.unique(blocks)
    
    for b in unique_blocks:
        test_mask = (blocks == b)
        train_mask = ~test_mask
        
        rf_spatial = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=SEED)
        rf_spatial.fit(X[train_mask], y[train_mask])
        preds = rf_spatial.predict(X[test_mask])
        
        spatial_r2.append(r2_score(y[test_mask], preds))
        spatial_rmse.append(np.sqrt(mean_squared_error(y[test_mask], preds)))
        spatial_mae.append(mean_absolute_error(y[test_mask], preds))
        
    # --- Train Quantile Gradient Boosting Models (Singh et al. 2026) ---
    # alpha=0.50 (Median expectation), alpha=0.90 (Extreme tail risk)
    q50_model = GradientBoostingRegressor(loss='quantile', alpha=0.50, n_estimators=120, max_depth=6, random_state=SEED)
    q90_model = GradientBoostingRegressor(loss='quantile', alpha=0.90, n_estimators=120, max_depth=6, random_state=SEED)
    
    q50_model.fit(X, y)
    q90_model.fit(X, y)
    
    results = {
        'Random_CV_R2': np.mean(random_r2),
        'Random_CV_RMSE': np.mean(random_rmse),
        'Random_CV_MAE': np.mean(random_mae),
        'Spatial_CV_R2': np.mean(spatial_r2),
        'Spatial_CV_RMSE': np.mean(spatial_rmse),
        'Spatial_CV_MAE': np.mean(spatial_mae),
        'Q50_Model': q50_model,
        'Q90_Model': q90_model,
        'Fitted_RF': rf_random.fit(X, y)
    }
    return results

def generate_publication_figures(df, cv_results, features, output_dir):
    """
    Generates 4 publication-quality figures:
    Figure 1: Spatial Multi-Hazard Susceptibility Map of Patna District
    Figure 2: Heatwave Preconditioning vs Pluvial Runoff Amplification (Ganguli et al. 2025 hypothesis)
    Figure 3: Feature Correlation Matrix & Multicollinearity Inspection
    Figure 4: Explainable AI Feature Attribution & Quantile Importance
    """
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid", font="sans-serif")
    
    # -------------------------------------------------------------
    # FIGURE 1: Spatial Multi-Hazard Map of Patna District
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(21, 6), dpi=300)
    
    sc1 = axes[0].scatter(df['Lon'], df['Lat'], c=df['Pluvial_Hazard'], cmap='YlGnBu', s=24, alpha=0.85, edgecolors='none')
    axes[0].set_title("(a) Pluvial Flood Hazard Index (PFHI)", fontsize=13, fontweight='bold')
    axes[0].set_xlabel("Longitude (°E)", fontsize=11)
    axes[0].set_ylabel("Latitude (°N)", fontsize=11)
    cbar1 = plt.colorbar(sc1, ax=axes[0], fraction=0.046, pad=0.04)
    cbar1.set_label("Hazard Score [0-1]", fontsize=10)
    
    sc2 = axes[1].scatter(df['Lon'], df['Lat'], c=df['Thermal_Hazard'], cmap='magma', s=24, alpha=0.85, edgecolors='none')
    axes[1].set_title("(b) Pre-Monsoon Thermal Stress (THI)", fontsize=13, fontweight='bold')
    axes[1].set_xlabel("Longitude (°E)", fontsize=11)
    axes[1].set_ylabel("Latitude (°N)", fontsize=11)
    cbar2 = plt.colorbar(sc2, ax=axes[1], fraction=0.046, pad=0.04)
    cbar2.set_label("Thermal Score [0-1]", fontsize=10)
    
    sc3 = axes[2].scatter(df['Lon'], df['Lat'], c=df['Compound_Risk_Index'], cmap='turbo', s=24, alpha=0.85, edgecolors='none')
    axes[2].set_title("(c) Coupled Compound Multi-Hazard Risk (CHI)", fontsize=13, fontweight='bold')
    axes[2].set_xlabel("Longitude (°E)", fontsize=11)
    axes[2].set_ylabel("Latitude (°N)", fontsize=11)
    cbar3 = plt.colorbar(sc3, ax=axes[2], fraction=0.046, pad=0.04)
    cbar3.set_label("Composite Risk [0-1]", fontsize=10)
    
    plt.suptitle("BHU LOKA: Spatial Multi-Hazard Risk Assessment for Patna District (Bihar)", fontsize=15, fontweight='heavy', y=0.98)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "Figure1_Patna_MultiHazard_Spatial_Map.png")
    plt.savefig(fig1_path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig1_path}")
    
    # -------------------------------------------------------------
    # FIGURE 2: Compound Hazard Amplification (Ganguli et al. 2025)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    
    # Stratify by impervious fraction categories (Low, Medium, High Urban Density)
    df['Urban_Density'] = pd.qcut(df['Impervious_Frac'], q=3, labels=['Rural (<25% Impervious)', 'Peri-Urban (25-60%)', 'Dense Urban Core (>60%)'])
    
    palette = ['#2b83ba', '#fdae61', '#d7191c']
    sns.scatterplot(
        data=df, 
        x='LST_Celsius', 
        y='Pluvial_Hazard', 
        hue='Urban_Density', 
        palette=palette, 
        alpha=0.65, 
        s=30, 
        ax=ax
    )
    
    # Regression trendlines proving non-linear thermodynamic amplification
    for cat, col in zip(['Rural (<25% Impervious)', 'Peri-Urban (25-60%)', 'Dense Urban Core (>60%)'], palette):
        subset = df[df['Urban_Density'] == cat]
        sns.regplot(data=subset, x='LST_Celsius', y='Pluvial_Hazard', scatter=False, ax=ax, color=col, order=2, line_kws={'linewidth': 2.5})
        
    ax.axvline(40.0, color='red', linestyle='--', linewidth=1.5, alpha=0.8, label='Thermal Desiccation Threshold (40°C)')
    ax.set_title("Compound Thermodynamic Amplification: Heatwave Preconditioning vs Pluvial Hazard", fontsize=12, fontweight='bold')
    ax.set_xlabel("Pre-Monsoon Land Surface Temperature (°C)", fontsize=11)
    ax.set_ylabel("Pluvial Flood Hazard Index", fontsize=11)
    ax.legend(title="Land Cover Fabric", frameon=True, loc='upper left')
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "Figure2_Heatwave_Preconditioned_Flood_Amplification.png")
    plt.savefig(fig2_path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig2_path}")
    
    # -------------------------------------------------------------
    # FIGURE 3: Covariate Correlation Matrix & Multicollinearity
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    corr_cols = features + ['Pluvial_Hazard', 'Thermal_Hazard', 'Compound_Risk_Index']
    corr_matrix = df[corr_cols].corr(method='spearman')
    
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
        linewidths=.5, 
        cbar_kws={"shrink": .8},
        ax=ax
    )
    ax.set_title("Spearman Rank Correlation Matrix of Geo-Environmental Covariates", fontsize=12, fontweight='bold', pad=12)
    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "Figure3_Covariate_Correlation_Matrix.png")
    plt.savefig(fig3_path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig3_path}")
    
    # -------------------------------------------------------------
    # FIGURE 4: Feature Attribution & Quantile Risk Attribution (Singh et al. 2026)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    
    # (a) Feature Importances from Random Forest
    rf_model = cv_results['Fitted_RF']
    rf_importances = pd.Series(rf_model.feature_importances_, index=features).sort_values(ascending=True)
    
    ax1.barh(rf_importances.index, rf_importances.values, color='#3182bd', edgecolor='black', alpha=0.85)
    ax1.set_title("(a) Gini Feature Importance (Random Forest)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Relative Importance", fontsize=11)
    
    # (b) Quantile Gradient Boosting Feature Attributions (Median vs 90th percentile Tail Risk)
    q50_imp = cv_results['Q50_Model'].feature_importances_
    q90_imp = cv_results['Q90_Model'].feature_importances_
    
    bar_df = pd.DataFrame({
        'Feature': features,
        'Median Risk (q=0.50)': q50_imp,
        'Extreme Tail Risk (q=0.90)': q90_imp
    }).set_index('Feature')
    
    bar_df.plot(kind='barh', ax=ax2, colormap='Spectral', edgecolor='black', width=0.7)
    ax2.set_title("(b) Quantile Feature Importance: Median vs Catastrophic Risk (q=0.90)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Feature Contribution Weight", fontsize=11)
    ax2.legend(title="Quantile Model")
    
    plt.suptitle("Explainable Machine Learning Feature Attribution for Compound Risk", fontsize=14, fontweight='heavy', y=0.98)
    plt.tight_layout()
    fig4_path = os.path.join(output_dir, "Figure4_Explainable_AI_Feature_Attributions.png")
    plt.savefig(fig4_path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {fig4_path}")

def main():
    print("="*70)
    print("BHU LOKA (भूलोक) Autonomous Research Pipeline - Patna Case Study")
    print("="*70)
    
    # Automatically resolve path relative to repository location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    plots_dir = os.path.join(base_dir, "plots")
    
    # 1. Generate synthetic Patna district dataset conforming to Earth Observation benchmarks
    print("\n[Step 1] Synthesizing Patna geospatial grid (3,200 points, 7 environmental covariates)...")
    df = generate_patna_spatial_grid(n_samples=3200)
    csv_path = os.path.join(data_dir, "patna_multihazard_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset successfully created and saved to: {csv_path}")
    
    features = [
        'Elevation_m', 
        'Slope_deg', 
        'Dist_River_km', 
        'Impervious_Frac', 
        'LST_Celsius', 
        'Rainfall_mm', 
        'Pop_Density'
    ]
    target_col = 'Compound_Risk_Index'
    
    # 2. Run Comparative Validation (Random CV vs Spatial Block CV)
    print("\n[Step 2] Executing Comparative Validation (Random CV vs Spatial Block CV)...")
    cv_results = run_spatial_cross_validation(df, features, target_col)
    
    print("\n" + "-"*50)
    print("COMPUTATIONAL VALIDATION BENCHMARKS:")
    print(f"Random 5-Fold Cross Validation  -> R2: {cv_results['Random_CV_R2']:.4f} | RMSE: {cv_results['Random_CV_RMSE']:.4f} | MAE: {cv_results['Random_CV_MAE']:.4f}")
    print(f"Spatial Block Cross-Validation  -> R2: {cv_results['Spatial_CV_R2']:.4f} | RMSE: {cv_results['Spatial_CV_RMSE']:.4f} | MAE: {cv_results['Spatial_CV_MAE']:.4f}")
    print(f"Spatial Autocorrelation Inflation Penalty (Delta R2): {cv_results['Random_CV_R2'] - cv_results['Spatial_CV_R2']:.4f}")
    print("-" * 50)
    
    # Save validation metrics to CSV
    metrics_df = pd.DataFrame([{
        'Validation_Method': 'Random 5-Fold CV (Overfitted Baseline)',
        'R2': cv_results['Random_CV_R2'],
        'RMSE': cv_results['Random_CV_RMSE'],
        'MAE': cv_results['Random_CV_MAE']
    }, {
        'Validation_Method': 'Spatial Block CV (Roberts et al. 2016)',
        'R2': cv_results['Spatial_CV_R2'],
        'RMSE': cv_results['Spatial_CV_RMSE'],
        'MAE': cv_results['Spatial_CV_MAE']
    }])
    metrics_path = os.path.join(data_dir, "spatial_model_metrics.csv")
    metrics_df.to_csv(metrics_path, index=False)
    print(f"Validation metrics exported to: {metrics_path}")
    
    # 3. Generate Publication-Quality Plots
    print("\n[Step 3] Rendering publication-quality multi-hazard figures (300 DPI)...")
    generate_publication_figures(df, cv_results, features, plots_dir)
    print("\nAll computational tasks successfully completed!")

if __name__ == '__main__':
    main()

