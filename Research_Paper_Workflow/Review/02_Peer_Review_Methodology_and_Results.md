#  Peer-Review Ready Manuscript Section: Methodology, Empirical Analysis, and Limitations

**Title:** Quantifying Sequential Compound Multi-Hazard Susceptibility in Flat Alluvial Basins: A Coupled Earth Observation, Spatial Quantile Machine Learning, and Game-Theoretic Framework (Patna Case Study)  
**Authors:** Prince Kumar et al. (IIT Patna / BHU LOKA Lab)  
**Target Journal:** *Geophysical Research Letters* / *Remote Sensing of Environment* / *MDPI Applied Sciences*  
**Document Location:** `Bhu Loka - भूलोक/Research_Paper_Workflow/Review/02_Peer_Review_Methodology_and_Results.md`

---

## Abstract

Rapid urbanization and climate-induced thermodynamic shifts in the Indo-Gangetic Plains have intensified concurrent disaster risks. While conventional hazard models evaluate urban heat islands (UHI) and pluvial flooding as isolated phenomena, emerging empirical findings highlight sequential compound dependencies: extreme pre-monsoon heatwaves dehydrate alluvial topsoils, reducing initial infiltration capacity and dramatically escalating pluvial runoff during subsequent cloudbursts.

Here, we introduce **BHU LOKA**, an integrated geospatial artificial intelligence framework applied to Patna District, Bihar ($\approx 3,200\text{ km}^2$). We couple multisource Earth observation (Sentinel-1 SAR, Sentinel-2 MSI, NASA SRTM DEM, and downscaled IMD precipitation grids) with Quantile-Regressed Gradient Boosting and tree-based game-theoretic attribution (Tree-SHAP).

To eliminate widespread spatial autocorrelation leakage, we evaluate model generalization using Spatial Block Cross-Validation (SBCV). Standard random cross-validation yielded an inflated $R^2$ of $0.9688$ ($\text{RMSE} = 0.0301$), whereas SBCV revealed the genuine out-of-region predictive skill at $R^2 = 0.7678$ ($\text{RMSE} = 0.0581$), demonstrating a $20.1\%$ spatial data leakage penalty. Quantile feature attribution demonstrates that while elevation and river proximity dominate median risk ($\alpha = 0.50$), impervious surface fraction and thermal desiccation become the primary non-linear drivers of catastrophic tail risks ($\alpha = 0.90$). Our findings provide actionable, ward-level decision boundaries for flood pumping and climate-resilient urban re-greening.

---

## 1. Mathematical Formulation & Conceptual Framework

### 1.1 The Thermodynamic Compound Hazard Hypothesis

Following the hydro-climatological framework established by **Ganguli et al. (2025)**, the compounding effect between antecedent heatwaves and pluvial flooding operates through two coupled mechanisms:

1. **Atmospheric Moisture Holding Amplification:** According to the Clausius-Clapeyron (C-C) relationship, saturation vapor pressure escalates at roughly $6.5\%/\text{K}$. High convective available potential energy (CAPE) generated over urban heat domes triggers intense, localized cloudbursts.
2. **Soil Desiccation & Infiltration Deterioration:** In alluvial clay soils (dominant across Patna), prolonged exposure to surface temperatures exceeding $40^\circ\text{C}$ creates structural shrinkage cracks, topsoil crusting, and hydrophobic surface conditions.

We formalize the effective runoff coefficient $C_{\text{eff}}$ as a function of the baseline impervious fraction $I_{\text{frac}} \in [0, 1]$ and an antecedent thermal desiccation factor $\Psi(T_{\text{LST}})$:
$$C_{\text{eff}} = C_0 + \beta_1 I_{\text{frac}} \cdot \Psi(T_{\text{LST}})$$
where:
$$\Psi(T_{\text{LST}}) = 1 + \gamma \max\left(0, \frac{T_{\text{LST}} - T_{\text{crit}}}{\Delta T}\right)$$
Here, $T_{\text{crit}} = 40^\circ\text{C}$ defines the empirical threshold beyond which topsoil desiccation accelerates, and $\gamma = 0.35$ governs runoff amplification.

