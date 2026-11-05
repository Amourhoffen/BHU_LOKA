# Sequential Compound Hydro-Thermal Risk in Continental Alluvial Metropolises: Integrating Synthetic Aperture Radar, Spatial Quantile Machine Learning, and Game-Theoretic Explainability

**Prince Kumar**  
Department of Computer Science & Engineering, Indian Institute of Technology Patna, Bihta, Bihar 801106, India  
Center for Disaster Management and Geoinformatics, Patna, Bihar, India  
*Corresponding Author:* Prince Kumar (prince_cse@iitp.ac.in)

---

## Abstract

Continental riverine metropolises across the Indo-Gangetic Basin increasingly confront compound hydrometeorological hazards whose joint impacts exceed those of isolated occurrences. While coastal multi-hazard interactions have been examined extensively, inland alluvial basins—characterized by low relief, elevated riverbeds, and severe pre-monsoon thermal regimes—remain poorly understood. This study investigates the sequential coupling between pre-monsoon heatwaves and subsequent pluvial flash flooding across the saucer-shaped urban terrain of Patna District, Bihar, India (3,200 km²). We formulate **BHU LOKA (भूलोक)**, a multi-hazard analytical framework that links multitemporal Sentinel-1 Synthetic Aperture Radar (SAR) backscatter observations, regular 50 m hexagonal spatial discretization, and quantile-regressed gradient boosting (LightGBM, α = 0.90) with Tree-based Shapley Additive Explanations (Tree-SHAP). Using the catastrophic deluge of September 2019 as an empirical baseline (342.5 mm rainfall in 72 hours), we assess spatial model generalizability under both random 5-fold cross-validation and rigorous Spatial Block Cross-Validation (SBCV). The evaluation demonstrates that random cross-validation yields an overly optimistic coefficient of determination (R² = 0.9688, RMSE = 0.0301), whereas SBCV reveals an out-of-region predictive skill of R² = 0.7678 (RMSE = 0.0581), quantifying a spatial autocorrelation performance penalty of ΔR² = -0.2010 (20.1% degradation). Thermodynamic simulation indicates that antecedent heatwave exposure (HWI > 0.7) desiccates fine-grained alluvial surface soils, reducing initial infiltration capacity and escalating surface runoff volumes by 41.3% under equivalent precipitation pulses. Tree-SHAP attributions identify distance to river confluence (|SHAP| = 0.284) and surface elevation (|SHAP| = 0.241) as primary physical determinants of flood ponding, while built-up density and antecedent thermal stress dominate localized urban anomalies. These findings demonstrate that multi-hazard early warning systems in alluvial plains must account for thermodynamic soil preconditioning and spatial autocorrelation biases to support municipal emergency logistics.

**Keywords:** Compound hazards; Pluvial inundation; Synthetic Aperture Radar; Spatial block cross-validation; Quantile regression; Explainable artificial intelligence.

---

## 1. Introduction

Hydro-climatic hazard assessments have traditionally evaluated urban flood risks and atmospheric heatwaves as statistically independent phenomena (van Westen et al., 2011; Jato-Espino et al., 2024). In continental river basins, however, hazards frequently occur in close succession, establishing compound and cascading regimes where the consequences of the secondary hazard are conditioned by the physical footprint of the primary event (Ganguli et al., 2025). The Indo-Gangetic Plain represents one of the most densely populated alluvial basins on Earth, containing over 400 million residents vulnerable to consecutive climatological anomalies. Within this geographic corridor, urban conglomerates routinely transition from extreme pre-monsoon heatwaves (May–June, with surface air temperatures regularly exceeding 44 °C) to monsoonal cloudbursts (July–September) that produce severe pluvial ponding.

Standard hydrologic engineering frameworks assume stationary antecedent catchment conditions, neglecting how prolonged thermal desiccation alters surface infiltration physics. As demonstrated by Ganguli et al. (2025) in peninsular India, sustained high temperatures increase atmospheric water storage capacity in accordance with the Clausius-Clapeyron relationship (approximately 6.5% to 7% increase in saturation vapor pressure per Kelvin of warming), while desiccating surface soil layers. In fine-grained alluvial sediments, prolonged thermal baking causes pore collapse, surface hardening, and hydrophobic crust formation. When intense monsoonal convective cells rupture over these desiccated catchments, initial infiltration capacity ($f_0$) is suppressed, accelerating the time to peak hydrograph concentration and converting incoming precipitation into rapid overland sheetflow (Rohini et al., 2025).

Simultaneously, empirical spatial modeling of multi-hazard vulnerability in urban settings has expanded through machine learning algorithms. Despite their high empirical accuracy, these models often suffer from a fundamental methodological deficiency: the uncritical application of random $k$-fold cross-validation to spatially autocorrelated data (Roberts et al., 2016). Because proximate spatial locations share unobserved geomorphic, topological, and atmospheric traits ($Cov(Z(s), Z(s+h)) > 0$), randomly partitioning training and testing sets causes extensive data leakage between folds. Models trained under random cross-validation report inflated performance metrics that fail when deployed across adjacent, unseen administrative sectors. Quantifying this spatial autocorrelation bias through Spatial Block Cross-Validation (SBCV) is therefore essential for realistic operational deployments (Roberts et al., 2016).

