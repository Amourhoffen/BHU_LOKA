# BHU LOKA (भूलोक) — Phase 1 Workstation Layout & Visual Interface Specification

**Document ID:** `BHU-DESIGN-PHASE1`  
**Status:** Canonical Interface Specification for Milestone 1  
**Target:** Scientific Earth-Observation Workstation  
**Author:** Teamwork Worker (`worker_m1_1`)  
**Date:** 2026-11-14  

---

## 1. Executive Overview & Workstation Metaphor

BHU LOKA is transformed into a high-precision, mission-control scientific Earth-observation workstation inspired by modern IDE (VS Code) geometry and geospatial mission-control suites (NASA Worldview, SAGA GIS, Cesium Ion). The interface subordinates decorative chrome to genuine planetary telemetry, 3D/2D GIS layers, and grounded AI reasoning.

### Key Architectural Tenets:
1. **Activity-Driven Workspace Switching:** A persistent 48px far-left vertical Activity Bar drives workspace focus and high-level domain transitions (3D Earth, Precision Agriculture, SAR Flood Deluge, Thermal Public Health, Solar Ephemeris, Dual-Agent AI).
2. **Clean Sovereign Command Header:** Top utility bar hosts BHU LOKA sovereign branding and the universal location search engine. Redundant top-center navigation pills and in-viewport floating AI prompt overlays are completely eliminated.
3. **Inverted Side Panel Architecture:**
   - **Left Panel (280px–480px, resizable):** Houses the **AI Research Assistant** (Dual-Agent chat feed, prompt inputs, role selectors, and telemetry reasoning).
   - **Right Panel (280px–480px, resizable):** Houses the **Scientific Explorer & Tools** (Scientific Layer Explorer with 6 categories and 15 sensor products, Live Hydromet & River Flow, India Intelligence A–F dock slot, and Location HUD).
4. **Dominant 3D Viewport with Zero-Distortion Resizing:** The central Three.js canvas dynamically claims all remaining space. Staggered `ResizeObserver` and `requestAnimationFrame` debouncing maintain camera projection matrices without aspect-ratio stretching during panel resizing, collapse, and theater mode toggling.
5. **Persistent Collapsible Global Time Machine:** Bottom dock bar allows scrubbing temporal epochs from 3000 BCE to 2026 CE with a dedicated collapse/expand toggle to maximize vertical viewport space when not scrubbing time.

---

## 2. Workstation Layout Structure Diagram

```
+========================================================================================================================+
| TOP COMMAND HEADER (44px fixed, #070b12 glass, border-b: rgba(148,163,184,0.14))                                       |
| [भू BHU LOKA SOVEREIGN | IIT PATNA] [2D Earth] [SAR Hero] ---------- [ Universal Search: Place or lat,lon ] [API] [Theater] [User] |
+====+-------------------------+---+---------------------------------------------------------+---+-----------------------+
| A  | LEFT RAIL: AI ASSISTANT | R | CENTER STAGE: 3D THREE.JS VIEWPORT                      | R | RIGHT RAIL: EXPLORER  |
| C  | (300px-480px, resizable)| E | flex: 1 min-w-0, height: calc(100vh - 116px)            | E | (320px-480px, resiz.) |
| T  |                         | S |                                                         | S |                       |
| I  | [AI Terminal | Insights]| I | [World | India 36 | Bihar 38 | Holo 90m | Universe]     | I | [Scene | A-F | HUD]   |
| V  | ----------------------- | Z | +-----------------------------------------------------+ | Z | --------------------- |
| I  | - Dual-Agent Header     | E | |                                                     | | E | - Hydromet & River    |
| T  | - Role Selectors        | R | |         Interactive 3D Earth / Orbit Mesh           | | R | - 15 Sci GIS Layers   |
| Y  |   (Farmer, Worker, etc) |   | |                 (Three.js r128)                     | |   |   (S1, S2, MODIS, DEM)|
|    | - Cartographic Banner   | 1 | |                                                     | | 2 | - India Intel Dock A-F|
| B  | - Query Stream (#chat)  |   | |                                                     | |   | - Location HUD Slot   |
| A  | - Voice Audio Controls  | 8 | +-----------------------------------------------------+ | 8 | - Satellite Telemetry |
| R  | - Multilingual Form     | p | [Wards Elevation Audit Panel - Collapsible Drawer]      | p |                       |
|    |   (#user-input + RUN)   | x |                                                         | x |                       |
| 48 | - Quick Prompt Chips    |   |                                                         |   |                       |
| px | [◀ Collapse Panel]      |   |                                                         |   | [▶ Collapse Panel]    |
+====+-------------------------+---+---------------------------------------------------------+---+-----------------------+
| COLLAPSIBLE GLOBAL TIME MACHINE (#bhu-time-machine, 24px collapsed / 48px expanded, z-index: 50)                       |
| [▴/▾ Toggle] [ |<<  >  >>| 1x-365x ] -----[ -3000 BCE ============================ 2026 CE ]----- [ LIVE CelesTrak GP ] |
+========================================================================================================================+
| TELEMETRY & PROVENANCE FOOTER (28px fixed, #05080c, border-t: rgba(148,163,184,0.12))                                  |
| Location: Patna · 25.5940°N, 85.1370°E | CRS: EPSG:4326 UTM 32645 | Radius: 10km | Provenance: Copernicus DEM | UTC Clock |
+========================================================================================================================+
```

