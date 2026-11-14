# BHU LOKA (भूलोक) — UI / UX Design Index (R0 / R0.1)

**Document ID:** `BHU-UIUX-R0`  
**Verification Date:** 2026-11-12  

## Team & Responsibilities
- **Prince Kumar** (Project Owner, IIT Patna): Geospatial web visualization implementation (`bhu_loka_cyber_dashboard.html`, `bhu_loka_leafmap_interactive.html`, `bhu_loka_india_intel.js`, `bhu_loka_agri.js`, `bhu_loka_location_engine.js`).
- **Pallav Rustogi** (Project Supervisor): Review and oversight.
- **Payal Priyadarshini** (UI/UX Designer, IIITDM Jabalpur, 1st Semester): Recognized UI/UX designer for BHU LOKA; no frontend or backend code authorship is invented or attributed beyond her official UI/UX design role.

## Verified Software UI Surfaces
1. **3D Sovereign Tactical HUD:** `bhu_loka_cyber_dashboard.html` (Three.js r128, Earth globe with NASA Blue Marble texture and live CelesTrak orbital satellites, India 36-State, Bihar 38-District, and Patna DEM/SAR relief modes, `INDIA LOCATION & STREET INTELLIGENCE` navigation, telemetry drawer, and link to `AGRICULTURE INTELLIGENCE (2D)`).
2. **2D Interactive GIS & Precision Agriculture Explorer:** `bhu_loka_leafmap_interactive.html` (Leaflet 1.9.4, verified NASA EOSDIS GIBS WMTS overlays — MODIS Terra True Color, MODIS Terra Daytime LST 1km, and MODIS Terra NDVI 8-Day — plus empirical S1 SAR / GLO-30 DEM / MODIS LST rasters, `BhuLokaIndiaIntel` Modules A–F, and `BhuLokaAgri` interactive farm polygon draw/edit/Satellite/Soil/AI workspace).
3. **Desktop Wrapper:** `BhuLoka_Chromium_App/` (Electron 33 wrapper loading the 3D HUD and invoking `god_eye_hybrid_rag.py`).

## UI Provenance & Integrity Rules
- Never display any satellite tile or layer as NASA data without verified NASA EOSDIS / LaRC / LP DAAC attribution (`NASA EOSDIS GIBS / Worldview`). BHU LOKA claims no NASA partnership or endorsement.
- `UNAVAILABLE` / `ERROR` states MUST display `#fb7185` rose alert styling and explicit unavailability messages, never `#6ee7b7` live green badges.
- Asynchronous refreshes preserve active search inputs, text cursor positions, and drawer scroll offsets.

## UI/UX Craft Pass (Step 4 — Verified R0.2 Polish & Direction 1 Cartographic Instrument)
- **Authoritative Design System (`DESIGN.md` & `Assets/vendor/bhu_loka_theme.css`):** Formalized **Direction 1 — Cartographic Instrument** (`BHU-DESIGN-v1.0`) grounded in SAGA GIS, scientific 3D visualization, precision agriculture, orbital intelligence, and smart-city GIS grammar.
- **Dark Hairline Surface System & Theme Tokens:** Standardized CSS variables in `bhu_loka_theme.css` (`--bg-void: #05080c`, `--bg-canvas: #06090e`, `--bg-inset: #070b12`, `--bg-panel: #0b1019`, `--border-hairline: rgba(148, 163, 184, 0.14)`) with dark thin instrument scrollbars across `bhu_loka_cyber_dashboard.html`, `bhu_loka_leafmap_interactive.html`, `bhu_loka_india_intel.js`, `bhu_loka_location_engine.js`, and `bhu_loka_agri.js`.
- **Dockable Non-Occluding Side Workstations:** Converted `BhuLokaIndiaIntel` (`#bhu-intel-dock-slot`), `BhuLokaLocationEngine` (`#bhu-location-dock-slot`), and `BhuLokaAgri` (`#bhu-agri-dock-slot`) from floating overlays into static non-overlapping desktop side docks (`Scene & Hydromet` | `Explorer (A-F)` and `AI Decision` | `Location HUD` on 3D; collapsible left Explorer and right `Location HUD` | `Agriculture` docks on 2D), with `localStorage` rail width/collapse persistence (`bhu_loka_workspace_prefs_v1`).
- **Unified `28px` Provenance, Coordinate & CRS Footers:** Added `#workstation-footer` (3D) and `#gis-bottom-footer` (2D) displaying live target coordinates, `EPSG:4326` + dynamic northern-hemisphere `UTM 326xx`, zoom/radius, non-error sync routing (`#footer-provenance` / `#gis-footer-provenance`), and live UTC telemetry.
- **Typography, Restraint & Accessibility:** Enforced a `>= 10px` readability floor across all telemetry cards, A–F tabs, and disclaimers; applied `font-variant-numeric: tabular-nums`; set `#gis-legend-card` below Leaflet popups (`z-index: 450`) with toolbar toggling; ensured keyboard `Escape` closes `#sys-modal` and exit fullscreen; and preserved strict `#fb7185` rose unavailability states.
