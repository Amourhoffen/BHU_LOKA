# BHU LOKA (भूलोक) — Scientific Workstation Design System (`DESIGN.md`)

**Document ID:** `BHU-DESIGN-v1.0`  
**Status:** Design Specification for Visual Quality Gate (Pending Owner Direction Approval Before Implementation)  
**Scope:** Unified UI/UX Design System across Earth Intelligence (`3D` & `2D`), India Location Intelligence (`A–F`), Precision Agriculture, ClimateGuard / Human Safety, Urban / Site Studio, and Dual-Agent AI Terminal.  
**Team Roles:** Prince Kumar (Owner, IIT Patna), Pallav Rustogi (Supervisor), Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur).

---

## 1. Visual Reference Synthesis & Selected Direction

### 1.1 Reference Archetypes Studied (`Bhu Loka - भूलोक/Refrence Image/`)

1. **NASA Worldview & Eyes on the Earth:** Full-bleed Earth/Map primary surface (`>= 75%` viewport), compact top utility strip, docked left layer drawer with grouped toggles/eyes and attribution, and a calibrated bottom timeline/UTC scrubber.
2. **SAGA GIS Multi-Pane Desktop:** Strict multi-pane scientific geometry — workspace/module tree on the left, synchronized 2D + 3D views in the center, structured `Key / Value` parameter inspector on the right, and execution/provenance + CRS coordinate strip along the bottom.
3. **Precision Agriculture GIS (`AgriMap` / Difference Map):** Orthophoto/satellite imagery as hero, thin `1px` parcel polygons, discrete stepped choropleth ramp docked cleanly at the bottom edge, tabular stats (`Min / Max / Avg / StdDev / Area ha`), and quiet collapsible inspector rails.
4. **3D Digital Urban & Orbital Twins:** Solar-azimuth and shadow overlays, camera telemetry (`Lat / Lon / Elev / Bearing`), orthogonal callouts, zero floating neon clutter.
5. **3D Thermal & Bio-Safety Visualization:** Monochrome slate-navy figure background keeping `100%` of the color budget on scientific measurement heatmaps, calibrated color bars (`°C`, `m/s`, `WBGT`), and leader-line callouts.
6. **Anti-Patterns Explicitly Rejected from Concept Mockups:** Glowing oval pills (`shadow-[0_0_20px...]`), sparkle icons on AI inputs, oversized `24px` bento cards, pastel widgets, repeated `"PRO / BETA"` status pills, and fake decorative sparklines.

### 1.2 Chosen `/unslop` Direction Specification ("Cartographic Instrument")

- **Product:** BHU LOKA is an integrated geospatial intelligence and Earth-observation workstation unifying 3D Three.js orbital/DEM views, 2D Leaflet satellite/GIS layers, India administrative/street intelligence (`A–F`), precision agriculture, and provenance-grounded AI analysis.
- **Character:** Quiet, high-precision laboratory instrument built for researchers, planners, and field analysts — dense, calm, unambiguous, and subordinate to real terrain and telemetry.
- **World:** Nocturnal telemetry obsidian (`#06090e` to `#101724`) framed by cool slate hairlines, inspired by mission-control terminals, NASA Worldview, and SAGA GIS desktop geometry.
- **Moments:** Orbiting the 3D globe or panning 2D NASA GIBS / Sentinel-2 imagery uninterrupted while docked Explorer and Inspector panels stay aligned beside it, clicking any ward or parcel to synchronize telemetry, and watching honest backend/API provenance update live.
- **Signature:** Zero glowing borders and zero card soup — docked split-pane panels divided by crisp `1px` hairlines and `8px` pointer splitters, tabular coordinates anchored at the bottom status bar, and scientific color reserved strictly for Earth layers and honest telemetry state.

---

## 2. Color Tokens (Single Neutral Obsidian Ramp + Calibrated Accents)

All surfaces share one cool-slate obsidian neutral ramp so satellite imagery, DEM relief shading, and GIS vector layers dominate visually.

### 2.1 Surface & Border Tokens