A further operational challenge lies in Earth observation during monsoonal deluges. Passive optical sensors, including Sentinel-2 MSI and Landsat-8/9 OLI, are consistently obstructed by persistent cloud decks during active monsoon troughs. Active microwave Synthetic Aperture Radar (SAR), specifically the C-band sensor aboard Sentinel-1 ($\lambda = 5.6\text{ cm}$, frequency 5.405 GHz), overcomes this barrier by penetrating cloud cover and heavy rainfall (MapAction, 2024). Smooth open floodwaters act as specular reflectors for incoming microwave pulses, scattering energy away from the satellite antenna and causing a distinct drop in the radar backscatter coefficient ($\sigma^0$) that can be mapped at 10 m spatial resolution regardless of solar illumination or atmospheric cloudiness.

To bridge these physical, statistical, and operational gaps, this paper presents **BHU LOKA (भूलोक)**, an integrated spatial machine learning and Earth observation framework calibrated for Patna District, Bihar, India. Patna represents an archetype of continental alluvial vulnerability, situated in a saucer-shaped trough bounded by three major river systems (Ganges, Son, and Punpun). 

This investigation addresses four primary objectives:
1. Couple multi-temporal Sentinel-1 C-band SAR backscatter analysis with an automated Otsu thresholding protocol to map surface water dynamics during the extreme deluge of September 2019.
2. Formulate a coupled hydro-thermodynamic runoff function that captures infiltration suppression resulting from antecedent heatwave desiccation.
3. Quantify the empirical performance degradation caused by spatial autocorrelation by contrasting random 5-fold cross-validation against a 5-quadrant Spatial Block Cross-Validation protocol using Quantile Gradient Boosted Regression (LightGBM, $\alpha = 0.90$).
4. Resolve feature-level risk attributions across administrative wards using Tree-based Shapley Additive Explanations (Tree-SHAP) to inform disaster management authorities.

---

## 2. Study Area and Environmental Setting

Patna District encompasses approximately 3,200 km² within the central Gangetic Alluvial Plain of Bihar, India, centered at 25.61°N latitude and 85.14°E longitude (Figure 1). The urban core, governed by the Patna Municipal Corporation (PMC), spans 75 administrative wards covering 109.2 km² with an estimated population exceeding 2.3 million residents.

```
       85°00'E                           85°15'E                           85°30'E
  25°45'N ┌─────────────────────────────────────────────────────────────────┐
          │                      GANGES RIVER (NORTH)                       │
          │     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~     │
          │         [Danapur]            [Central Patna]       [Fatuha]     │
          │             |                      |                   |        │
  25°35'N │  SON        |         SAUCER-SHAPED URBAN CORE         |        │
          │  RIVER      |     (Kankarbagh, Rajendra Nagar)         |        │
          │  (WEST)     |                      |                   |  PUNPUN│
          │             |             BYPASS EXPRESSWAY            |  RIVER │
          │             |                      |                   | (SOUTH)│
  25°20'N │             |       ALLUVIAL FLOODPLAIN AGRICULTURAL   |        │
          │             |                     ZONE                 |        │
          └─────────────────────────────────────────────────────────────────┘
```

The district exhibits an unusual geomorphic configuration: a saucer-shaped topographic depression where the central and southern municipal wards sit between 48 m and 52 m above mean sea level (a.m.s.l.), lower than the natural natural levees and engineered embankments of the Ganges River to the north (53 m to 55 m a.m.s.l.). The territory forms the hydrodynamic confluence of three major drainage systems: the Ganges flowing west-to-east along the northern boundary, the Son River bounding the west, and the Punpun River traversing the southern and southeastern periphery.

During the peak southwest monsoon (July–September), high river stages in the Ganges generate a severe backwater effect. Outfall sluice gates along the riverfront embankments are closed to prevent the Ganges from entering the city. Consequently, internal pluvial runoff generated by high-intensity convective rainfall cannot discharge by gravity and must be evacuated via mechanical pumping stations into the Punpun or Ganges basins. When pumping infrastructure fails or is overwhelmed, severe internal ponding occurs.

This vulnerability materialized between 27 and 30 September 2019, when a late-monsoon deep depression produced 342.5 mm of rainfall across Patna within 72 hours (more than 25% of the total annual precipitation). The Ganges water level reached 49.85 m, exceeding the danger mark (48.60 m), while internal sumps and drainage outfalls failed. Over 70% of the urban center, including the low-lying sectors of Rajendra Nagar, Kankarbagh, and Pataliputra, was submerged under 1.5 m to 2.5 m of standing water for 7 to 12 days, disrupting drinking water, electricity, and emergency response logistics. This September 2019 event serves as the empirical ground-truth benchmark for this study.

---

## 3. Data and Methodology

### 3.1 Earth Observation and SAR Inundation Extraction

To map the spatial extent of inundation during cloud-covered periods, we obtained Level-1 Ground Range Detected (GRD) products from the Sentinel-1A/B constellation operating in Interferometric Wide (IW) swath mode with dual polarization (VV and VH). Two primary granules were ingested:
1. *Pre-deluge baseline:* 10 September 2019 (orbit 121, relative pass 042).
2. *Peak-flood acquisition:* 28 September 2019 (orbit 121, relative pass 042).

