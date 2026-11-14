# BHU LOKA (भूलोक) — Low-Level Design (LLD, R0 / R0.1 Aligned)

**Document ID:** `BHU-LLD-R0`  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope Boundary:** Software-Only modules (IoT hardware, wearables, and physical sensor firmware are **OUT OF CURRENT SCOPE**)  

---

## 1. SQLite Schema (`Data/01_Boundaries/bhu_loka_india_intel.sqlite`)

Managed by `Pipelines/bhu_loka_india_db_setup.py` via `ensure_normalized_schema()` and accessed safely via `@contextmanager def _get_conn()` inside `Pipelines/bhu_loka_india_intel.py` (deterministic `commit()`, `rollback()`, and `close()` in `finally:` preventing Windows file locks).

| Table | Key Columns & Purpose | Verified R0 Count |
| :--- | :--- | :--- |
| `states_uts` | `state_code` (PK), `name_en`, `unit_type` (`State` \| `Union Territory`), `hierarchy_schema_json`, `bbox_*`, `geom_geojson` | `36` (`28` States + `8` UTs) |
| `admin_units` | `unit_id` (PK), `state_code`, `parent_id`, `level_depth`, `level_type`, `level_label_state_specific`, `stable_id`, `verified_flag`, `source_attribution` | `36` L1, `724` L2, `2,180` verified L3 (`98` `'n.a.'` rows inactive at `verified_flag=0`) |
| `idx_admin_rtree` | SQLite R-tree (`id`, `min_lon`, `max_lon`, `min_lat`, `max_lat`) mapped via `rowid_rtree` | Indexed |
| `admin_aliases` | `alias_id`, `target_id`, `target_type`, `alias_name`, `language_code` | Active multilingual search index |
| `city_locations` | `city_id`, `name_en`, `state_code`, `district`, `is_capital`, `settlement_class`, `latitude`, `longitude` | `43` settlements & capitals |
| `land_record_portals` | `state_code`, `ror_portal_url`, `bhunaksha_portal_url`, `revenue_dept_url`, `direct_api_status`, `integration_notes` | `36` DILRMP official portal records |
| `land_parcels` | Composite scoped storage (`state_code`, `district_name`, `circle_name`, `mauza_name`, `khata_no`, `khesra_no`, `plot_no`, `ulpin`) | `0` fabricated records |
| `police_stations` | `station_id`, `station_name`, `district`, `boundary_status`, `official_source`, `latitude`, `longitude` | Official Patna register + Overpass |
| `public_cctv_cameras` | Strict 6-status taxonomy (`LIVE`, `PUBLIC LINK`, `AUTHORIZED ACCESS REQUIRED`, `OFFLINE`, `UNAVAILABLE`, `NOT VERIFIED`) | Authorized public nodes only |
| `local_news_items` | `news_id`, `headline`, `publisher`, `publication_time`, `language_code`, `geographic_precision`, `news_category`, `lat`, `lon` | Official PIB EN/HI + NDMA CAP |
| `osm_spatial_cache` | `cache_key`, `payload_json`, `expires_epoch` (30-min TTL; `ERROR`/`UNAVAILABLE` never inserted) | Clean (`0` mock rows) |

---

## 2. Core Python Module Contracts

### 2.1 `Pipelines/bhu_loka_india_intel.py`
- **`_wait_overpass_slot(endpoint)`**: Acquires `_OVERPASS_LOCK` solely to compute and reserve monotonic spacing (`>= 0.5s` per endpoint), sleeps outside mutex.
- **`_fetch_overpass_elements(query_body, timeout=5.0, max_retries=2)`**: Queries Overpass endpoints with `HTTP 429`/`503` exponential backoff and `Retry-After` cap (`<= 5.0s`).
- **`get_gis_layer(layer_id, lat, lon, radius_km=10.0, refresh_live=False, ...)`**: Returns normalized GeoJSON `FeatureCollection` + `items` + `status` (`LIVE`, `CACHED`, `VERIFIED_LOCAL`, `EMPTY`, `UNAVAILABLE`).

### 2.2 `Pipelines/bhu_loka_location_engine.py`
- **`resolve_location_context(lat, lon, place_name, radius_km, timeout)`**: Exposes canonical `in_india`, `state_code`, `state`, `district`, `crs="EPSG:4326"`, backed by `_LOCATION_CACHE_LOCK`.
- **`_build_infrastructure_module(...)` (Module 10)**: Queries `get_gis_layer("road_closures")` and `get_gis_layer("traffic_advisories")` in parallel via `ThreadPoolExecutor(max_workers=2)`.
- **`_build_hospitals_amenities_module(...)` (Module 11)**: Queries `get_gis_layer("hospitals")` and maps honest `facilities` and `UNAVAILABLE` reasons without hardcoded hospital templates.
- **`fetch_universal_location_intelligence(...)`**: Parallel ThreadPool Stage 1 (context, terrain, weather/rainfall/soil, hydro, air) + Stage 2 GIS (`infra`, `hospitals`, `cameras`, `news`) returning all `15` modules.

### 2.3 `Models/04_Hybrid_RAG/enterprise_rag_app/rag/`
- **`retriever.py`**: Hybrid BM25 + FAISS (`all-MiniLM-L6-v2` cached `.npz` or TF-IDF SVD fallback) fused via Reciprocal Rank Fusion (`k=60`).
- **`generator.py` (`LocalSovereignGenerator`)**: Formats context-grounded structured synthesis from `retrieved_docs`.
- **`main.py`**: Exposes `/api/v1/query`, running `RagasEvaluator.compute_all_metrics()` + `BhuLokaGuardrails.evaluate_output()`.

---

## 3. Frontend Synchronization Contract (`Assets/vendor/`)

- **`window.BhuLokaLocationEngine`**: Emits canonical coordinate updates (`subscribe()`), builds 15+2 module cards, and uses rose/amber indicators (`#fb7185`) when values or APIs are `UNAVAILABLE`.
- **`window.BhuLokaIndiaIntel`**: Preserves input focus, text selection, and `#bhu-ii-body` scroll offset across asynchronous `renderWorkspace()` redraws, and renders all `12` GIS layers onto Leaflet (`L.geoJSON`) and Three.js (`THREE.Group`).