| Token Name | Value | Usage |
| --- | --- | --- |
| `--bg-void` | `#05080c` | WebGL2 canvas backdrop, deepest map background |
| `--bg-canvas` | `#06090e` | Application shell background & scroll tracks |
| `--bg-inset` | `#070b12` | Inputs, code/log boxes, plot backgrounds, recessed metrics |
| `--bg-panel` | `#0b1019` | Primary docked rails, toolbars, drawer bodies |
| `--bg-elevated` | `#101724` | Sub-cards, active tab fills, table headers, interactive buttons |
| `--bg-hover` | `#162032` | Interactive hover surface step |
| `--border-hairline` | `rgba(148, 163, 184, 0.14)` | Default panel dividers and table row hairlines |
| `--border-strong` | `rgba(148, 163, 184, 0.24)` | Active control edges, input resting border, splitter thumb |
| `--border-focus` | `#38bdf8` | Keyboard `:focus-visible` ring (`1.5px` solid) |

### 2.2 Text Hierarchy Tokens (3 Roles Max)

| Token Name | Value | Contrast on `#0b1019` | Usage |
| --- | --- | --- | --- |
| `--text-primary` | `#f8fafc` | `17.5:1` | Headings, active labels, metric values, primary chat text |
| `--text-secondary` | `#94a3b8` | `6.6:1` | Descriptions, metadata values, inactive tabs, axis text |
| `--text-muted` | `#64748b` | `3.8:1` | Subtle separator punctuation, disabled text (minimum `10px`, never primary labels) |

### 2.3 Accent & Scientific Status Tokens (Semantic Honesty Contract)

| Token Name | Value (Bg/Border) | Text Ink | Meaning & Strict Rule |
| --- | --- | --- | --- |
| `--accent-primary` | `#38bdf8` | `#05080c` / `#7dd3fc` | Selected workspace item, focused coordinate target, active primary CTA (max 1–2 per screen) |
| `--state-verified` | `#10b981` | `#6ee7b7` | `VERIFIED_LOCAL`, `LIVE`, `FASTAPI :8000 CONNECTED`, Safe Elevation Ridge (`>52.0m`), Healthy NDVI (`>=0.66`) |
| `--state-warning` | `#f59e0b` | `#fcd34d` | `EMPTY`, `PARTIAL_METADATA_ONLY`, `API OFFLINE · LOCAL`, Ponding (`48–52m`), Moderate NDVI (`0.40–0.66`) |
| `--state-unavailable` | `#f43f5e` | `#fb7185` | `ERROR`, `UNAVAILABLE`, `OFFLINE`, Critical Flood Sink (`<46.0m`). **Mandatory:** Never substitute green for unavailable feeds. |
| `--state-idle` | `#94a3b8` | `#cbd5e1` | `IDLE` (unfetched/unchecked GIS layer), provenance tags (`EPSG:4326`) |

### 2.4 Calibrated Quantitative Legend Ramps (Map / 3D Overlays Only)

- **Elevation / Patna Flood Relief:** `<46.0m` (`#f43f5e`) · `46–48m` (`#f97316`) · `48–52m` (`#f59e0b`) · `>52.0m` (`#10b981`) · `49.5m Ganga Lock` (`#38bdf8`)
- **NDVI / Crop Vigor (Sentinel-2 L2A):** `<0.20` (`#f43f5e` Very Low) · `0.20–0.40` (`#fb923c` Low) · `0.40–0.66` (`#facc15` Moderate) · `0.66–1.00` (`#10b981` High)
- **Thermal / Environmental WBGT (Phase 2 Ready):** `<=30°C` (`#38bdf8`) -> `32°C` (`#22c55e`) -> `34°C` (`#eab308`) -> `37°C+` (`#f43f5e`)

---

## 3. Typography

- **UI / Prose / Navigation Sans:** `'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif`
- **Coordinates / Numeric Telemetry / Provenance Mono:** `'IBM Plex Mono', 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace` with mandatory `font-variant-numeric: tabular-nums`.
- **Weights Allowed:** `400` (Regular), `500` (Medium), `600` (Semibold). Weights `800`/`900` are prohibited.
- **Casing Rule:** Use clean Title Case or Sentence Case for panel headers, quick prompts, and module tabs (`"Live Hydromet & River Flow"`, `"A. Admin Explorer"`). **Avoid** wide-tracked (`letter-spacing > 0.08em`) all-caps labels on buttons or prose headers.
- **Type Scale (Strict Minimum Floor `10px`):**
  - `14px` / `600`: Brand wordmark (`BHU LOKA / भूलोक`)
  - `13px` / `600`: Drawer / View titles
  - `12px` / `400–500`: Body prose, AI responses, form inputs, table body cells
  - `11px` / `500`: Left/Right rail section headers, active GIS controls, table headers
  - `10px` / `500`: Hard floor — coordinates, timestamps, provenance tags, chart axes, legend ticks. **Zero `8px` or `9px` text anywhere.**

