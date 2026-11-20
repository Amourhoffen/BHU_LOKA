# BHU LOKA (भूलोक) — PHASE 0 EMPIRICAL EVIDENCE REPORT
**Repository State, Runtime Verification & Execution Diagnostics**
**Document ID:** `BL-EVD-2026-V1`  
**Date:** 20 November 2026  
**Repository Branch:** `feature/bhu-loka-india-gis-reengineering`  
**Primary Git Remote:** `competition` (`https://github.com/Amourhoffen/BhuLoka.git`)  
**Secondary Remotes:** `origin` (`https://github.com/Amourhoffen/BHU_LOKA.git`), `backup` (`https://github.com/Amourhoffen/BHU_LOKA_privite.git`)  
**Evidence Standard:** 100% Measured Runtime & Code Inspection Data (No Hallucinated Results)  

---

## 1. GIT REPOSITORY & DEPLOYMENT STATE (VERIFIED)

### 1.1 Branch & Remote Topology
The following data was obtained directly from host git execution:
- **Current Active Branch**: `feature/bhu-loka-india-gis-reengineering` [VERIFIED]
- **Main Branch Status**: Unmodified, preserved intact.
- **Head Commit Hash**: `2083512`
- **Head Commit Message**: `feat(v6.2): mobile-first shell, fix JS syntax error, segmented Land Studio tabs, drawer fixed rows, multi-hazard routing`
- **Configured Remotes**:
  ```
  competition  https://github.com/Amourhoffen/BhuLoka.git (fetch)
  competition  https://github.com/Amourhoffen/BhuLoka.git (push)
  origin       https://github.com/Amourhoffen/BHU_LOKA.git (fetch)
  origin       https://github.com/Amourhoffen/BHU_LOKA.git (push)
  backup       https://github.com/Amourhoffen/BHU_LOKA_privite.git (fetch)
  backup       https://github.com/Amourhoffen/BHU_LOKA_privite.git (push)
  ```

### 1.2 Binary Synchronization: Root vs `public/` (VERIFIED)
An automated Node.js byte-matching script (`fs.readFileSync().equals()`) evaluated every core file against its `public/` mirror on 2026-11-20T18:43:50:

| Root File | `public/` Mirror File | File Size (Bytes) | Exact Binary Match | Status |
|---|---|---|---|---|
| `index.html` | `public/index.html` | 996,026 B | **TRUE** | **VERIFIED** |
| `bhu_loka_cyber_dashboard.html` | `public/bhu_loka_cyber_dashboard.html` | 996,026 B | **TRUE** | **VERIFIED** |
| `bhu_loka_leafmap_interactive.html` | `public/bhu_loka_leafmap_interactive.html` | 90,765 B | **TRUE** | **VERIFIED** |
| `Assets/vendor/bhu_loka_urban_studio.js` | `public/Assets/vendor/bhu_loka_urban_studio.js` | 281,084 B | **TRUE** | **VERIFIED** |
| `Assets/vendor/bhu_loka_agri.js` | `public/Assets/vendor/bhu_loka_agri.js` | 124,746 B | **TRUE** | **VERIFIED** |
| `Assets/vendor/bhu_loka_2d_layer_panel.js` | `public/Assets/vendor/bhu_loka_2d_layer_panel.js` | 31,437 B | **TRUE** | **VERIFIED** |
| `Assets/vendor/bhu_loka_ml_inference.js` | `public/Assets/vendor/bhu_loka_ml_inference.js` | 31,633 B | **TRUE** | **VERIFIED** |
| `CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html` | `public/CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html` | 41,241 B | **TRUE** | **VERIFIED** |

*Conclusion*: All root and deployed files are synchronized.

### 1.3 Firebase Hosting Configuration (`firebase.json`)
- **Public Folder**: `"public"`
- **Default Catch-All Rewrite**: `"destination": "/index.html"` for `"**"`
- **Leaflet 2D Workstation Rewrite**: `"source": "/2d" -> "destination": "/bhu_loka_leafmap_interactive.html"`
- **Pitch Deck Presentation Rewrite**: `"source": "/presentation" -> "destination": "/BHU_LOKA_Presentation_Amour_Hoffen.html"`
- **Cache-Control Headers**: `no-cache, no-store, must-revalidate` for HTML, JS, and CSS; `max-age=86400` for images and static assets.

---

## 2. HOST RUNTIME & SCIENTIFIC LIBRARIES (VERIFIED)

The host Python runtime was inspected directly on 2026-11-20T18:46:17:
- **Python Version**: `3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025) [MSC v.1944 64 bit (AMD64)]`
- **Shapely**: `2.2.0` (C-GEOS planar geometric operations)
- **PyProj**: `3.8.0` (PROJ coordinate transformations, UTM auto-projections)
- **Rasterio**: `1.5.2` (GDAL raster I/O, COG windowing, vector shape extraction)
- **SciPy**: `1.16.3` (Morphological binary opening/closing, spatial filters)
- **NumPy**: `2.1.3` (Multi-dimensional array mathematics)
- **FastAPI**: `0.115.5` (ASGI microservices)
- **Pydantic**: `2.13.5` (Data validation and type safety)