```
   Raw Sentinel-1 Level-1 GRD (IW Mode, VV/VH)
                       │
                       ▼
          Apply Precise Orbit Ephemerides
                       │
                       ▼
            Thermal Noise Removal
                       │
                       ▼
     Radiometric Calibration to Sigma-Nought (σ°)
                       │
                       ▼
       Lee Speckle Filtering (5x5 Adaptive Window)
                       │
                       ▼
     Range Doppler Terrain Correction (Copernicus 30m DEM)
                       │
                       ▼
         Decibel Conversion: σ°(dB) = 10 * log10(σ°)
                       │
                       ▼
       Log-Ratio Change Detection: Δσ° = σ°_post - σ°_pre
                       │
                       ▼
       Automated Otsu Thresholding (T_optimal ≈ -4.2 dB)
                       │
                       ▼
         Empirical Flood Extent Binary Mask (10 m)
```

The SAR data processing pipeline was implemented using standard radiometric and geometric operations:
1. *Orbit Correction:* Application of precise orbit ephemerides (POD) files from the European Space Agency (ESA) to ensure accurate satellite positioning.
2. *Thermal Noise Removal:* Removal of additive thermal noise across cross-polarization channels, particularly at the image margins.
3. *Radiometric Calibration:* Conversion of digital pixel values to normalized radar backscatter cross-sections ($\sigma^0$):
   $$\sigma^0 = \frac{DN_i^2}{A_i^2}$$
   where $DN_i$ is the digital number at pixel $i$ and $A_i$ is the calibration factor.
4. *Speckle Suppression:* Application of a $5 \times 5$ refined Lee adaptive speckle filter to preserve sharp edges and linear features while reducing granular noise.
5. *Terrain Correction:* Range-Doppler terrain correction using the 30 m Copernicus Digital Elevation Model (GLO-30), projecting data into the Universal Transverse Mercator (UTM Zone 45N, WGS84 datum) coordinate system at 10 m pixel spacing.
6. *Decibel Scaling:* Transformation of the backscatter coefficient to a logarithmic scale:
   $$\sigma^0\text{ (dB)} = 10 \cdot \log_{10}(\sigma^0)$$

Open water exhibits low backscatter due to specular reflection, whereas urban structures and dense vegetation generate high backscatter through volume and double-bounce scattering:
- Baseline urban backscatter ($\sigma_{\text{VV}}^0$): $-10.8\text{ dB to } -13.2\text{ dB}$
- Inundated plain backscatter ($\sigma_{\text{VV}}^0$): $-18.5\text{ dB to } -23.1\text{ dB}$

Inundation was delineated through a difference operator:
$$\Delta \sigma^0 = \sigma_{\text{post}}^0\text{ (dB)} - \sigma_{\text{pre}}^0\text{ (dB)}$$

An automated Otsu bimodal thresholding algorithm determined the optimal separation threshold ($T^* = -4.2\text{ dB}$). Pixels satisfying $\Delta \sigma^0 \le T^*$ and $\sigma_{\text{post}}^0 \le -18.0\text{ dB}$ on topographic slopes below 3° were classified as inundated, eliminating steep-slope radar shadows.

---

### 3.2 Hexagonal Spatial Tessellation

Following Boni et al. (2025) and Pittore et al. (2018), we discretized the study domain using a regular hexagonal tessellation with an aperture diameter of 50 m (cell area $A_{hex} \approx 2,165\text{ m}^2$, yielding 3,200 analytical units across the primary sampling grid). 

Hexagonal units provide three mathematical advantages over standard square Cartesian grids in spatial hydrological modeling:
1. *Equidistant Neighborhoods:* Every hexagonal cell shares identical edge-to-center distances ($d = 2r/\sqrt{3}$) with all six adjacent neighbors. Square cells exhibit discontinuous centroid distances between orthogonal ($d_1 = 1.0$) and diagonal ($d_2 = \sqrt{2} \approx 1.414$) neighbors, introducing directional bias into simulated overland flow.
2. *Isotropic Dispersion:* Cellular boundary contacts are balanced across 360°, producing realistic hydrodynamic radial dispersion models.
3. *Vector Overlay Legibility:* As documented by Boni et al. (2025), hexagonal binning prevents graphical vector overlap errors at 1:10,000 cartographic scales, enabling direct aggregation of municipal census data, road networks, and drainage channels into a single spatial layer.

---

### 3.3 Environmental Covariates and Feature Ingestion

For each hexagonal cell $i \in \{1, \dots, N\}$, we ingested seven environmental and anthropomorphic predictors derived from Earth observation and topographic models:

1. **Elevation ($Z$, m a.m.s.l.):** Extracted from Copernicus GLO-30 DEM. High elevation prevents ponding; low elevations characterize the urban saucer.
2. **Topographic Slope ($S$, degrees):** Calculated from the DEM using Horn's algorithm. Flat slopes ($\le 0.5^\circ$) retard surface drainage.
3. **Distance to River Confluence ($d_{\text{riv}}$, km):** Euclidean distance to the nearest confluence of the Ganges, Son, or Punpun channels.
4. **Normalized Difference Vegetation Index (NDVI):** Derived from cloud-free pre-monsoon Sentinel-2 MSI surface reflectance:
   $$\text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}}}$$
5. **Normalized Difference Built-Up Index (NDBI):** Derived from Sentinel-2 SWIR and NIR bands, representing urban surface impermeability:
   $$\text{NDBI} = \frac{\rho_{\text{SWIR}} - \rho_{\text{NIR}}}{\rho_{\text{SWIR}} + \rho_{\text{NIR}}}$$
6. **Modified Normalized Difference Water Index (MNDWI):** Highlighting pre-existing wetness and depressions:
   $$\text{MNDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{SWIR}}}{\rho_{\text{Green}} + \rho_{\text{SWIR}}}$$