---

## 4. Spacing, Radii & Grid System

### 4.1 Strict 4px Spacing Scale

Only multiples of `4px` are permitted: `4px` (`gap-1`), `8px` (`gap-2` / `p-2`), `12px` (`gap-3` / `p-3`), `16px` (`p-4`), `24px`, `32px`, `48px`. Arbitrary off-grid sizes (`7px`, `13px`, `31px`) are disallowed.

### 4.2 Nested Radius Math

- `2px`: Internal indicator bars, progress ticks
- `4px`: Buttons, inputs, inline source chips, sub-inset cards
- `6px`: Primary docked panels (`#left-rail` sections, `#right-rail`, `#viewport-panel`)
- `8px`: Top-level detached overlays/modals when unavoidable (`1px` solid border, zero Gaussian halo)
- `9999px` (`rounded-full`): Allowed ONLY on `6px–8px` circular status indicator dots and range slider thumbs — **never** on buttons, search inputs, or nav tabs.

### 4.3 Desktop Workstation Grid (`>= 1024px`, `100vw x 100vh`, `overflow: hidden`)

```
+-------------------------------------------------------------------------+
| ROW 1: Top Command Bar (44px fixed) — Wordmark | Search | Modes | API   |
+-------------------------------------------------------------------------+
| ROW 2: Module & Spatial Nav Ribbon (36px fixed, single-line overflow-x) |
+---------------+---+---------------------------------+---+---------------+
| LEFT DOCK     | R | CENTER VIEWPORT                 | R | RIGHT DOCK    |
| 280–340px     | E | flex: 1 (min 60% width default; | E | 300–360px     |
| Collapsible   | S | >= 85% in Theater / Focus Mode) | S | Collapsible   |
| (Explorer,    | I | [3D Earth / DEM / SAR] OR       | I | (Inspector +  |
|  12 GIS Layers| Z | [2D Leaflet Satellite/GIBS/OSM] | Z |  Dual-Agent   |
|  & A–F Admin) | E | Floating minimal controls       | E |  RAG Chat)    |
+---------------+---+---------------------------------+---+---------------+
| ROW 4: Bottom Status & Provenance Strip (28px fixed)                    |
| CRS | Lat/Lon | Elev | Active Layer Scale/Date | Sync Status | UTC Time |
+-------------------------------------------------------------------------+
```

---

## 5. Panel & Component Specifications

### 5.1 Panel Behavior (Dock-First Architecture)

- **No Floating Pile-Ups:** India Intelligence (`A–F`), Precision Agriculture (`NDVI/Farm`), and Telemetry HUD must dock cleanly into dedicated Left/Right workspace rails or replace rail tab content on desktop (`>= 1024px`), preventing modals from covering the central Earth/Map viewport.
- **Splitter Resizing:** `8px` pointer-drag splitters (`#left-resizer`, `#right-resizer`) resize Left (`240–420px`) and Right (`260–440px`) docks in place without modifying camera zoom or target center (`ResizeObserver` -> `requestAnimationFrame` -> renderer `setSize` / `map.invalidateSize()`).
- **Persistence:** Store `{ leftOpen, rightOpen, leftWidth, rightWidth, theaterMode, activeLeftTab }` in `localStorage` (`bhu_loka_workspace_prefs_v1`).
- **Focus Stability:** Every `input`, `select`, and `textarea` enforces `scroll-margin: 0`; searching or toggling panels must never trigger root document scroll (`scrollY === 0`).

### 5.2 Buttons

