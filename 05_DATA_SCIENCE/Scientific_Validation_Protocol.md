# BHU LOKA (भूलोक) — Scientific Validation Protocol (R0 / R0.1 Aligned)

**Document ID:** `BHU-SVP-R0`  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Primary Scientific Priority:** Authentic NASA Earth Observation (`MOD11A1.061`, `MOD11A2.061`, `MOD13Q1.061`, `HLSL30.020`, `GIBS`, `LaRC POWER AG`) + USGS/NASA Landsat C2 L2 + Copernicus Sentinel-1/2 (software-only analytics)  
**Peer-Review Reference:** Roberts et al. (2016/2017), *Ecography* — Spatial Block Cross-Validation (`Research_Papers/`)  

---

## 1. Empirical Experiment Verification Ledger

All numerical metrics cited in BHU LOKA research reports and dashboards MUST trace directly to committed outputs:

| Experiment / Artifact | Ground-Truth Source File | Verified Quantities | Known Nuances & Limitations |
| :--- | :--- | :--- | :--- |
| **Exp 01: Sentinel-1 SAR Flood & UN-SPIDER Benchmark** | `Experiments/Exp_01_SAR_Flood_Inundation/exp01_results.json`, `unspider_vs_bhu_loka_benchmark.json`, `run_sar_experiment_v2.py` | Granules: `S1A_IW_GRDH_VV_20190923_pre_flood.tif` & `S1B_IW_GRDH_VV_20190929_peak_flood.tif` (10 m, VV-only). PMC area: `133.87 km^2`. BHU LOKA total flooded area: `99.60 km^2` (`74.40%`). UN-SPIDER ($\Delta\sigma^0 \le -2.0\text{ dB}$): `4.01 km^2` (`2.99%`), urban omission error `95.98%`. | `exp01_results.json` splits `0.07 km^2` specular + `99.52 km^2` double-bounce; `unspider_vs_bhu_loka_benchmark.json` records `1.15 km^2` + `94.08 km^2` under its secondary comparison mask while reporting identical `99.60 km^2` total. Only VV co-polarization is present locally. |
| **Exp 02: Copernicus GLO-30 DEM** | `Experiments/Exp_02_Copernicus_DEM_Terrain/exp02_results.json` | Frame `142.48 km^2`; elevation `40.00` to `72.99 m`, mean `53.99 m (+/- 3.0 m)`, mean slope `2.31 deg`, slope `< 1 deg`: `25.24%`, closed sinks: `47.24 km^2` (`33.15%`). | Topographic sinks indicate potential drainage retention behind river levees when sluices close (`>49.5 m`). |
| **Exp 03: NASA Terra MODIS LST** | `Experiments/Exp_03_MODIS_Thermal_Heat/exp03_results.json` | MOD11A1 v061 (`2019-04-01` to `2019-06-30`), `91` daily scenes, `61` clear-sky. Mean urban LST `37.29 C`, mean rural LST `38.32 C`, daytime urban-minus-rural delta `-1.03 C`, peak urban LST `46.25 C` (`45.32 C` spatial mean on DOY 139). | Terra 10:30 AM ascending pass measures daytime fallow bare-soil rural heating exceeding vegetated/shaded urban corridors (`-1.03 C`); nocturnal canopy/surface SUHI is not measured by this daytime pass. |
| **Exp 04: Population & ULSI** | `Experiments/Exp_04_MultiHazard_Fusion/exp04_results.json` | WorldPop 2020 core `214,281`; flood-exposed `167,246`; in depression sinks `60,790`; compound hazard `49,380`; mean PMC ULSI `52.27` (S1: `20.1%`, S2: `27.7%`, S3: `33.1%`, S4: `19.1%`). | ULSI is a screening index requiring local geotechnical survey prior to construction. |

---

## 2. Spatial Machine Learning Protocol (`train_spatial_model.py`)

Following Roberts et al. (2016/2017), nearby spatial pixels share unobserved hydrological and urban structural covariance ($\text{Cov}(Z(s), Z(s+h)) > 0$). Validation MUST isolate spatial test blocks from training blocks:

1. **Sample Design:** $N = 60{,}000$ stratified points ($30{,}000$ flooded, $30{,}000$ non-flooded) across the $2{,}602 \times 1{,}709$ aligned Patna grid.
2. **Spatial Partitioning:** Partitioned into $5$ contiguous longitudinal spatial strips (`block_width = W // 5`, `spatial_blocks = clip(x // block_width, 0, 4)`).
3. **Executed Estimator:** `sklearn.ensemble.RandomForestClassifier` (`n_estimators=100`, `max_depth=12`, `random_state=42`). Note that LightGBM ($\alpha=0.90$) and Tree-SHAP remain planned research comparisons rather than executed code in `train_spatial_model.py`.
4. **Verified Metrics (`Models/01_Spatial_ML/spatial_cv_metrics.json`):**
   - Mean 5-Fold SBCV ROC-AUC: **`0.7498 +/- 0.0497`** (Folds: `0.6855`, `0.7900`, `0.7999`, `0.7802`, `0.6937`)
   - Mean F1-Score: **`0.6530`**
   - Mean Accuracy: **`68.88%`**
   - Mean Brier Score: **`0.2003`**
5. **Known Input-Feature Caveat (`SAR_Pre_dB` Importance = `0.00%`):** When the precomputed `Data/08_Processed_Outputs/patna_2019_delta_sigma0.npy` array exists on disk, `train_spatial_model.py` lines 70–74 construct `sar_pre_db` as a constant `-12.0 dB` array (`sar_post_db = sar_pre_db + delta_sigma0`). Consequently, Gini split importance for `SAR_Pre_dB` is exactly `0.0`, while `SAR_Post_dB` (`0.3676`) and `Delta_Sigma0` (`0.2993`) carry the radar variance. Any manuscript or defense slide citing `spatial_cv_metrics.json` MUST disclose this precomputed-delta constant baseline transparently.

---

## 3. Enterprise RAG Evaluation Protocol

- **Faithfulness Gate (`BhuLokaGuardrails` & `RagasEvaluator`):** Synthesized responses must achieve context groundedness / faithfulness $\ge 0.70$ against `retrieved_docs`.
- **Telemetry & Agricultural Context Rule:** External weather, flood, or farm observations passed to the RAG pipeline MUST be serialized into a provenance-stamped synthetic document inside `retrieved_docs` prior to answer synthesis and RAGAS scoring, never bypassed as unverified assertions.
