# 🏛️ Master Research Compendium & Academic Defense Blueprint: Project BHU LOKA (भूलोक)

**Title:** Sequential Compound Hydro-Thermal Risk and Urban Corner-Reflector Flood Mapping in Continental Alluvial Metropolises: Empirical Earth Observation and Spatial Validation Sensitivity over Patna, India  
**Principal Investigator & Author:** Prince Kumar (Department of Computer Science & Engineering, IIT Patna, Roll No. PA2511CDH37)  
**Research Supervisor & Co-Author:** Pallav Rustogi  
**Target Submission Venues:** *International Journal of Disaster Risk Reduction (Elsevier)* | *InterPore Journal*  
**Document Location:** `Bhu Loka - भूलोक/Research_Paper_Workflow/Review/04_Master_Research_Compendium_and_PhD_Blueprint.md`

---


## Executive Summary

Urban risk governance across the Indo-Gangetic Basin confronts compound hydro-thermal extremes shaped by pre-monsoon heat stress, flat alluvial relief, embanked river confluences, and dense street canyons. **BHU LOKA (भूलोक)** integrates eight foundational literature pillars with a dual-track reproducible empirical and modeling workflow over Patna, Bihar ($\approx 3,200\text{ km}^2$):


1. **Track 1 (`EMPIRICAL_EO`):** Pairs 10 m Sentinel-1A/B SAR (23 Sep & 29 Sep 2019), 30 m Copernicus GLO-30 DEM, 91 daily NASA Terra MODIS (`MOD11A1.061`) thermal granules, WorldPop 2020 population rasters, and a 60,000-pixel 5-fold SBCV Random Forest classifier (`ROC-AUC = 0.7498 +/- 0.0497`). Proves that standard UN-SPIDER specular thresholding (`4.01 km^2`) omits 95.98% of inundated PMC streets compared to bimodal specular + dihedral corner double-bounce detection (`99.60 km^2`, 74.4% of the `133.87 km^2` municipal core).
2. **Track 2 (`DERIVED_SIMULATION_PROXY`):** Benchmarks `sklearn` `RandomForestRegressor` and Quantile `GradientBoostingRegressor` ($\alpha \in \{0.50, 0.90\}$) over $N = 3,200$ synthetic points, proving a -14.8% mean SBCV penalty ($R^2 = 0.9688 \to 0.8258$, collapsing to $R^2 = 0.5266$ inside Central Urban Core Block 2) and a +17.4% controlled urban runoff escalation above $40^\circ\text{C}$.

---


## 1. Theoretical Knowledge Base (Verified Bibliography Pillars)


| Pillar | Source Citation (Verified PDF) | Method / Domain | Role in BHU LOKA |
| :---: | :--- | :--- | :--- |
| 1 | Ganguli et al. (2025), *Geophysical Research Letters*, 52, `e2025GL115795` | Compound heatwave-flood extremes (Chennai) | Physical mechanism for pre-monsoon desiccation & Clausius-Clapeyron moisture scaling |
| 2 | Roberts et al. (2017), *Ecography*, 40(8), 913–929 | Spatial Block Cross-Validation | Eliminating spatial autocorrelation leakage via contiguous holdout blocks |
| 3 | Singh et al. (2026), *Land*, 15(3), 488 | Quantile LightGBM & SHAP (Delhi) | Motivation for $\alpha = 0.90$ pinball quantile regression via `sklearn` GBR |
| 4 | Jato-Espino et al. (2025), *IJDRR*, 119, `105277` | Compact multi-hazard MCDA (heat/flood/PM10) | Parsimonious indicator design avoiding collinear bloat |
| 5 | Rohini et al. (2025), *IMD Monograph* `MoES/IMD/HS/Chemistry of Rain/02(2024)/64` | Indian GAW rainwater chemistry & washout | Aerosol loading and pre-monsoon surface chemical context over northern plains |
| 6 | van Westen et al. (2011), *UNU-ITC RiskCity* | Hazard x Exposure x Vulnerability | Classical composite exposure matrix underlying WorldPop / ULSI overlay |
| 7 | Boni et al. (2025), *IJDRR*, 119, `105343` & Pittore et al. (2023), *Nat. Hazards* 119 | Regular 50 m hexagonal DGGS | Target cartographic aggregation architecture for municipal dispatch |
| 8 | Tallapragada et al. (2026), *MAUSAM*, 77(4), 1261–1284 | NOAA/IMD UFS Monsoon evaluation | Explaining $0.25^\circ$ NWP diurnal convective bias and downscaling needs |
| 9 | MapAction (2024), *flood-mapping-tool* (`UN-SPIDER`) | Specular SAR change baseline | Empirical urban flood omission benchmark ($4.01\text{ km}^2$ vs $99.60\text{ km}^2$) |