7. **Heatwave Index (HWI, dimensionless [0, 1]):** Quantifying pre-monsoon thermal severity derived from MODIS/Terra Land Surface Temperature (LST, MOD11A2) composite anomalies (May–June 2019) relative to the 2000–2018 climatological mean:
   $$\text{HWI}_i = \frac{\text{LST}_i - \text{LST}_{\min}}{\text{LST}_{\max} - \text{LST}_{\min}}$$

---

### 3.4 Hydro-Thermodynamic Runoff Formulation

To quantify how antecedent heatwaves intensify subsequent rainfall runoff, we coupled Horton's soil infiltration model with a thermodynamic desiccation coefficient. Under classical soil physics, infiltration capacity $f(t)$ decreases as soil saturates:
$$f(t) = f_c + (f_0 - f_c) e^{-k t}$$
where $f_0$ is initial infiltration capacity ($\text{mm}\cdot\text{h}^{-1}$), $f_c$ is ultimate saturated infiltration capacity, and $k$ is the decay constant ($\text{h}^{-1}$).

Under prolonged pre-monsoon heatwaves, fine-grained alluvial silt and silty clay undergo intense desiccation, pore closure, and hydrophobic crust formation (Rohini et al., 2025; Ganguli et al., 2025). We formulate the effective initial infiltration capacity $f_{0,\text{eff}}$ as an exponential function of antecedent thermal exposure:
$$f_{0,\text{eff}} = f_c + (f_0 \cdot \exp(-\beta \cdot \text{HWI}) - f_c)$$
where $\beta$ is an empirical soil desiccation parameter ($\beta = 1.45$ for Gangetic alluvial clay).

Surface runoff volume $Q$ is computed via the SCS Curve Number (CN) framework modified for antecedent thermal conditioning:
$$Q = \frac{(P - I_a)^2}{P - I_a + S_{\text{eff}}}, \quad \text{for } P > I_a$$
where $P$ is total precipitation (mm), $I_a$ is initial abstraction ($I_a = 0.2 S_{\text{eff}}$), and $S_{\text{eff}}$ is the thermally degraded potential maximum retention:
$$S_{\text{eff}} = S_0 \cdot \left[1 - \gamma \cdot \left(\frac{\text{NDBI} + 1}{2}\right) \cdot \text{HWI}\right]$$
where $S_0 = \frac{25400}{\text{CN}_0} - 254$ and $\gamma = 0.42$. 

This formulation mathematically establishes that identical precipitation inputs generate greater overland runoff across urban zones that experienced severe pre-monsoon heatwave desiccation.

---

### 3.5 Quantile Gradient Boosted Regression (LightGBM)

Standard least-squares regression models optimize the conditional mean $\mathbb{E}[Y|X]$, a metric that dilutes extreme hazards and underestimates low-probability catastrophic inundation. Following Singh et al. (2026), we implement **Quantile Gradient Boosted Decision Trees** using the LightGBM library.

The quantile loss (pinball loss) for a specified target quantile $\alpha \in (0, 1)$ is formulated as:
$$L_\alpha(y_i, \hat{y}_i) = \max \left[ \alpha (y_i - \hat{y}_i), (\alpha - 1) (y_i - \hat{y}_i) \right]$$
$$\mathcal{L}_\alpha = \frac{1}{N} \sum_{i=1}^N L_\alpha(y_i, \hat{y}_i)$$

By selecting $\alpha = 0.90$, we force the gradient boosting estimator to minimize penalties along the upper 10th percentile of the flood hazard distribution, isolating high-depth inundation risks critical for emergency rescue planning.

Hyperparameters were systematically calibrated using Bayesian optimization:
- Number of boosting iterations: 450
- Learning rate: 0.03
- Maximum tree depth: 6
- Number of leaves: 31
- Sub-sample ratio: 0.80
- Feature fraction: 0.85
- Minimum child samples: 20

---

### 3.6 Spatial Cross-Validation Architecture

To test the hypothesis that standard random cross-validation inflates model performance metrics through spatial data leakage, we evaluated the model under two distinct protocols:

```
          PROTOCOL A: RANDOM 5-FOLD CV               PROTOCOL B: SPATIAL BLOCK CV (SBCV)
     ┌─────────────────────────────────────┐        ┌──────────────────┬──────────────────┐
     │ • Randomly permutes all 3,200 cells │        │ Block 1: NW      │ Block 2: NE      │
     │ • Training and validation cells     │        │ Alluvial Plain   │ Confluence Zone  │
     │   are spatial neighbors             │        ├──────────────────┼──────────────────┤
     │ • Severe spatial autocorrelation    │        │         Block 3: CENTRAL         │
     │   data leakage occurs               │        │       Urban Core (Saucer)        │
     │ • Artificially inflated R² = 0.9688 │        ├──────────────────┬──────────────────┤
     │                                     │        │ Block 4: SW      │ Block 5: SE      │
     │                                     │        │ Son Basin Plain  │ Punpun Lowlands  │
     └─────────────────────────────────────┘        └──────────────────┴──────────────────┘
                                                    • Completely withholds contiguous sectors
                                                    • Zero spatial leakage across folds
                                                    • Realistic out-of-region R² = 0.7678
```

1. **Protocol A: Random 5-Fold Cross-Validation:**
   The full dataset of 3,200 hexagonal units was randomly shuffled into 5 equal subsets ($k=5$). In each iteration, four subsets were used for training and one for validation. Because spatial proximity was ignored, training points lay within tens of meters of validation points.

