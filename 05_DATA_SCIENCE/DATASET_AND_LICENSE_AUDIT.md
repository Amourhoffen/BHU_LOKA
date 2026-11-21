# BHU LOKA — DATASET AND LICENSE AUDIT FOR GEOSPATIAL AI
**Document ID:** `BL-GEOAI-DLA-2026-V1`  
**System:** BHU LOKA (भूलोक) Indian Earth Observation Platform  
**Scope:** Training, Benchmark, and Evaluation Datasets for 9-Class Land Site Analytics

---

## 1. Executive Evaluation Matrix

| Dataset | Provider / Authors | Sensor / Resolution | Classes / Labels | Coverage & Size | License | Commercial Permissibility | Suitability for Indian Geography |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenEarthMap (OEM)** | Xia et al. / Univ. of Tokyo | Aerial/Satellite VHR ($0.25 - 0.5\text{m}$) | 8 classes (Bare soil, Building, Road, Agri, Forest, Water, Open, Non-veg) | 5,000 tiles ($1024\times1024$), 97 regions worldwide | CC BY-NC-SA 4.0 | ❌ Non-Commercial (Academic only) | **Moderate** (Good generic weights, but lacks informal Indian settlements) |
| **LoveDA** | Wang et al. (Wuhan Univ.) | VHR Aerial ($0.3\text{m}$ RGB) | 7 classes (Background, Building, Road, Water, Barren, Forest, Agriculture) | 5,987 images ($1024\times1024$), 18 urban/rural scenes | CC BY-SA 4.0 | ⚠️ ShareAlike constraint | **High** (Specifically tests urban-rural domain shifts identical to Indian peri-urban zones) |
| **TreeSatAI** | Ahlswede et al. (TU Berlin) | Multi-Sensor: Aerial ($0.2\text{m}$), Sentinel-2 (10m), Sentinel-1 SAR | 20 European tree species + canopy height | 50,381 multi-sensor patches | CC BY 4.0 | ✅ Full Commercial Freedom | ⚠️ **Species Mismatch** (European temperate species; cannot classify Indian tropical flora) |
| **Dynamic World** | WRI / Google / ESA | Sentinel-2 L2A ($10\text{m}$ multispectral) | 9 classes (Water, Trees, Grass, Flooded, Crops, Shrub, Built, Bare, Snow) | Global coverage, Near-real-time ($2015 - \text{Present}$) | CC BY 4.0 | ✅ Full Commercial Freedom | **Very High** (Continuous pan-India 10m baseline for macro LULC monitoring) |
| **LandCoverNet** | Radiant Earth Foundation | Sentinel-2 L2A ($10\text{m}$) | 7 classes (Water, Natural bare, Artificial bare, Cultivated, Woody, Shrub, Herbaceous) | 1,980 chips ($512\times512$), Africa, Asia, Americas | CC BY-SA 4.0 | ⚠️ ShareAlike | **High** (High-quality consensus human labels for Southern Asia/India) |
| **Google Open Buildings v3** | Google Research | VHR Satellite ($0.5\text{m}$) | Building footprints + polygon vertices + confidence | 1.8 billion buildings (South Asia, Africa, LatAm) | CC BY 4.0 / ODbL | ✅ Full Commercial Freedom | **Exceptional** (Primary ground-truth for Indian building geometry) |
| **Microsoft Global ML Footprints** | Microsoft AI for Good | Bing Imagery ($0.3 - 0.5\text{m}$) | Building footprints (GeoJSON / FlatGeobuf) | 1.2 billion building polygons worldwide | ODbL (Open Data Commons) | ✅ Full Commercial Freedom | **Exceptional** (Complements Open Buildings in urban centers) |
| **Bhuvan LULC (ISRO NRSC)** | ISRO NRSC, Hyderabad | Resourcesat-2 LISS-III / AWiFS ($24\text{m} / 56\text{m}$) | National LULC 1:50,000 (22 classes: kharif, rabi, double crop, wasteland, wetlands) | 100% Pan-India coverage ($2005 - \text{Present}$) | Government Open Data (GODL-India) | ✅ Free Indian Use (Attribution required) | **Gold Standard** for Indian ground-truth validation |
| **Forest Survey of India (FSI)** | Ministry of Environment, Forest & Climate Change | Sentinel-2 / LISS-III ($10\text{m} - 23.5\text{m}$) | Very Dense Forest (VDF), Moderately Dense (MDF), Open Forest (OF), Scrub | Pan-India biennial inventory ($1987 - 2023$) | Government Open Data (GODL-India) | ✅ Free Indian Use (Attribution required) | **National Benchmark** for Indian forest canopy validation |

---

## 2. Scientific Evaluation of Indian Geospatial Complexities