---

## 3. Design Tokens (Obsidian Cool-Slate System)

All surfaces follow a strict obsidian cool-slate ramp designed to prioritize data legibility and preserve WebGL dark-space contrast.

### 3.1 Surface Tokens
| Token Name | Value | Description & Purpose |
| :--- | :--- | :--- |
| `--bg-void` | `#05080c` | Deep space backdrop, WebGL canvas clear color, deep footer |
| `--bg-canvas` | `#06090e` | Master application background, activity rail background |
| `--bg-inset` | `#070b12` | Inset panels, inputs, search fields, recessed metric displays |
| `--bg-panel` | `#0b1019` | Side rails (`#left-rail`, `#right-rail`), modal container surfaces |
| `--bg-elevated` | `#101724` | Active tabs, button default surfaces, card headers |
| `--bg-hover` | `#162032` | Interactive button hover, selectable row highlights |

### 3.2 Border & Divider Tokens
| Token Name | Value | Description & Purpose |
| :--- | :--- | :--- |
| `--border-hairline` | `rgba(148, 163, 184, 0.12)` | Subtle panel dividers, table horizontal lines |
| `--border-subtle` | `rgba(148, 163, 184, 0.20)` | Resting card borders, tab bar dividing lines |
| `--border-strong` | `rgba(148, 163, 184, 0.35)` | Interactive control boundaries, resizer resting thumbs |
| `--border-focus` | `#38bdf8` | Keyboard focus ring (`1.5px solid #38bdf8`), active tab indicator |

### 3.3 Text Hierarchy Tokens
| Token Name | Value | Contrast Ratio | Usage Rule |
| :--- | :--- | :--- | :--- |
| `--text-primary` | `#f8fafc` | 17.5:1 on `#0b1019` | Main headers, active values, user input, chat text |
| `--text-secondary` | `#94a3b8` | 6.6:1 on `#0b1019` | Secondary labels, descriptions, inactive tabs, captions |
| `--text-muted` | `#64748b` | 3.8:1 on `#0b1019` | Hard minimum 10px floor; timestamps, axis units, delimiters |

### 3.4 Semantic & State Colors
| Token Name | Value | Ink Text | Meaning & Contract |
| :--- | :--- | :--- | :--- |
| `--accent-primary` | `#38bdf8` | `#05080c` / `#7dd3fc` | Active workspace selections, primary CTA buttons |
| `--state-verified` | `#10b981` | `#6ee7b7` | Verified sensor telemetry, connected FastAPI `:8000`, safe zone |
| `--state-warning` | `#f59e0b` | `#fcd34d` | Partial metadata, local fallback cache, flood warning buffer |
| `--state-unavailable` | `#f43f5e` | `#fb7185` | Inactive sensor feed, critical flood inundation, error state |
| `--state-idle` | `#94a3b8` | `#cbd5e1` | Unchecked layer, passive ephemeris, coordinate tags |

---

## 4. Typography System

The workstation uses dual IBM Plex typography with strict tabular alignment for numerical telemetry.

```css
/* Primary UI Prose and Control System */
font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;

/* Numerical Telemetry, Ephemeris, GIS Coordinates, and Provenance */
font-family: 'IBM Plex Mono', 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace;
font-variant-numeric: tabular-nums;
```

### Type Scale Rules
- **18px / 700 / Sans:** Top brand wordmark (`BHU LOKA · भूलोक`).
- **13px / 600 / Sans:** Panel section headers (`Dual-Agent Decision Terminal`, `Scientific Layer Explorer`).
- **12px / 400 / Sans:** Chat dialog, long-form analytical prose, notification bodies.
- **11px / 500 / Mono:** Control inputs, form fields, tab buttons, quick prompt chips.
- **10px / 500 / Mono (Hard Floor):** Satellite TLE ephemeris, GIS coordinates (`25.5940°N, 85.1370°E`), UTC timestamps, status chips. **Zero text below 10px.**