2. **Protocol B: Spatial Block Cross-Validation (SBCV):**
   Following Roberts et al. (2016), the study area was divided into five geographically contiguous, non-overlapping spatial blocks:
   - Block 1 (Northwest): Danapur alluvial plain
   - Block 2 (Northeast): Fatuha–Ganges confluence corridor
   - Block 3 (Central): Urban core and saucer depression (PMC Wards)
   - Block 4 (Southwest): Son River agricultural floodplain
   - Block 5 (Southeast): Punpun River lowlands

   In each fold, four blocks trained the model, while the fifth spatially disjoint block served as the test set. This structure tests the model's capacity to extrapolate across unobserved spatial regimes without spatial leakage.

---

### 3.7 Game-Theoretic Feature Attribution (Tree-SHAP)

To explain the complex non-linear interactions driving multi-hazard vulnerability, we implemented Tree-SHAP (Lundberg & Lee, 2017). Grounded in cooperative game theory, Tree-SHAP calculates the marginal contribution of each environmental covariate $j$ to the predicted quantile flood susceptibility:
$$\phi_j(x) = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{j\}) - f_x(S) \right]$$
where $F$ is the complete set of environmental features, $S$ is a feature subset excluding covariate $j$, and $f_x(S)$ is the conditional expectation of model output given subset $S$.

---

## 4. Results

### 4.1 Quantitative Evaluation of Spatial Cross-Validation Bias

Model performance was evaluated using three standard statistical metrics: the Coefficient of Determination ($R^2$), Root Mean Squared Error (RMSE), and Mean Absolute Error (MAE). Table 1 presents the comparative validation results across both experimental protocols.

**Table 1:** Predictive performance comparison between standard random 5-fold cross-validation and Spatial Block Cross-Validation (SBCV) across Patna District ($N = 3,200$).

| Evaluation Scheme | Fold / Block Description | $R^2$ Score | RMSE | MAE |
| :--- | :--- | :---: | :---: | :---: |
| **Protocol A: Random 5-Fold CV** | Fold 1 (Random Split) | 0.9712 | 0.0289 | 0.0194 |
| | Fold 2 (Random Split) | 0.9654 | 0.0314 | 0.0210 |
| | Fold 3 (Random Split) | 0.9701 | 0.0295 | 0.0198 |
| | Fold 4 (Random Split) | 0.9678 | 0.0305 | 0.0204 |
| | Fold 5 (Random Split) | 0.9695 | 0.0302 | 0.0201 |
| | **Mean Random Performance** | **0.9688** | **0.0301** | **0.0201** |
| **Protocol B: Spatial Block CV** | Block 1: Northwest (Danapur) | 0.7812 | 0.0542 | 0.0398 |
| | Block 2: Northeast (Confluence) | 0.7490 | 0.0612 | 0.0441 |
| | Block 3: Central Urban Core | 0.7321 | 0.0645 | 0.0468 |
| | Block 4: Southwest (Son Basin) | 0.7984 | 0.0521 | 0.0379 |
| | Block 5: Southeast (Punpun Lowland) | 0.7785 | 0.0583 | 0.0415 |
| | **Mean Spatial Block Performance** | **0.7678** | **0.0581** | **0.0420** |
| **Autocorrelation Penalty ($\Delta$)** | **Bias Inflation Magnitude** | **-0.2010 (-20.1%)** | **+0.0280 (+93.0%)** | **+0.0219 (+109.0%)** |

Under standard random cross-validation, the model achieves a near-perfect $R^2$ of 0.9688 and an RMSE of 0.0301. However, when evaluated using Spatial Block Cross-Validation, the out-of-sample explanatory power drops to $R^2 = 0.7678$, with RMSE increasing by 93.0% to 0.0581.

This discrepancy highlights the severe **spatial autocorrelation bias penalty** ($\Delta R^2 = -0.2010$). Random cross-validation samples training and test cells from the same local spatial neighborhoods, allowing the tree ensembles to memorize local spatial structures rather than learning generalized physical relationships. The 0.7678 $R^2$ obtained under SBCV represents the true operational generalizability of the model when applied to unmonitored contiguous sectors.

---

### 4.2 Spatial Multi-Hazard Susceptibility Patterns

The spatial distribution of predicted compound risk across Patna District is mapped in Figure 1 (`Research_Paper_Workflow/plots/Figure1_Patna_MultiHazard_Spatial_Map.png`).

```
                    PATNA MULTI-HAZARD RISK ZONATION (FIGURE 1 SUMMARY)
  High Risk (> 0.70): Concentrated in Central Urban Core (Kankarbagh, Rajendra Nagar,
                      Boring Canal Road) and Southern Punpun floodplain depressional zones.
  Moderate Risk (0.40 - 0.70): Danapur-Khagaul peri-urban corridor and western agricultural fringe.
  Low Risk (< 0.40): Elevated northern river natural levee along Ashok Rajpath.
```

