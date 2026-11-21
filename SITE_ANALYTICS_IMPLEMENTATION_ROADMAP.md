# BHU LOKA — AI SITE ANALYTICS IMPLEMENTATION ROADMAP
**Document ID:** `BL-ROADM-SITE-AI-2026-V1`  
**System:** BHU LOKA (भूलोक) Planetary Geospatial Intelligence Platform  
**Target:** 6-Phase Engineering Execution Plan & Resource Budget

---

## 1. Phased Implementation Timeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ENGINEERING EXECUTION ROADMAP                                 │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│      PHASE 1      │      PHASE 2      │      PHASE 3      │      PHASE 4      │     PHASE 5-6   │
│ Audit & Arch Plan │ Backend FastAPI   │ Frontend Studio   │ Bi-Temporal Change│ DeepForest ITC, │
│  (COMPLETE NOW)   │ Microservice MVP  │ Integration       │ & Split View      │ PDF Dossier, QA │
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

---

## 2. Phase-by-Phase Breakdown

### Phase 1: Existing Project Audit & Architecture Formulation *(Status: COMPLETED)*
* Complete audit of 2D map (Leaflet), 3D Earth (Cesium / Three.js), Land Intelligence Studio, and Python pipeline modules.
* Formalization of Deliverables:
  - `GEOSPATIAL_AI_MODEL_RESEARCH.md`
  - `DATASET_AND_LICENSE_AUDIT.md`
  - `AI_SITE_ANALYTICS_ARCHITECTURE.md` (and `BHU_LOKA_AI_ARCHITECTURE.md`)
  - `SATELLITE_DATA_PIPELINE.md`
  - `MODEL_BENCHMARK_PLAN.md` (and `MODEL_SELECTION_AND_BENCHMARK.md`)
  - `GIS_ANALYSIS_WORKFLOW.md`
  - `SITE_ANALYTICS_IMPLEMENTATION_ROADMAP.md` (and `IMPLEMENTATION_ROADMAP.md`)
* Railway track & road anti-hallucination masks implemented and verified in Land Studio.
* Watermark-free OSM France and Esri Dark Canvas basemaps verified.
* Circle AOI and Zone Grid toggle switches integrated.

### Phase 2: Lightweight FastAPI Geospatial Microservice MVP
* Create `Pipelines/bhu_loka_site_analytics_api.py` (FastAPI + Pydantic v2 + Uvicorn).
* Integrate STAC client (Microsoft Planetary Computer / Copernicus CDSE) with windowed HTTP Range COG reading.
* Deploy **SegFormer-B0** ($3.7\text{M}$ parameters) pretrained on LoveDA / LandCoverNet for 7-class semantic segmentation:
  - Building, Road, Water, Barren, Forest/Canopy, Agriculture, Background.
* Vectorize prediction mask with `rasterio.features.shapes`.
* Auto-project to local UTM CRS for metric hectare and coverage percentage calculation.
* Expose REST endpoints: `/api/v1/analyze`, `/api/v1/preview`, `/api/v1/results`.

### Phase 3: Frontend Integration in Land Intelligence Studio
* Add fifth primary tab in Land Intelligence Studio header:
  `[ 2D MAP ] [ EXPLODED 3D ] [ ANALYSIS BOARD ] [ ML & MODEL CARD ] [ 🛰️ AI SITE ANALYTICS ]`
* Integrate AOI controls: Square, Radial Circle, Polygon, 500m–5km presets.
* Integrate acquisition date picker (Single date or Before/After date range).
* Real-time progress bar (streaming SSE: "Fetching Sentinel-2 COG... 30%", "Inference... 65%", "Vectorizing... 90%").
* Interactive layer visibility toggles and opacity sliders for all 7 segmented classes.
* Floating AI Spectral Object Decoder showing live class areas ($ha$ and $\%$).