---

## 3. AUTOMATED TEST SUITE EXECUTION EVIDENCE (VERIFIED)

### 3.1 Targeted Scientific Microservice Suites (`25 / 25 Passed`)
Command executed:
```powershell
pytest tests/test_site_analytics_engine.py tests/test_multi_source_extraction.py tests/test_railway_mask_and_spatial_mesh.py tests/test_flood_intel_and_cropper.py -v
```
**Measured Output**: `25 passed in 14.72s` (Exit code 0).

Individual Test Evidence:
1. `tests/test_site_analytics_engine.py`:
   - `test_health_endpoint`: **PASSED** (Verifies FastAPI `/health` returns `200 OK`, `status: HEALTHY`)
   - `test_utm_epsg_pan_india`: **PASSED** (Verifies UTM zone mapping for Indian longitudes: $68^\circ\text{E} \to \text{EPSG:32642}$, $85^\circ\text{E} \to \text{EPSG:32645}$)
   - `test_imagery_search_endpoint`: **PASSED** (Verifies STAC catalog query logic and date filtering)
   - `test_site_analysis_endpoint`: **PASSED** (Verifies LULC mask generation, vectorization, and metric area calculation)
   - `test_change_detection_endpoint`: **PASSED** (Verifies bi-temporal transition matrix and net area calculations)
   - `test_morphological_noise_cleaning`: **PASSED** (Verifies SciPy `binary_opening`/`binary_closing` removes sub-pixel raster noise)
2. `tests/test_multi_source_extraction.py`:
   - `test_extraction_service_instance`: **PASSED** (ExtractionService class initialization)
   - `test_polygon_iou_calculation`: **PASSED** (Turf/Shapely geodesic intersection calculation)
   - `test_spatial_chunking_grid_for_large_aoi`: **PASSED** (Grid decomposition for large bounding boxes)
   - `test_density_modes_and_source_tagging`: **PASSED** (Strict OSM vs Balanced Open Buildings tagging)
   - `test_rajendra_nagar_patna_before_after_comparison`: **PASSED** (AOI clipping consistency)
   - `test_completeness_report_zero_fake_data`: **PASSED** (Validates zero fabricated coordinates in output)
3. `tests/test_railway_mask_and_spatial_mesh.py`:
   - `test_watermark_free_basemaps`: **PASSED** (Verifies compliant basemap URLs)
   - `test_railway_and_road_anti_hallucination_in_building_generators`: **PASSED** (Verifies corridor buffer logic)
   - `test_circle_aoi_support`: **PASSED** (Circular geodesic polygon generation)
   - `test_dual_mode_spatial_mesh`: **PASSED** (Flat grid vs 3D elevation mesh)
   - `test_html_ui_controls`: **PASSED** (Verifies DOM control elements)
4. `tests/test_flood_intel_and_cropper.py`:
   - `test_flood_intel_js_exists_and_parses`: **PASSED** (`bhu_loka_flood_intel.js` AST parse)
   - `test_research_data_empirical_metrics`: **PASSED** (Verifies calibrated backscatter thresholds)
   - `test_dashboard_html_model_intel_integration`: **PASSED** (Dashboard script imports)
   - `test_dashboard_html_pan_india_cropper_features`: **PASSED** (Pan-India bounding box calculations)
   - `test_calibrated_dem_synthesizer_output`: **PASSED** (Copernicus DEM height normalization)
   - `test_sovereign_command_dock_spectral_legend_and_presentation`: **PASSED** (Legend DOM checks)
   - `test_area_flood_prediction_modal_and_endpoint`: **PASSED** (Pure-NumPy vector DB fallback check)
   - `test_3d_in_map_flood_visualizer_and_hud`: **PASSED** (3D in-map HUD parameters)

### 3.2 Full Repository Pytest Suite Run (`53 Passed, 5 Failed`)
Command executed:
```powershell
pytest tests/
```
**Measured Output**: `53 passed, 5 failed in 31.54s` (Exit code 1).
- **5 Failures Diagnostic**: All 5 failures occurred inside `tests/test_e2e_workstation.py`:
  - `test_tier1_f1_vscode_activity_bar_navigation`: Fails because test asserts presence of legacy button `#act-btn-flood`, which was previously removed.
  - `test_tier1_f2_clean_top_bar_branding_and_search`: Fails because test expects `<header>` tag; `index.html` uses `<nav id="top-command-header">`.
  - `test_tier1_f5_persistent_collapsible_time_machine`: Fails because test asserts `#tm-slider` min is `-3000`, while current markup has `-50000`.
  - `test_tier1_f6_design_system_tokens`: Fails because test expects CSS token `--bg-void`; `bhu_loka_theme.css` uses `--bg-canvas`.
  - `test_tier2_reduced_motion_css_token_clamping`: Fails because `@media (prefers-reduced-motion)` block was in `index.html` inline styles rather than `bhu_loka_theme.css`.

*Significance*: Zero scientific pipeline tests failed. The 5 failures are layout assertion regressions from an earlier UI refactoring pass, which will be updated in Phase 1.

---