---


## 2. Empirical Data Matrix & Processing Integrity


| Dataset / Module | Resolution / Scope | Provenance Tier | Key Verified Outputs |
| :--- | :--- | :--- | :--- |
| **Sentinel-1A/B (23 & 29 Sep 2019)** | 10 m IW VV ($2602 \times 1709$ px) | `EMPIRICAL_EO` | Otsu $T^* = -3.80\text{ dB}$; `26.54 km^2` bbox specular; `99.60 km^2` (74.4%) PMC bimodal; 95.98% UN-SPIDER omission |
| **Copernicus GLO-30 DEM** | 30 m EGM2008 (`142.48 km^2` grid) | `EMPIRICAL_EO` | Elev 40.00–72.99 m (mean 53.99 m); mean slope $2.31^\circ$; `47.24 km^2` (33.15%) sinks |
| **NASA Terra MODIS `MOD11A1.061`** | 1 km daily (61 clear / 91 scenes) | `EMPIRICAL_EO` | Mean urban LST $37.29^\circ\text{C}$; peak pixel $46.25^\circ\text{C}$; DOY 139 urban core $45.32^\circ\text{C}$; morning urban-fallow delta $-1.03^\circ\text{C}$ |
| **WorldPop 2020 & ULSI** | 10 m resampled PMC mask | `EMPIRICAL_EO` | `214,281` modeled PMC residents (`167,246` flooded, `49,380` compound flood+sink); mean ULSI `52.27/100` |
| **60k-Pixel Spatial RF SBCV** | 5 west-east strips ($N = 60,000$) | `EMPIRICAL_EO` | Mean `ROC-AUC = 0.7498 +/- 0.0497`, `F1 = 0.6530`, Acc `68.88%`, Brier `0.2003` |
| **Hydro-Thermal Simulation Proxy** | $N = 3,200$ synthetic points | `DERIVED_SIMULATION_PROXY` | Random CV $R^2 = 0.9688$ -> SBCV $R^2 = 0.8258$ (-14.8%); Urban Block 2 $R^2 = 0.5266$; controlled $+17.4\%$ runoff escalation |
| **Sentinel-2 MSI & IMD Rainfall** | 10–20 m optical / $0.25^\circ$ gauge | External Planned | Guide placeholders only (`Data/03_Optical_Sentinel2`, `Data/05_Rainfall_IMD`); planned ingestion |

---


## 3. Operational Limitations & Defense Checklist

1. **No Conflation of Tracks:** Defense materials strictly report Track 1 real EO findings separately from Track 2 parametric sensitivity benchmarks (`sklearn` RF + Quantile GBR, NOT LightGBM or Tree-SHAP).
2. **MODIS Diurnal Interpretation:** Morning 10:30 AM Terra passes exhibit $-1.03^\circ\text{C}$ urban-minus-fallow delta due to bare fallow pre-monsoon soil warming (`38.32 C` rural fallow vs `37.29 C` urban core); nocturnal LST passes (`MOD11A1` night) are queued for night-time SUHI verification.
3. **Hexagonal DGGS Roadmap:** Regular 50 m hexagonal geometry following Boni et al. (2025) and Pittore et al. (2023) is specified as the target municipal integration schema rather than being instantiated inside the current $N = 3,200$ point script.
4. **Next-Phase Empirical Completion:** Download Sentinel-2 pre-monsoon MSI + IMD $0.25^\circ$ daily rain grids, integrate NISAR dual-band SAR once operational, and train gradient-descent `BhuLokaOmniNet` / LoRA Geo-SLM weights on verified empirical labels.