### Phase 4: Bi-Temporal Change Detection & Swipe Comparison
* Implement bi-temporal scene alignment and difference engine:
  - Compares $t_1$ (e.g. 2024) vs $t_2$ (e.g. 2026).
  - Highlights newly constructed buildings (Red), vegetation loss/tree felling (Orange), and lake boundary shrinkage (Cyan).
* Add interactive "Before / After" split-screen swipe slider on the map.
* Calculate net land-use transition matrix:
  $$\Delta \text{Built} = +\text{X ha}, \quad \Delta \text{Green} = -\text{Y ha}, \quad \Delta \text{Water} = -\text{Z ha}$$

### Phase 5: DeepForest VHR Tree Crown Delineation & Legal PDF Dossier
* Integrate `deepforest` (MIT License) for sub-meter ($< 0.5\text{m}$) drone and VHR satellite imagery:
  - Counts individual tree crowns.
  - Generates crown polygons and diameter statistics.
* Integrate ReportLab / WeasyPrint for official Government Encroachment Dossier PDF:
  - High-res satellite before/after orthophoto.
  - Boundary survey coordinates and statutory 30m Lake FTL buffer violation flags.
  - Digital SHA-256 verification seal and timestamps.

### Phase 6: Production Hardening, Automated Testing & Scaling
* Expand Pytest suite to cover end-to-end API inference, STAC windowed reading, and UTM metric calculations.
* Validate memory limits (ensure peak RSS $< 2.0\text{ GB}$ per worker).
* Dockerize microservice (`Dockerfile.site_analytics`) with multi-stage build.
* Provide zero-cloud local fallback mode (runs purely on local CPU or GPU without external cloud costs).

---

## 3. Computational Resource & Budget Estimates

| Resource Layer | Development / Testing Tier | Production MVP Tier | Scaled Multi-Tenant Tier |
| :--- | :--- | :--- | :--- |
| **Compute / Host** | Local Workstation (CPU or GPU) | 1x Cloud VM (4 vCPU, 16 GB RAM) | 2x Auto-Scaled VM + 1x T4 GPU |
| **GPU Requirement** | None required (SegFormer-B0 runs on CPU in ~65ms) | Optional (NVIDIA T4 16GB) | NVIDIA T4 / L4 (16GB–24GB VRAM) |
| **RAM Footprint** | $\le 1.8\text{ GB}$ RAM | $\le 4.0\text{ GB}$ RAM | $\le 8.0\text{ GB}$ RAM |
| **STAC Satellite Data API** | **$0.00** (Copernicus CDSE / Planetary Computer open tiers) | **$0.00** (Open Data) | **$0.00** (Open Data) |
| **Storage (COG Cache)** | 5 GB Local NVMe | 50 GB Object Storage (S3 / GCS) | 200 GB Managed COG Bucket |
| **Monthly Cloud Cost** | **$0.00 / month** | **$30 - $60 / month** (CPU-only VM) | **$180 - $280 / month** (GPU instance) |

---

## 4. Risk Mitigation & Scientific Guardrails

| Risk | Probability | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Monsoon Cloud Cover** | High (June–Sept) | High | Fall back to **Sentinel-1 SAR** ($\sigma^0\text{ dB}$) flood/urban double-bounce analysis. Automatically reject optical scenes with $> 15\%$ cloud cover. |
| **Tree Species Misclassification** | High | Critical | **Scientific Guardrail:** Strictly prohibit tree species claims on 10m Sentinel-2 or RGB imagery. Label as "Vegetation Canopy (Species Unclassified)". |
| **Building False Positives on Tracks** | Low (Resolved) | High | Enforce **32m buffer spatial mask** on all railway corridors and **14m buffer** on arterial road centerlines. |
| **License Violation (e.g. AGPL)** | Low | High | Avoid YOLO11-Seg in production backend. Use **SegFormer (Apache 2.0)** and **DeepForest (MIT)**. |
| **API Cost Overruns** | Low | Medium | Enforce **Windowed COG Range Reads** (`rasterio.windows.from_bounds`). Never download full 1 GB scenes. |