Training models strictly on Western or East Asian datasets creates severe domain shifts when deployed on Indian terrain. The following domain-specific characteristics must be addressed:

### 2.1. Informal Settlements and Mixed Building Materials
* Western benchmarks (Inria, SpaceNet) assume orthogonal, regularly spaced roofs with bitumen shingles or terracotta tiles.
* In Indian cities (e.g. Hyderabad, Patna, Mumbai peri-urban zones), 40%–60% of structures are informal with mixed roofs:
  - RCC Concrete flat terraces (`#cbd5e1` / `#e2e8f0`) with boundary parapet shadows
  - Blue or metallic galvanized tin/asbestos sheets (`#0284c7` / `#38bdf8`)
  - Brick and mud tile roofs (`#ea580c` / `#c2410c`)
* **Solution:** Supplement OpenEarthMap/LoveDA with Google Open Buildings v3 and local Indian VHR spectral contrast heuristics.

### 2.2. Monsoon Phenology & Agricultural Dynamics
* Unlike temperate biomes with single-season planting, India exhibits distinct cropping cycles:
  - **Kharif** (June–October, monsoon-fed, high cloud cover)
  - **Rabi** (November–April, winter irrigated)
  - **Zaid** (April–June, summer fallow / arid)
* An agricultural parcel in Rajasthan or Bihar will classify as "Barren/Bare soil" in May, but "Dense Agriculture" in September.
* **Mandate:** The Site Analytics Engine must **display the acquisition timestamp and season code** on all agricultural predictions.

### 2.3. Water Bodies and Traditional Tank Cascades
* In Southern India (Telangana, Karnataka, Tamil Nadu), water bodies exist as interconnected "Eri" or tank cascades with seasonal Full Tank Level (FTL) boundaries.
* During dry months, lake beds become dry cracked clay (easily misclassified as barren land). Encroachments frequently occur on seasonal dry lake margins.
* **Mandate:** Link water body delineation to statutory FTL boundaries and Sentinel-1 SAR backscatter ($\sigma^0 < -18\text{ dB}$) to detect surface moisture even under canopy or weed cover.

---

## 3. Tree Species Classification: The Indian Botanical Reality

TreeSatAI provides outstanding multi-sensor training methodology, but its classes are European temperate species:
- *Quercus robur* (English oak), *Pinus sylvestris* (Scots pine), *Picea abies* (Norway spruce).

In Indian ecosystems, the dominant tree species are vastly different:
- **Tropical Dry Deciduous / Agroforestry:** *Azadirachta indica* (Neem), *Dalbergia sissoo* (Shisham), *Mangifera indica* (Mango), *Tectona grandis* (Teak), *Bambusa vulgaris* (Bamboo), *Ficus religiosa* (Peepal), *Ficus benghalensis* (Banyan).
- **Semi-Arid / Urban Invasive:** *Prosopis juliflora* (Vilayati Kikar), *Eucalyptus globulus*, *Conocarpus erectus*.

> [!WARNING]
> **Scientific Integrity Rule:** BHU LOKA will **not** attempt tree species identification on 10m Sentinel-2 or standard RGB imagery. Tree species classification will only be enabled when:
> 1. High-resolution hyperspectral imagery (e.g., AVIRIS-NG India campaigns or EnMAP/PRISMA) is available, OR
> 2. Verified multi-temporal phenology profiles (12-month Sentinel-2 NDVI harmonic curve) match validated Forest Survey of India (FSI) spectral libraries.

---

## 4. Recommended Dataset Strategy for Production MVP

```
                                  BHU LOKA TRAINING & EVALUATION STRATEGY
                                                     │
         ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
         ▼                                           ▼                                           ▼
  PRETRAINED BASELINE                     INDIAN VECTOR GROUND-TRUTH                     VALIDATION BENCHMARK
  • SegFormer on ImageNet-1k              • Google Open Buildings v3 (1.8B)             • LoveDA Urban/Rural (5,987 tiles)
  • TorchGeo LandCoverNet Weights          • Microsoft Global ML Footprints (1.2B)        • ISRO Bhuvan 1:50k LULC
  • DeepForest NEON ITC Model (MIT)       • OpenStreetMap India Administrative Bounds    • Forest Survey of India (FSI)
```

1. **Phase 1 MVP:** Leverage pretrained **SegFormer-B0** fine-tuned on **LoveDA + TorchGeo LandCoverNet** for 7-class semantic segmentation (Building, Road, Water, Barren, Forest, Agriculture, Background).
2. **Phase 2 Building Refinement:** Overlay Google Open Buildings v3 and Microsoft ML vector layers to eliminate false positives over active railway corridors and arterial roads.
3. **Phase 3 Tree Crown Delineation:** Deploy **DeepForest** exclusively on drone and sub-meter VHR satellite crops.