## 4. JAVASCRIPT STATIC SYNTAX VERIFICATION (VERIFIED)

Executed `node --check` across all platform vendor scripts on 2026-11-20T18:45:54:
```powershell
node -c Assets/vendor/bhu_loka_urban_studio.js      # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_2d_layer_panel.js       # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_agri.js                 # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_location_engine.js      # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_india_intel.js          # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_ml_inference.js         # EXIT: 0 (PASS)
node -c Assets/vendor/bhu_loka_flood_intel.js          # EXIT: 0 (PASS)
```
**Result**: `ALL_JS_SYNTAX_CHECK_PASS = TRUE` (0 syntax errors).

---

## 5. CODE-LEVEL DISCLOSURES & REPRODUCIBLE UI DIAGNOSTICS

### 5.1 Land Intelligence Studio Black Screen Bug (Screenshot 2)
- **File**: `Assets/vendor/bhu_loka_urban_studio.js:3025-3035`
- **Code Reference**:
  ```javascript
  this._renderLayerCatalogue();
  const mapEl = document.getElementById('urban-leaflet-map');
  if (mapEl && !this.leaflet && typeof L !== 'undefined') {
    this.leaflet = new UrbanLeafletEngine(mapEl, (bounds, gj) => this.extractForBounds(bounds, this.activeSite.name, gj));
    this._bindSearch();
  }
  ```
- **Reproducible Steps**:
  1. Open `index.html` in browser.
  2. Click `LAND STUDIO` button in top navigation bar (`bhuNavTo('land-studio')`).
  3. Modal `#bhu-urban-studio-modal` transitions from `display: none` to `display: flex`.
  4. The Leaflet map container `#urban-leaflet-map` initializes while its rendered dimensions are 0x0 pixels.
  5. Result: Map tiles fail to load; center viewport appears as a blank black rectangle (exactly as seen in user screenshot 2).
- **Diagnostic Remedy (Phase 4)**: Inject `setTimeout(() => { if (this.leaflet && this.leaflet.map) this.leaflet.map.invalidateSize(); }, 150);` upon modal open and tab switch.

### 5.2 3D Globe Coordinate Pin Drift on Rotation (Screenshot 8 / 10)
- **File**: `index.html:9300-9420`
- **Code Reference**: `updateMarkerPositions()`
- **Reproducible Steps**:
  1. Open `index.html` at default 3D World view.
  2. Observe landmark pins (e.g. Patna, Hyderabad, Delhi) on the 3D globe.
  3. Click and drag mouse horizontally to rotate the Three.js Earth sphere.
  4. Result: The pins move across screen space using unconstrained CSS transforms rather than staying fixed to their geodetic latitude/longitude surface coordinates on the rotating sphere mesh.
- **Diagnostic Remedy (Phase 1)**: Recalculate 3D geodetic coordinates to camera frustum projection every frame inside the Three.js animation loop:
  ```javascript
  const screenPos = landmarkVector3.clone().project(camera);
  const x = (screenPos.x * 0.5 + 0.5) * canvasWidth;
  const y = (-screenPos.y * 0.5 + 0.5) * canvasHeight;
  markerEl.style.transform = `translate3d(${x}px, ${y}px, 0)`;
  markerEl.style.display = screenPos.z < 1.0 && landmarkVector3.dot(camera.position) > 0 ? 'block' : 'none';
  ```

### 5.3 Reality of Current ML Inference Implementation
- **File**: `Pipelines/bhu_loka_site_analytics_api.py:140-216`
- **Code Reference**: `synthesize_geospatial_raster()`, `run_segformer_inference()`
- **Code Inspection Finding**:
  ```python
  def synthesize_geospatial_raster(bounds: BoundingBox, dim: int = 128) -> Dict[str, Any]:
      seed = int((abs(c_lat) * 1000 + abs(c_lon) * 100) % 65535)
      rng = np.random.default_rng(seed)
      ndvi = np.clip(0.35 + 0.45 * np.sin(grid_lat * 250) * np.cos(grid_lon * 250) + rng.normal(0, 0.05, (dim, dim)), -0.2, 0.9)
      ...
  ```
  The function `run_segformer_inference()` currently operates on synthetic multi-spectral arrays generated via deterministic spatial coordinates (`synthesize_geospatial_raster`) combined with multi-spectral threshold rules.
- **Status Classification**:
  - The API structure, endpoint schema, auto-UTM projection, and Shapely/Rasterio vectorization are **`VERIFIED`**.
  - The deep neural network weights (`SegFormer-B0` / `Prithvi-EO`) are **`PROPOSED`**.
  - Accuracy metrics ($mIoU = 0.842$, $F_1 = 0.912$) previously shown in UI templates are **`PROPOSED BENCHMARKS`** and must not be presented as achieved operational performance.

---

## 6. PHASE 0 CONCLUSION

This Evidence Report establishes the empirical, reproducible truth of the BHU LOKA repository. All scientific inaccuracies, legal exaggerations, and unverified performance claims have been eliminated from the planning baseline.

Application code has NOT been modified. The repository is ready for Phase 1 execution upon your explicit approval.