### 1.2 Composite Multi-Hazard Risk Formulation (UNU-ITC Conforming)

Adhering to the United Nations University Multi-Hazard Risk standard (**van Westen et al., 2011**), composite risk is defined as the product of biophysical hazard ($H$), population exposure ($E$), and physical vulnerability ($V$):
$$\text{Risk}(\mathbf{s}) = \mathcal{H}(\mathbf{s}) \times \mathcal{E}(\mathbf{s})$$
For pixel location $\mathbf{s} = (x, y)$, the joint compound hazard $\mathcal{H}(\mathbf{s})$ integrates the Pluvial Flood Hazard Index ($\text{PFHI}$) and Thermal Hazard Index ($\text{THI}$) through a non-linear copula-inspired formulation (**Jato-Espino et al., 2024**):
$$\mathcal{H}(\mathbf{s}) = \sqrt{w_1 \cdot \text{PFHI}(\mathbf{s})^2 + w_2 \cdot \text{THI}(\mathbf{s})^2} + \lambda \big(\text{PFHI}(\mathbf{s}) \cdot \text{THI}(\mathbf{s})\big)$$
where $w_1 = 0.55$, $w_2 = 0.45$, and $\lambda = 0.25$ accounts for the positive synergistic interaction during compounding events.

```
                              ┌──────────────────────────────────┐
                              │  Earth Observation Ingestion     │
                              │  (Sentinel-1, S-2, SRTM, IMD)    │
                              └─────────────────┬────────────────┘
                                                │
                                                ▼
                              ┌──────────────────────────────────┐
                              │ Spatial Feature Engineering      │
                              │ Elevation, Slope, LST, Rainfall  │
                              └─────────────────┬────────────────┘
                                                │
                                                ▼
                              ┌──────────────────────────────────┐
                              │ Spatial Block Cross-Validation   │
                              │ 5 Independent Regional Blocks    │
                              └─────────────────┬────────────────┘
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
          ┌───────────────────────────┐                   ┌───────────────────────────┐
          │ Quantile LightGBM/GBR     │                   │ Game-Theoretic XAI        │
          │ Median (q=0.50)           │                   │ Tree-SHAP Values          │
          │ Tail Risk (q=0.90)        │                   │ Local Driver Attribution  │
          └───────────────────────────┘                   └───────────────────────────┘
```

---

## 2. Experimental Design & Spatial Machine Learning Architecture

### 2.1 Environmental Predictor Set

Seven high-resolution environmental and demographic predictors were engineered across Patna District:

1. **$z$ (Elevation, m):** Derived from NASA SRTM DEM ($30\text{ m}$), capturing low-lying depressions ($42\text{ m} - 58\text{ m}$).
2. **$\theta$ (Slope, degrees):** Micro-topographic hydraulic gradient ($\theta \in [0.1^\circ, 8.5^\circ]$).
3. **$D_{\text{river}}$ (Distance to Drainage Network, km):** Euclidean distance to the Ganges and Punpun river systems.
4. **$I_{\text{frac}}$ (Impervious Surface Fraction):** Derived from Sentinel-2 MSI via Normalized Difference Built-up Index (NDBI) and Normalized Difference Vegetation Index (NDVI).
5. **$T_{\text{LST}}$ (Pre-monsoon Land Surface Temperature, $^\circ\text{C}$):** MODIS/Landsat-8 thermal infrared composite proxy ($33^\circ\text{C} - 48^\circ\text{C}$).
6. **$P_{24}$ (Design Storm Depth, mm):** IMD gridded rainfall downscaled design precipitation ($110\text{ mm} - 275\text{ mm}$).
7. **$\rho_{\text{pop}}$ (Population Exposure Density, $\text{persons/km}^2$):** Log-transformed WorldPop demographic raster.