---

## 5. Icon System (Inline Geometric SVGs)

All workstation controls use inline SVGs with standard 14x14px or 16x16px bounding boxes, `stroke-width: 1.5` or `2.0`, `fill="none"`, and `stroke="currentColor"`. Arbitrary emoji characters are disallowed in technical controls and indicators.

### Key Icon Specifications:
1. **Activity Bar: 3D Earth (`#act-btn-home`):**
   ```html
   <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
   </svg>
   ```
2. **Activity Bar: AI Decision Terminal (`#act-btn-ai`):**
   ```html
   <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
   </svg>
   ```
3. **Activity Bar: Agriculture / Kishan (`#act-btn-agri`):**
   ```html
   <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
   </svg>
   ```
4. **Panel Resizers & Collapse Toggles (`#btn-toggle-left`, `#btn-toggle-right`):**
   ```html
   <!-- Collapse Left Rail -->
   <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
   </svg>
   <!-- Collapse Right Rail -->
   <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
   </svg>
   ```
5. **Time Machine Collapse / Expand Toggle (`#tm-toggle-btn`):**
   ```html
   <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
   </svg>
   ```

---

## 6. Component Contracts & Interaction Specifications

### 6.1 Panel Inversion Architecture
- **Left Rail (`#left-rail`):**
  - Order: Desktop `lg:order-1`, Mobile `order-2`
  - Width: Default `320px` (min `240px`, max `480px`)
  - Content: Dual-Agent AI Terminal (`#left-ai-view`), chat stream (`#chat-feed`), input field (`#user-input`), role selector (`#cyber-role-selector`), language buttons, quick prompts, orbital insights tab (`#left-insights-view`).
  - Collapse: Handled by `toggleLeftRail()`, adding `.rail-collapsed`.
- **Right Rail (`#right-rail`):**
  - Order: Desktop `lg:order-5`, Mobile `order-3`
  - Width: Default `340px` (min `260px`, max `480px`)
  - Content: Scene & Hydromet view (`#right-scene-view`), Live Hydromet preset selector, Scientific Layer Explorer (`#sci-layer-explorer`), India Intel dock slot (`#bhu-intel-dock-slot`), Location HUD dock slot (`#bhu-location-dock-slot`).
  - Collapse: Handled by `toggleRightRail()`, adding `.rail-collapsed`.

### 6.2 Splitter Drag Math & WebGL Preservation
- `#left-resizer` (between `#left-rail` and `#center-stage`):
  `width = clamp(240px, startW + dx, min(480px, window.innerWidth * 0.38))`
- `#right-resizer` (between `#center-stage` and `#right-rail`):
  `width = clamp(260px, startW - dx, min(480px, window.innerWidth * 0.38))`
- Invocations of `scheduleResizeRenderer()` run on `requestAnimationFrame` and trigger at `0ms`, `160ms`, and `280ms` during CSS transitions to prevent any aspect-ratio stretching.

### 6.3 Global Time Machine Collapse Contract
- Standard Height: `48px`.
- Collapsed Height: `24px` with minimal epoch label (`2026 CE · LIVE · CelesTrak GP`) and expand trigger.
- Toggle function `toggleTimeMachine()` switches states, toggles `.tm-collapsed` class, and invokes `scheduleResizeRenderer()`.

---

## 7. Affected File List

1. `Bhu Loka - भूलोक/DESIGN_WORKSTATION_PHASE1.md`: (New) Phase 1 layout and visual specification document.
2. `Bhu Loka - भूलोक/bhu_loka_cyber_dashboard.html`:
   - Top Bar DOM and styling cleanup.
   - Activity Bar (`#vscode-activity-bar`) click bindings and active indicators.
   - Floating prompt overlay (`#bhu-floating-ai-bar`) removal.
   - Side panel inversion: Moving AI Decision Terminal to `#left-rail`, and Scientific Explorer / Hydromet / Intel / Location HUD to `#right-rail`.
   - Adding collapse/expand toggles for left rail, right rail, and time machine.
   - Updating `switchLeftDockTab`, `switchRightDockTab`, `setNasaNavTab`, `initRailResizers`, and `bhuTimeMachineSeek` to reflect inverted docking.
   - Updating automated test helper `runStep1AutomatedTests()` to assert against the active Activity Bar buttons and inverted panels.
3. `Bhu Loka - भूलोक/Assets/vendor/bhu_loka_theme.css`:
   - Workstation layout token refinements, obsidian color ramp alignment, `.tm-collapsed` styling.
