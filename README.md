# BHU LOKA (भूलोक) · Dancing with the SARs
### Sovereign Dual-Date SAR Flood Inundation & Change Detection Workstation
**NASA Space Apps Challenge 2026 · Challenge: "Dancing with the SARs"**

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![SAR Platform](https://img.shields.io/badge/Sensor-Copernicus%20Sentinel--1%20C--SAR-0284c7.svg)](https://search.asf.alaska.edu/)
[![Study Area](https://img.shields.io/badge/Region-Patna%20%26%20Ganga%20Floodplain-amber.svg)](https://en.wikipedia.org/wiki/2019_Bihar_floods)
[![Data Provenance](https://img.shields.io/badge/Provenance-ASF%20Vertex%20%2F%20NASA%20Earthdata-blue.svg)](https://search.asf.alaska.edu/)

---

## 1. Project Overview & Motivation

During catastrophic monsoon floods in South Asia, optical satellites (such as Landsat, Sentinel-2, or MODIS) are rendered **100% blind** due to dense cloud cover and heavy rainfall. In late September 2019, the author's hometown of **Patna, Bihar** (located at the confluence of the Ganga, Gandak, Son, and Punpun rivers) experienced an unprecedented pluvial and fluvial deluge, submerging urban residential sectors (Rajendra Nagar, Kankarbagh) under 6 to 10 feet of standing water.

**BHU LOKA · Dancing with the SARs** delivers an interactive, scientifically verified Synthetic Aperture Radar (SAR) change-detection workstation. By processing dual-date active microwave C-band ($5.405\text{ GHz}$) radar data from the **Copernicus Sentinel-1 constellation** (via Alaska Satellite Facility Vertex and NASA Earthdata), the workstation penetrates heavy monsoon cloud cover and nighttime darkness to delineate specular floodwaters and extract newly inundated areas (**"Naya Paani"**).

---

## 2. Key Interactive Features

- **Interactive Before/After Swipe Slider:**
  Hardware-accelerated vertical curtain slider comparing the Pre-Flood dry baseline (23 Sep 2019, Sentinel-1A) with the Peak Flood deluge (29 Sep 2019, Sentinel-1B).
- **"Naya Paani" (Flood Water Gain) Overlay:**
  High-visibility fluorescent cyan (`#00E5FF`) overlay delineating the verified **$26.54\text{ km}^2$** of newly inundated land with real-time opacity adjustment ($0\%\text{ to }100\%$).
- **Permanent River Channel Separation:**
  Independent deep navy (`#1565C0`) overlay preserving the **$113.82\text{ km}^2$** baseline perennial Ganga riverbed.
- **Bilingual AI SAR Analyst (English + Hindi):**
  A grounded conversational explanation module translating radar backscatter physics into actionable guidance for relief agencies (NDRF/SDRF) while explicitly communicating scientific limitations.
- **100% Static Client-Side Deployment:**
  Zero external Python backend required at runtime. Runs entirely in modern browsers via standard Web APIs and Leaflet.js, deployable instantly to GitHub Pages or Netlify.

---

## 3. Scientific Methodology & Data Provenance

```
[Raw Sentinel-1 GeoTIFFs (ASF Vertex)]
                │
                ▼
[1. Spatial Crop & Co-registration (Patna AOI: 2602 × 1709 px, 10m grid)]
                │
                ▼
[2. Radiometric Calibration: σ°(dB) = 10 · log10(DN² + ε) - 83.0 dB]
                │
                ▼
[3. 5×5 Median Kernel Speckle Noise Suppression]
                │
                ▼
[4. Logarithmic Backscatter Difference: Δσ° = σ°_post - σ°_pre]
                │
                ▼
[5. Automated Otsu Bimodal Thresholding: T* = -3.80 dB]
                │
        ┌───────┴────────────────────────┐
        ▼                                ▼
[Permanent Ganga River Channel]   ["Naya Paani" / Flood Water Gain]
(σ°_pre ≤ -40.0 dB, 113.82 km²)  (Δσ° ≤ -3.80 dB, σ°_post ≤ -15.0 dB, 26.54 km²)
```

### Exact Observed Sentinel-1 Scenes (ASF Vertex / NASA Earthdata)
| Role | Scene ID | Sensor | Acquisition Date (UTC) | Pass |
|---|---|---|---|---|
| **Pre-Flood Baseline** | `S1A_IW_GRDH_1SDV_20190923T002026_20190923T002051_029141_034EEC` | Sentinel-1A | 2019-09-23 00:20:38 | Descending |
| **Peak Flood Deluge** | `S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB` | Sentinel-1B | 2019-09-29 00:19:37 | Descending |

---

## 4. Quantitative Results

| Metric | Value | Description |
|---|---|---|
| **Total Study AOI** | **$444.68\text{ km}^2$** | Patna Urban Core & Ganga Floodplain Bounding Box |
| **Permanent River Channel** | **$113.82\text{ km}^2$** | Pre-flood baseline perennial Ganga channel |
| **Newly Inundated Flood Water** | **$26.54\text{ km}^2$** | Verified flood gain (**"Naya Paani"**) |
| **Total Peak Water Extent** | **$140.36\text{ km}^2$** | Total water surface during peak deluge |
| **Urban Inundation Fraction** | **$5.97\%$** | Fraction of urban AOI submerged |
| **Otsu Backscatter Drop ($T^*$)** | **$-3.80\text{ dB}$** | Automated bimodal water separation threshold |
| **Water Mean Backscatter** | **$-41.85\text{ dB}$** | Specular scattering reflection |

---

## 5. Repository Structure

```
.
├── index.html                           # Hero Interactive SAR Viewer (Static web app)
├── REFERENCES.md                        # Authoritative scientific citations & data provenance
├── LICENSE                              # MIT Open Source License
├── README.md                            # Project documentation
├── Data/
│   ├── 02_SAR_Sentinel1/                # Raw Sentinel-1 manifest & metadata (GeoTIFFs excluded via .gitignore)
│   └── 08_Processed_Outputs/
│       ├── sar_pre_flood_20190923.png   # Pre-flood calibrated grayscale SAR raster
│       ├── sar_post_flood_20190929.png  # Peak deluge calibrated grayscale SAR raster
│       ├── sar_flood_gain_overlay.png   # Transparent RGBA cyan inundation overlay
│       ├── sar_permanent_water_overlay.png # Transparent RGBA navy river overlay
│       ├── sar_change_classified_overlay.png # Combined multi-class change overlay
│       └── sar_flood_change_metadata.json # Scientific quantitative summary JSON
├── Research_Paper_Workflow/
│   └── scripts/
│       └── process_sar_flood_change.py  # Reproducible Python raster processing script
└── Assets/
    └── vendor/                          # Local Leaflet.js, Leaflet.css, Tailwind CSS
```

---

## 6. Quickstart & Deployment

### Local Usage
No web server required. Simply double-click `index.html` or open it in any modern browser:
```bash
# Windows
start index.html

# macOS
open index.html

# Linux
xdg-open index.html
```

### Static Hosting (GitHub Pages / Netlify)
1. Push this repository to GitHub.
2. Under **Settings > Pages**, set the source branch to `Test` or `main` and directory to `/ (root)`.
3. The interactive viewer goes live at `https://<username>.github.io/<repo>/`!

### Reproducing the Processing Pipeline (Python)
```bash
pip install numpy scipy pillow
python Research_Paper_Workflow/scripts/process_sar_flood_change.py
```

---

## 7. Research Team & Academic Provenance

- **Author:** Prince Kumar (`PA2511CDH37`)
- **Institution:** Indian Institute of Technology Patna (IIT Patna)
- **Program:** M.S. (CSDA)
- **Supervisor:** Dr. Pallav Rustogi
- **Challenge:** NASA Space Apps Challenge 2026 — *"Dancing with the SARs"*