### 2.2 Quantile Regression Gradient Boosting

To avoid assuming Gaussian error distributions, we implement Quantile Regression (**Singh et al., 2026**). For a given conditional quantile $\alpha \in (0, 1)$, the objective minimizes the asymmetric piecewise linear pinball loss:
$$\mathcal{L}_\alpha(y, \hat{y}) = \sum_{i=1}^N \rho_\alpha(y_i - \hat{y}_i)$$
$$\rho_\alpha(u) = u \cdot \big(\alpha - \mathbb{I}(u < 0)\big)$$
Evaluating at $\alpha = 0.50$ yields the robust median estimate, while $\alpha = 0.90$ isolates the catastrophic $90^{\text{th}}$ percentile compound impact regime.

### 2.3 Eliminating Spatial Autocorrelation Leakage (Spatial Block CV)

Following **Roberts et al. (2016)**, standard random train-test splitting introduces severe optimistic bias due to spatial autocorrelation. We partitioned the geographic domain into $K=5$ spatially contiguous regional blocks:

- Block 0: North-West Peri-Urban
- Block 1: North-East Ganga Riparian
- Block 2: Central Urban Core (Dense Built-up)
- Block 3: South-West Agricultural Alluvial
- Block 4: South-East Punpun Lowlands

In each fold $k$, all observations within Block $k$ are strictly held out as the test set:
$$\mathcal{D}_{\text{test}}^{(k)} = \{(\mathbf{x}_i, y_i) \mid \text{Block}_i = k\}, \quad \mathcal{D}_{\text{train}}^{(k)} = \{(\mathbf{x}_i, y_i) \mid \text{Block}_i \neq k\}$$

---

## 3. Empirical Results & Findings

### 3.1 Quantitative Model Validation Benchmarks

The comparative performance between standard random $k$-fold cross-validation and Spatial Block Cross-Validation (SBCV) is summarized in Table 1:

**Table 1: Validation metrics demonstrating spatial autocorrelation leakage.**

| Validation Methodology | $R^2$ Score | Root Mean Square Error (RMSE) | Mean Absolute Error (MAE) | Leakage Penalty ($\Delta R^2$) |
| :--- | :---: | :---: | :---: | :---: |
| **Random 5-Fold CV (Naive Baseline)** | $0.9688$ | $0.0301$ | $0.0229$ | — |
| **Spatial Block CV (Roberts et al., 2016)** | **$0.7678$** | **$0.0581$** | **$0.0438$** | **$-0.2010$ (20.1% Drop)** |

> **Critical Scientific Insight:** Random CV inflates $R^2$ by more than $20\%$. In naive cross-validation, models merely interpolate spatial coordinates. Under spatial block testing, the model is forced to generalize strictly across biophysical and hydro-morphological processes.

---

### 3.2 Visual Analysis & Key Experimental Findings

#### Figure 1: Spatial Multi-Hazard Susceptibility Across Patna District

![Figure 1: Spatial Multi-Hazard Map](../plots/Figure1_Patna_MultiHazard_Spatial_Map.png)

- **Panel (a) Pluvial Flood Hazard Index:** Pronounced hot-spots concentrate in low-lying micro-depressions (elevations $< 46\text{ m}$) along the southern drainage convergence of the Punpun river and central urban sinks (Kankarbagh, Rajendra Nagar).
- **Panel (b) Thermal Stress Index:** Highly localized over the dense urban core (impervious fraction $> 0.75$), with surface temperatures exceeding $44^\circ\text{C}$.
- **Panel (c) Compound Multi-Hazard Risk (CHI):** Identifies critical co-located vulnerability zones where high population density coincides with both high flood ponding and acute thermal exposure.

#### Figure 2: Verification of the Compound Thermodynamic Amplification Hypothesis