- **Default Secondary:** `height: 28px` (compact toolbar) or `32px` (form), `bg: #101724`, `border: 1px solid rgba(148,163,184,0.20)`, `text: #e2e8f0`, `border-radius: 4px`, hover `bg: #162032`.
- **Selected / Active Mode:** `bg: rgba(56, 189, 248, 0.14)`, `border: 1px solid rgba(56, 189, 248, 0.45)`, `text: #7dd3fc`.
- **Primary Action (Max 1–2 visible):** Solid `#38bdf8` fill, `#05080c` text, `font-weight: 600` (e.g., `2D Earth` / `3D Workstation` or Search `Go`).
- **Destructive Action:** `bg: rgba(244, 63, 94, 0.12)`, `border: rgba(244, 63, 94, 0.40)`, `text: #fb7185`.

### 5.3 Inputs & Selects

- `height: 30px`, `padding: 0 10px`, `bg: #070b12`, `border: 1px solid rgba(148,163,184,0.24)`, `border-radius: 4px`, `font-size: 11px` mono/sans.
- Placeholder: Concise noun phrase (`"Place or lat, lon"`, `"Ask spatial query"`), color `#64748b`.
- Custom chevron/select contrast `#cbd5e1` on `#070b12`.

### 5.4 Tables (Risk Matrices, Zone Stats, Search Hits)

- Full-width borderless container inside inset panel, header row `26px` high, `10px` mono `#94a3b8`, `border-bottom: 1px solid rgba(148,163,184,0.18)`.
- Data rows `28px` high (`padding: 4px 8px`), `1px` bottom hairline `rgba(148,163,184,0.10)`, hover `bg: #162032`.
- Units placed in header (`Elev (m)`, `Area (ha)`, `ULSI`); numeric cells right-aligned with `tabular-nums`.

### 5.5 Scientific Charts (Apache ECharts / SVG Standard)

- Canvas background `#070b12`; zero gradient bar fills or neon glow shadows.
- Gridlines dashed `1px` `rgba(148,163,184,0.10)`; axis labels `10px` mono `#94a3b8`.
- Max `3` series per chart using distinct accessible hues (`#38bdf8`, `#10b981`, `#f59e0b`; rose `#f43f5e` strictly for threshold breach).
- Must carry dataset source + acquisition timestamp caption beneath or inside legend.

### 5.6 GIS Layer Controls (12-Layer + EO Raster Stack)

- Single compact row height (`32px–44px`): `14px` checkbox + `8px` layer color indicator + truncated layer title + monospace `STATUS (COUNT)` readout (`VERIFIED_LOCAL`, `LOADING`, `EMPTY`, `IDLE`, `ERROR`).
- Secondary control line (expandable or compact): `Opacity` slider + `Zoom` + `Info` (schema/provenance popover).
- Concurrency cap: max `2` active network Overpass layer fetches simultaneously so HTTP/1.1 browser sockets never saturate health checks.

### 5.7 Map Overlays & Annotations

- **Vector Parcels / Boundaries:** `1px–1.5px` crisp strokes without blurred drop halos.
- **3D Scene Leader Callouts:** `1px` orthogonal SVG/CSS hairlines `#94a3b8` terminating at a sharp `4px`-radius label box `#0b1019` with `1px` border.
- **Floating Overlays Cap:** At most 2 non-overlapping corner HUDs over the map canvas (top-right compact zoom/layer toggle; bottom-left compact scale/legend). Telemetry drawers stay in Left/Right docks.

### 5.8 Icons, Copy, Motion, Responsive & Accessibility

- **Icons:** Inline geometric SVG (`16x16` or `14x14`, `stroke-width: 1.5`, `currentColor`). Zero emojis in any control, header, log, table, or badge.
- **Copy:** Plain operational terminology (`"FastAPI :8000"`, `"API Offline · Local"`, `"No verified public CCTV feed"`). Zero exclamation marks or promotional buzzwords.
- **Motion:** Functional transitions only (`width`/`opacity` `200ms cubic-bezier(0.4, 0, 0.2, 1)` on side rails; `140ms ease-out` color shift on buttons). Zero `animate-pulse` on static tags; zero `hover:scale`. Honor `@media (prefers-reduced-motion: reduce)`.
- **Responsive Breakpoints:**
  - `>= 1280px`: Full 3-pane locked workstation (`Left + Center + Right`).
  - `1024–1279px`: Compact `268px` rails; opening deep Intel/Agri inspector swaps rail tab rather than overlaying Center.
  - `768–1023px` (Tablet): Center map `>= 52vh`; slide-over/stacked inspector tabs cleanly below or toggled from header.
  - `< 768px` (Mobile): Single-column scroll-safe layout, sticky/top `48vh` interactive canvas, concise action strip.