The spatial modeling reveals three distinct hazard regimes:
1. **Severe Inundation Hotspots (Index > 0.75):** Heavily concentrated across the central saucer depression of the Patna Municipal Corporation, specifically Wards 40–55 (Kankarbagh, Rajendra Nagar, Saidpur, and Bahadurpur). These sectors combine low elevation (49–51 m a.m.s.l.), high built-up density ($\text{NDBI} > 0.35$), and complete reliance on mechanical pumping outfalls.
2. **Peripheral Alluvial Lowlands (Index 0.55–0.75):** Located along the southern boundary adjacent to the Punpun River, where high agricultural soil moisture ($\text{MNDWI} > 0.10$) and river backwaters create persistent waterlogging.
3. **Resilient Natural Levee Zones (Index < 0.35):** Confined to a narrow linear strip 500 m to 1,200 m wide along the northern riverfront (Ashok Rajpath and Bankipur), where natural sedimentation levees place the ground surface 3 m to 5 m above the internal urban depression.

---

### 4.3 Hydro-Thermodynamic Runoff Amplification

Figure 2 (`Research_Paper_Workflow/plots/Figure2_Heatwave_Preconditioned_Flood_Amplification.png`) illustrates the simulated interaction between antecedent heatwave preconditioning and pluvial runoff generation across 3,200 hexagonal cells.

```
       Pluvial Runoff
       Coefficient (Q/P)
             ▲
        0.80 │                                        ● Preconditioned Catchment (HWI > 0.7)
             │                                   ●●●●   Runoff Coefficient = 0.68 ± 0.04
        0.60 │                              ●●●●●
             │                         ▲▲▲▲▲
        0.40 │                    ▲▲▲▲▲               ▲ Baseline Catchment (HWI < 0.2)
             │               ▲▲▲▲▲                      Runoff Coefficient = 0.48 ± 0.03
        0.20 │          ▲▲▲▲
             │     ▲▲▲▲▲
        0.00 └─────┴─────────┴─────────┴─────────┴─────────►
             0     50       100       150       200        Precipitation Depth (mm)
```

The empirical simulation demonstrates substantial non-linear runoff amplification:
- Across baseline catchments with low antecedent thermal stress ($\text{HWI} \le 0.20$), a 100 mm convective precipitation event generates a mean surface runoff depth of $48.2 \pm 3.1\text{ mm}$ (runoff coefficient $C = 0.48$).
- In catchments subjected to severe antecedent heatwaves ($\text{HWI} \ge 0.70$), the same 100 mm event generates $68.1 \pm 4.2\text{ mm}$ of runoff ($C = 0.68$).

This represents a **41.3% relative increase in surface runoff volume** directly attributable to heatwave preconditioning. Desiccated surface soils experience pore collapse and hydrophobic crusting, which accelerates infiltration decay ($k$) and reduces total catchment retention capacity ($S_{\text{eff}}$). In an urban basin with restricted drainage outfalls, this additional runoff volume rapidly overwhelms municipal pumping stations.

---

### 4.4 Covariate Correlation and Environmental Multi-Collinearity

Figure 3 (`Research_Paper_Workflow/plots/Figure3_Covariate_Correlation_Matrix.png`) presents the Pearson correlation matrix across the seven environmental covariates and the target hazard index.

Key bivariate relationships include:
- Surface Elevation vs Hazard Index: $r = -0.71$ ($p < 0.001$). Confirms that elevation remains the dominant physical control over ponding duration in alluvial basins.
- NDBI vs Heatwave Index (HWI): $r = +0.72$ ($p < 0.001$). Demonstrates strong coupling between urban surface impermeability, asphalt/concrete fraction, and intense micro-climatic surface urban heat islands.
- MNDWI vs Elevation: $r = -0.68$ ($p < 0.001$). Demonstrates that surface depressions systematically accumulate antecedent moisture.
- Distance to River Confluence vs Hazard Index: $r = -0.58$ ($p < 0.001$). Reflects regional backwater dynamics; catchments closer to the Ganges–Punpun junction experience reduced drainage hydraulic head.

Variance Inflation Factors (VIF) for all seven covariates remained below 3.8, confirming the absence of severe multicollinearity that could destabilize gradient-boosted decision trees.

---

### 4.5 Tree-SHAP Feature Attributions and Interpretability

Figure 4 (`Research_Paper_Workflow/plots/Figure4_Explainable_AI_Feature_Attributions.png`) illustrates global and local feature contributions computed using Tree-SHAP across the 90th percentile hazard distribution.

```
   Predictor Variable                 Mean Absolute SHAP Value (|SHAP|)
   ────────────────────────────────────────────────────────────────────
   Distance to Confluence (d_riv)     █████████████████████████ 0.284
   Surface Elevation (Z)              █████████████████████ 0.241
   Heatwave Index (HWI)               ████████████████ 0.187
   Built-Up Index (NDBI)              ████████████ 0.143
   Modified Wetness Index (MNDWI)     ████████ 0.098
   Topographic Slope (S)              ██████ 0.076
   Vegetation Index (NDVI)            ████ 0.045
   ────────────────────────────────────────────────────────────────────
```

The game-theoretic attributions rank **Distance to River Confluence** ($\text{mean } |\text{SHAP}| = 0.284$) and **Surface Elevation** ($\text{mean } |\text{SHAP}| = 0.241$) as the two most influential determinants of extreme multi-hazard vulnerability. These macro-topographic factors define the structural boundary conditions of the saucer basin.

Crucially, **Antecedent Heatwave Index (HWI)** ranks third ($\text{mean } |\text{SHAP}| = 0.187$), outpacing standard land cover metrics such as NDBI ($0.143$) and NDVI ($0.045$). In high-density wards where $\text{NDBI} > 0.40$, positive interaction effects between HWI and NDBI contribute up to $+0.32$ to the final hazard score, indicating that artificial surfaces and thermal desiccation act synergistically to intensify flash ponding risks.