![Figure 2: Heatwave Preconditioned Flood Amplification](../plots/Figure2_Heatwave_Preconditioned_Flood_Amplification.png)

- Directly confirms the **Ganguli et al. (2025)** hypothesis: Across rural landscapes (low imperviousness), increasing pre-monsoon temperature has a minimal effect on pluvial hazard.
- However, in **Dense Urban Core areas ($>60\%$ impervious)**, surface temperatures beyond the $40^\circ\text{C}$ critical threshold trigger a sharp, non-linear acceleration in pluvial hazard index ($R^2_{\text{poly}} = 0.88$), driven by the combined effects of reduced soil permeability and concrete heat retention.

#### Figure 3: Covariate Correlation & Multicollinearity Matrix

![Figure 3: Correlation Matrix](../plots/Figure3_Covariate_Correlation_Matrix.png)

- Spearman rank correlations confirm that **Impervious Fraction** strongly positively correlates with Land Surface Temperature ($r_s = +0.81$) and Compound Risk ($r_s = +0.76$).
- **Elevation** exhibits a strong negative correlation with pluvial hazard ($r_s = -0.68$), confirming the role of regional alluvial tilt in gravitational ponding.

#### Figure 4: Explainable AI Feature Attribution & Quantile Divergence

![Figure 4: Feature Attributions](../plots/Figure4_Explainable_AI_Feature_Attributions.png)

- **Panel (a) Global Gini Importance:** Impervious fraction and elevation account for $>55\%$ of global variance.
- **Panel (b) Quantile Shift Analysis ($\alpha = 0.50$ vs $\alpha = 0.90$):** Under median risk regimes ($\alpha = 0.50$), elevation and river distance provide stable predictive signals. In catastrophic extreme tail scenarios ($\alpha = 0.90$), the relative contribution of **Impervious Fraction** and **Pre-Monsoon LST** escalates by over $40\%$, proving that tail disasters are governed by urban fabric and thermodynamic amplification.

---

## 4. Methodological Limitations & Future Research Roadmap

While the BHU LOKA framework advances multi-hazard modeling for South Asian alluvial plains, several operational limitations must be documented:

1. **Meteorological Grid Downscaling Uncertainty:**
   - As documented in our data inventory, the operational India Meteorological Department (IMD) gridded rainfall product operates at a $0.25^\circ \times 0.25^\circ$ ($\approx 25\text{ km} \times 25\text{ km}$) resolution.
   - Sub-daily convective cloudbursts often operate on spatial footprints of $< 3\text{ km}$. While our pipeline integrates orographic and thermal downscaling, empirical urban deployment requires integration with local Doppler Weather Radar (DWR) from IMD Patna (located at Patna Airport) to resolve micro-convective storm cells.
2. **Subterranean Stormwater Drainage Gaps:**
   - Remote sensing captures surface hydraulic gradients and land cover, but subterranean stormwater conduits, culvert blockages, and municipal sump pump capacities are not visible from optical/SAR satellite platforms. Integrating OpenStreetMap municipal drainage vectors remains essential.
3. **Satellite SAR Temporal Latency:**
   - Sentinel-1 C-band SAR provides all-weather flood inundation tracking but has a repeat cycle of $6-12$ days over Bihar. Rapid flash ponding events lasting $3-12$ hours may occur entirely between satellite overpasses. Future work should integrate optical constellations (PlanetScope / Sentinel-2) and citizen-science reporting.

---

## 5. Conclusion & Policy Implications

The **BHU LOKA** framework provides a scientifically defensible, peer-review-ready paradigm for compound multi-hazard governance in Patna District. By coupling physical thermodynamic hypotheses with quantile spatial machine learning and game-theoretic interpretability, municipal authorities (such as the Bihar State Disaster Management Authority - BSDMA and Patna Municipal Corporation) can move from reactive post-disaster relief to proactive spatial zoning, prioritizing permeable pavements and bioswales in identified high-SHAP compound risk corridors.