- **Accessibility:** Keyboard `Tab` navigation across every nav/layer/search control, `1.5px` `#38bdf8` `:focus-visible`, `Escape` dismisses active modal/floating overlay, `aria-expanded` on toggles, WCAG AA text contrast throughout.

---

## 6. Technical Library Compatibility Audit & Recommendation Matrix

BHU LOKA currently runs a **zero-build static frontend** (`bhu_loka_cyber_dashboard.html` + `bhu_loka_leafmap_interactive.html` + `Assets/vendor/*.js`), bundled offline with **Tailwind CSS JIT CDN script (`tailwindcss.js`)**, **Three.js r128 (`three.min.js`)**, **Leaflet 1.9.4 (`leaflet.js`)**, and **satellite.js (`satellite.min.js`)**, served safely by **FastAPI (`main.py`)** and optionally wrapped in **Electron 33 (`BhuLoka_Chromium_App`)**.

| Library Evaluated | Architectural Fit | Compatibility With Current Stack | Recommendation |
| --- | --- | --- | --- |
| **Tailwind CSS (`Assets/vendor/tailwindcss.js`)** | Already bundled offline; drives existing utility layout | **NATIVE (KEEP)** | **KEEP** — Pair with shared `:root` CSS tokens in a single `Assets/vendor/bhu_loka_theme.css` so 3D, 2D, Intel, and Agri share identical colors, spacing, and typography. |
| **shadcn/ui & Radix UI** | Requires React 18/19, TypeScript/JSX compiler & Vite/Next bundler | **INCOMPATIBLE WITHOUT REWRITE** | **DEFER** — Do not rewrite working dashboards into React during Phase 1. Adopt Radix accessibility patterns (focus rings, `Escape`, `aria-expanded`) directly in vanilla components. |
| **Resizable Panel Library (`react-resizable-panels` / `Split.js`)** | `react-resizable-panels` is React-only; vanilla `Split.js` duplicates existing code | **UNNECESSARY OVERHEAD** | **KEEP EXISTING VANILLA SPLITTERS** — Enhance verified `#left-resizer` & `#right-resizer` with `localStorage` persistence and extend cleanly to 2D Leaflet docks. |
| **Apache ECharts (`echarts.min.js`)** | Pure framework-agnostic UMD bundle; built-in dark scientific canvas/SVG axes, zoom/brush, radar/scatter/timeseries | **HIGHLY COMPATIBLE (DROP-IN)** | **RECOMMEND (PHASE 1–3 ADDITIVE)** — Download verified UMD bundle into `Assets/vendor/echarts.min.js` for real NDVI/NDMI/Rainfall/Flood time-series, radar soil charts (as in Agri references), and thermal WBGT curves once backend data series are wired. |
| **MapLibre GL JS & deck.gl** | WebGL2 vector tile & GPU point/extrusion overlay stack | **PARTIAL OVERLAP / MIGRATION RISK** | **HOLD UNTIL PHASE 4 URBAN** — Preserve Leaflet 1.9.4 for NASA GIBS WMTS, Google Satellite, and verified `BhuLokaAgri` draw/edit workflows. Re-evaluate MapLibre+deck.gl only for high-volume 3D urban massing/building footprints when approved. |
| **CesiumJS** | Global 3D Tiles globe (`~5–15 MB` workers + terrain server dependencies) | **HEAVYWEIGHT OVERLAP** | **NOT RECOMMENDED NOW** — Preserves working `Three.js r128` globe + Patna 30m Copernicus DEM + OSM hologram without multi-megabyte bundle bloat or Ion token dependencies. |
| **React Three Fiber** | React reconciliation layer over Three.js | **INCOMPATIBLE WITHOUT REWRITE** | **NOT RECOMMENDED** — Direct `Three.js r128` WebGL2 code already powers the 3D globe, satellites, orbital rings, and Patna DEM/Hologram and can host Phase 2 3D human thermal visualization directly. |