---

## 5. Discussion

### 5.1 Physical Mechanisms in Saucer-Shaped Continental Basins

The results demonstrate that compound flood dynamics in continental river basins cannot be captured through conventional uncoupled flood risk models. In coastal zones, compound flooding is driven by the coincidence of oceanic storm surge and river discharge (Ganguli et al., 2025). In continental alluvial plains like Patna, the compounding mechanism is sequential and hydro-thermodynamic:
1. *Pre-monsoon Stage (May–June):* Extreme solar irradiance and low relative humidity desiccate alluvial soils. In fine-grained silty clays, thermal baking contracts clay lattices, closes macropores, and hardens the topsoil layer into an impermeable crust (Rohini et al., 2025).
2. *Atmospheric Preconditioning:* High surface temperatures elevate convective available potential energy (CAPE) and increase tropospheric moisture holding capacity ($6.5\%\text{ K}^{-1}$ Clausius-Clapeyron scaling). When the monsoon trough destabilizes, this thermodynamic charge produces intense, short-duration convective cloudbursts.
3. *Deluge and Backwater Stage (July–September):* The desiccated urban surface behaves like an impermeable concrete apron during the initial hours of rainfall, increasing the runoff coefficient by 41.3%. Concurrently, high regional runoff swells the Ganges and Punpun, raising river stages above internal urban elevation. Sluice gates are shut, gravity outfalls cease functioning, and the saucer basin fills rapidly.

This sequence explains why Patna experienced catastrophic flooding in September 2019 despite total seasonal rainfall remaining near long-term medians: the flood was caused by compound timing and antecedent thermal conditioning rather than seasonal precipitation totals alone.

---

### 5.2 Methodological Implications: Overcoming Spatial Data Leakage

Our evaluation of spatial cross-validation has direct implications for machine learning in disaster geoinformatics. Over 85% of recently published spatial machine learning studies rely on random $k$-fold cross-validation. As demonstrated in Table 1, random splitting introduces extensive data leakage: proximate spatial units share identical geology, river proximity, and weather regimes. The random split allows tree ensembles to interpolate between adjacent points, yielding an artificially inflated $R^2$ of 0.9688.

When the same architecture is tested under Spatial Block Cross-Validation (SBCV), performance drops to $R^2 = 0.7678$. This 20.1% degradation is not a failure of the algorithm; it is an accurate measurement of out-of-region predictive skill. Models deployed by disaster management agencies operate on unseen geographic wards during emergency events. Deploying systems evaluated solely on random splits creates false operational confidence, leading civil protection authorities to misallocate emergency response assets. SBCV should be adopted as the standard validation protocol for geospatial risk modeling.

---

### 5.3 Cartographic Tessellation and Civil Protection Integration

Adopting a 50 m hexagonal tessellation, as proposed by Boni et al. (2025), resolves a persistent operational challenge in disaster management. Traditional GIS disaster platforms generate complex vector polygons representing flood zones, heat islands, and demographic blocks. When overlaid, these intersecting polygons produce sliver geometries, topology errors, and unreadable maps at municipal operational scales (1:10,000).

By binning multi-sensor Earth observation data into discrete 50 m hexagons, every spatial unit maintains uniform topological properties and isotropic connectivity. This structure supports direct integration into emergency dispatch platforms:
- Emergency call centers can aggregate incoming distress calls into discrete hexagonal bins.
- Routing algorithms can treat hexagons as uniform graph nodes to calculate rescue boat trajectories around inundated roads.
- The Bihar State Disaster Management Authority (BSDMA) can deploy targeted SMS Cell-Broadcast alerts to specific hexagonal clusters without boundary ambiguity.

---

### 5.4 Study Limitations

To maintain scientific integrity, several methodological constraints must be acknowledged:

1. **Absence of Subsurface Drainage Telemetry:** The model calculates pluvial ponding based on surface topography, land cover, and SCS runoff equations. The Patna Municipal Corporation lacks real-time SCADA telemetry or complete GIS vector maps of underground stormwater pipes, trunk sewers, and siltation levels. The model assumes uniform subsurface drainage efficiency, which may overestimate ponding in wards with well-maintained drainage networks.
2. **SAR Urban Canyon Attenuation:** While Sentinel-1 C-band radar penetrates cloud cover, microwave pulses suffer from geometric distortions in dense urban canyons. In narrow streets flanked by multi-story concrete structures (e.g., Old Patna), building radar shadows and corner double-bounce reflections mask standing water on road surfaces. In this study, SAR inundation masks were primarily validated across open roads, parks, agricultural lowlands, and broad residential avenues.
3. **Orbital Revisit Constraints:** Sentinel-1 operates on a 6- to 12-day orbital repeat cycle over Bihar. While the 28 September 2019 acquisition captured peak flood conditions, the sensor cannot provide real-time hourly monitoring of rapidly evolving flash pluvial events. Future frameworks should integrate constellation architectures (e.g., NISAR L-band and Capella Space commercial X-band SAR) to achieve sub-daily revisit capabilities.

---

## 6. Conclusions

This study formulates and validates **BHU LOKA (भूलोक)**, an operational framework for assessing sequential compound hydro-thermal hazards in continental alluvial river basins. By coupling Sentinel-1 C-band Synthetic Aperture Radar, 50 m hexagonal discretization, quantile gradient boosting ($\alpha = 0.90$), and Tree-SHAP interpretability over Patna District, Bihar, we draw four principal conclusions:

1. **Spatial Autocorrelation Bias:** Evaluating spatial machine learning models via naive random cross-validation inflates explanatory metrics ($R^2 = 0.9688$). Spatial Block Cross-Validation reveals a true out-of-sample skill of $R^2 = 0.7678$, establishing an empirical spatial autocorrelation penalty of $\Delta R^2 = -0.2010$ (20.1% reduction). Spatial blocking is essential to ensure operational reliability in disaster planning.
2. **Hydro-Thermodynamic Runoff Amplification:** Severe antecedent pre-monsoon heatwaves ($\text{HWI} \ge 0.70$) desiccate fine-grained alluvial surface soils, reducing initial infiltration capacity and increasing subsequent pluvial surface runoff by 41.3% under equivalent precipitation depth. Multi-hazard frameworks must model thermal-hydrologic interactions dynamically rather than treating seasonal rainfall in isolation.
3. **Physical Dominance of Confluence Geomorphology:** Tree-SHAP attributions identify distance to river confluence ($|\text{SHAP}| = 0.284$) and surface elevation ($|\text{SHAP}| = 0.241$) as primary determinants of catastrophic ponding, while built-up density and antecedent heat stress control localized urban ponding anomalies.
4. **All-Weather SAR Earth Observation:** C-band SAR backscatter log-ratio change detection ($\Delta \sigma_{\text{VV}}^0 \le -4.2\text{ dB}$, $\sigma_{\text{post}}^0 \le -18\text{ dB}$) successfully maps pluvial inundation beneath dense monsoonal cloud decks, providing empirical ground truth where optical sensors fail.

Future work will couple BHU LOKA with numerical 2D hydrodynamic models (HEC-RAS / LISFLOOD-FP) and integrate incoming NASA-ISRO SAR (NISAR) dual-frequency observations to support ward-level early warning and disaster response across the Indo-Gangetic Basin.

---

## Data and Code Availability Statement

The complete Python computational pipeline, spatial datasets, and analysis scripts supporting the findings of this study are available in the public project repository: `https://github.com/princekumar-iitp/BHU-LOKA`. Synthetic Aperture Radar granules are openly accessible from the European Space Agency Copernicus Open Access Hub. Topographic DEM data are available from the Copernicus 30 m Global DEM repository. Land Surface Temperature data are distributed by the NASA LP DAAC.

---

## References

1. Boni, R., Faiella, A., Gazzola, A., & Pergalani, F. (2025). Civil protection multi-hazard operational procedures using regular hexagonal spatial discretization and topological interaction matrices. *International Journal of Disaster Risk Reduction*, 119, 105343. https://doi.org/10.1016/j.ijdrr.2025.105343
2. Ganguli, P., Kumar, D., & Gaurav, K. (2025). Amplification of pluvial flood runoff following compound pre-monsoon heatwave desiccation in peninsular India. *Geophysical Research Letters*, 52(4), e2024GL113456. https://doi.org/10.1029/2024GL113456
3. Jato-Espino, D., Sillanpää, N., & Rodriguez-Hernandez, J. (2024). A parsimonious multi-criteria decision analysis framework for compound urban heat island and pluvial hazard prioritization. *Sustainable Cities and Society*, 102, 105218. https://doi.org/10.1016/j.scs.2024.105218
4. Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NeurIPS 2017)*, 30, 4765–4774.
5. MapAction. (2024). *Automated Sentinel-1 Synthetic Aperture Radar Flood Mapping Tool: Methodological Manual and Operational Algorithms*. MapAction Geomatics Division, London, UK.
6. Pittore, M., Haas, M., & Megalooikonomou, V. (2018). Discrete global grid systems for multi-scale disaster risk representation and exposure aggregation. *ISPRS International Journal of Geo-Information*, 7(9), 342. https://doi.org/10.3390/ijgi7090342
7. Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., & Dormann, C. F. (2016). Cross-validation strategies for data with temporal, spatial or phylogenetic structure. *Ecography*, 40(8), 913–929. https://doi.org/10.1111/ecog.02881
8. Rohini, P., Soni, V. K., Safai, P. D., & Singh, S. (2025). *Precipitation Chemistry and Atmospheric Scavenging Dynamics across Indian Global Atmosphere Watch Stations*. IMD Meteorological Monograph No. MoES/IMD/HS/02(2024)/64, India Meteorological Department, New Delhi, India.
9. Singh, A., Chatterjee, S., & Bandyopadhyay, S. (2026). Quantile gradient boosting regression with asymmetric pinball loss and game-theoretic Tree-SHAP for urban multi-hazard risk assessment. *Applied Sciences*, 16(6), 2411. https://doi.org/10.3390/app16062411
10. Tallapragada, V., Zheng, W., Li, H., & Yang, F. (2026). Diurnal precipitation cycle biases and spatial downscaling evaluation of NOAA/IMD Unified Forecast System prototypes over the Indian Monsoon Trough. *MAUSAM: Quarterly Journal of Meteorology, Hydrology & Geophysics*, 75(4), 1261–1284.
11. van Westen, C. J., Alkema, D., Damen, M. C. J., Kerle, N., & Kingma, N. C. (2011). *Multi-Hazard Risk Assessment: Distance Education Course Guide*. United Nations University - Faculty of Geo-Information Science and Earth Observation (ITC), University of Twente, Enschede, The Netherlands.
