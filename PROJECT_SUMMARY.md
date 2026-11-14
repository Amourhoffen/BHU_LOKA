# PROJECT SUMMARY · Bhu Loka (भूलोक) – Patna Intelligence
### NASA Space Apps Challenge 2026 (Bhopal)
**Selected Challenge:** **"Dancing with the SARs"**  
**Project Name:** **Bhu Loka – Patna Intelligence**  
**Team / Author:** Prince Kumar (Roll No. `PA2511CDH37`, IIT Patna, M.S. CS & Data Analytics)  
**Supervisor / Mentor:** Dr. Pallav Rustogi  
**Repository:** [https://github.com/Amourhoffen/BHU_LOKA_privite](https://github.com/Amourhoffen/BHU_LOKA_privite) (Branch: `Test`)  
**License:** Open Source MIT License

---

## 1. High-Level Project Summary

**Bhu Loka – Patna Intelligence** is an open-source, client-side 3D geospatial workstation and AI decision system engineered for the **NASA Space Apps Challenge 2026 ("Dancing with the SARs")**. Focusing on the flood-vulnerable Gangetic metropolis of Patna, Bihar, Bhu Loka addresses the critical limitation of optical satellite sensors (such as Landsat or MODIS), which become 100% blinded by dense monsoon clouds and severe precipitation.

By processing active microwave Synthetic Aperture Radar (SAR) data from the Copernicus Sentinel-1 constellation alongside the upcoming NASA-ISRO NISAR radar mission specifications, Bhu Loka cuts through monsoon cloud cover to measure surface water inundation ("Naya Paani"), backscatter dynamics ($\Delta\sigma^0$), and elevation sinks. It translates complex radar physics into clear, actionable recommendations for four vital citizen groups: **farmers** (crop selection and soil wetness), **the public** (air quality, heatwave stress, and safe activity windows), **homebuyers and businesses** (elevation benchmarks and flood risk zones), and **city officials** (ward-level disaster exposure).

---

## 2. Detailed Technical Description

### 2.1 Problem Statement & Regional Context
Patna lies at the hydrologic confluence of four major river systems: the Ganga, Gandak, Son, and Punpun. During catastrophic monsoon events—most notably the late September 2019 deluge—intense localized rainfall combined with high river water levels causes severe backflow and drainage failure, inundating low-lying urban sectors like Kankarbagh and Rajendra Nagar under 2 to 3 meters of stagnant water for days. Traditional optical imagery was rendered completely useless by continuous overcast cloud decks. Disaster managers, farmers, and citizens lacked timely, cloud-penetrating spatial intelligence.

### 2.2 Methodology & Processing Pipeline
Bhu Loka's radar processing pipeline operates under strict scientific standards:
1. **Radar Ingestion & Radiometric Calibration:**
   Dual-date Sentinel-1 C-band SAR scenes (Pre-flood baseline: 23 Sep 2019, `S1A_IW_GRDH`; Peak flood: 29 Sep 2019, `S1B_IW_GRDH`) were acquired via the Alaska Satellite Facility (ASF Vertex) and NASA Earthdata. Scenes were spatially subsetted to the Patna Area of Interest ($25.2^\circ - 25.8^\circ\text{N}, 84.8^\circ - 85.5^\circ\text{E}$), radiometrically calibrated to backscatter coefficients $\sigma^0\text{ (dB)} = 10\cdot\log_{10}(\text{DN}^2 + \varepsilon) - 83.0$, and speckle-filtered using a $5\times 5$ median kernel.
2. **Logarithmic Difference & Inundation Extraction:**
   Difference backscatter was computed as $\Delta\sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$. Applying an automated Otsu bimodal threshold ($T^* = -3.80\text{ dB}$ for gain, $\sigma^0_{\text{post}} \le -15.0\text{ dB}$) delineated **$26.54\text{ km}^2$** of new surface floodwater (*"Naya Paani"*), while excluding the permanent $113.82\text{ km}^2$ river channel.
3. **3D Topographic Mesh Fusion:**
   Real elevation data from the Copernicus 30m / 90m Digital Elevation Model (DEM) was converted into a hardware-accelerated 3D terrain grid in Three.js, accurately modeling the high natural river levee ($53 - 55\text{ m}$) against the low inland drainage bowl ($44 - 46\text{ m}$).
4. **Bilingual AI Advisory Engine:**
   A rule-based and retrieval-augmented decision terminal interprets environmental data in English, Hindi (हिन्दी), and Hinglish, citing verified data inputs and including transparent *"Why this answer?"* accordions and public health medical disclaimers.

---

## 3. Space Agency Data Usage & Scientific Integrity

Bhu Loka adheres strictly to the rule of honest data labeling. Every metric displayed across the user interface carries a source tag indicating whether it is **Live**, **Measured**, **Modelled/Estimated**, or **Sample/Illustrative**:

| Dataset / API | Space Agency / Provider | Usage in Bhu Loka | Provenance Classification |
|---|---|---|---|
| **Sentinel-1 C-SAR GRD** | ESA / Alaska Satellite Facility (ASF Vertex) / NASA Earthdata | Dual-date radar backscatter, change detection, flood mask ($26.54\text{ km}^2$) | **Measured Satellite Observation** |
| **Copernicus DEM (GLO-30/90)** | European Space Agency (ESA) / Copernicus | 3D terrain mesh generation, ward elevation benchmarks (42m to 55m AMSL) | **Real Elevation Grid** |
| **NASA POWER API** | NASA Langley Research Center | Daily solar radiation (MJ/m²), ambient climatology, precipitation records | **Live Satellite Telemetry** |
| **Open-Meteo Weather & AQI** | Global NWP / CAMS / Copernicus Atmosphere | Live ambient temperature, relative humidity, PM2.5 hourly forecast | **Live Meteorological Feed** |
| **SoilGrids 250m** | ISRIC / FAO-56 | Soil texture (sandy loam, clay), organic carbon, pH ratings for Bihar | **Calibrated Soil Model** |
| **NISAR L-band & S-band Specs** | NASA JPL / ISRO | Dual-frequency penetration comparison under flooded forest and crop canopies | **Sensor Design Specification** |
| **Municipal Crime / Safety Index** | Synthesized municipal baseline | Illustrative ward security rating for homebuyers | **Sample / Illustrative (Clearly Marked)** |

---

## 4. Software Architecture & Deployment

- **Frontend Core:** Pure HTML5, WebGL, Three.js, Leaflet.js, and Tailwind CSS.
- **Client-Side Reliability:** 100% static deployment with local browser caching (1-hour TTL in `localStorage`) and graceful sovereign offline fallbacks. The application never breaks or throws blank screens when external network calls fail.
- **Deployability:** Out-of-the-box static deployment on Netlify (`netlify.toml`), Vercel (`vercel.json`), or GitHub Pages. Zero paid services required.
