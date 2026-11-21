# BHU LOKA — GEOSPATIAL AI MODEL RESEARCH & COMPARATIVE AUDIT
**Document ID:** `BL-GEOAI-MSR-2026-V1`  
**Author:** Senior Geospatial AI Architect & Remote Sensing Research Team  
**System:** BHU LOKA (भूलोक) Planetary Intelligence Platform  
**Target Environment:** Pan-India Geospatial Analytics (Satellite, Drone, SAR & DEM)

---

## 1. Executive Summary & Problem Scope

BHU LOKA requires an AI-powered Site Analytics Engine capable of automated multi-class spatial extraction across diverse Indian geographies. The objective is to identify and segment:
1. **Trees and Vegetation** (Macro canopy, orchards, riparian vegetation)
2. **Individual Tree Crowns (ITC)** (Delineation and count)
3. **Tree Species Classification** (Where hyperspectral or multi-seasonal spectral resolution permits)
4. **Buildings & Rooftops** (Informal settlements, plotted developments, commercial campuses)
5. **Road Networks** (Arterial highways to unpaved village collector roads)
6. **Lakes & Water Bodies** (Permanent lakes, seasonal tanks, irrigation canals, FTL boundaries)
7. **Agricultural Land** (Active croplands, fallow plots, cadastral boundaries)
8. **Barren Land** (Exposed bedrock, wasteland, arid soils, cleared plots)
9. **Land-Use & Land-Cover (LULC) Changes** (Bi-temporal encroachment and urbanization tracking)

No single machine learning model can optimally solve all nine tasks simultaneously. Satellite remote sensing is bound by the **fundamental trade-off between spatial resolution, spectral resolution, and revisit rate**. A foundation model designed for 30m HLS data cannot delineate a 3m tree crown, while an ultra-high-resolution drone detector cannot perform regional multi-temporal change detection across a river basin.

This document presents a rigorous scientific and engineering audit of the leading foundation, semantic segmentation, and object detection architectures to establish an evidence-based model selection.

---

## 2. In-Depth Model Architectures & Benchmark Matrix

| Feature / Metric | IBM-NASA Prithvi-EO 2.0 | SegFormer (MiT-B0 / B2) | SAMGeo (Segment Anything) | Grounding DINO | YOLO11-Seg | DeepForest | RT-DETR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Task** | Spatio-temporal Foundation (LULC, Flood, Biomass) | High-Throughput Semantic Segmentation | Zero-Shot Interactive Instance Segmentation | Open-Vocabulary Text-Guided Detection | Real-Time Instance Segmentation | Individual Tree Crown (ITC) Delineation | Real-Time Transformer Object Detection |
| **Model Type** | 3D Vision Transformer (MAE) | Hierarchical ViT + All-MLP Decoder | ViT Encoder + Prompt Mask Decoder | Dual-Encoder (Swin + Text Transformer) | CNN/CSPDarknet + Prototype Masks | RetinaNet / ResNet-50 Bounding Box/Mask | Hybrid ViT Encoder + Hungarian Matcher |
| **Parameters** | 100M / 300M | 3.7M (B0) / 27.5M (B2) | 91M (ViT-B) / 308M (ViT-L) | 172M (Swin-T) / 341M (Swin-B) | 2.8M (n) / 10.1M (s) | 32.5M | 20M (R18) / 42M (R50) |
| **Input Channels** | 6 Spectral Bands (B, G, R, Narrow NIR, SWIR1, SWIR2) | 3 (RGB) or 4 (RGB+NIR) | 3 (RGB) | 3 (RGB) | 3 (RGB) | 3 (RGB) | 3 (RGB) |
| **Native Resolution** | 15m – 30m (HLS / Sentinel-2) | Arbitrary ($0.1\text{m} - 10\text{m}$) | Arbitrary ($0.05\text{m} - 10\text{m}$) | Arbitrary ($0.1\text{m} - 1\text{m}$) | Arbitrary ($0.1\text{m} - 1\text{m}$) | VHR Airborne/Drone ($< 0.5\text{m}$) | Arbitrary ($0.1\text{m} - 1\text{m}$) |
| **Inference Time (T4 GPU)**| ~85 ms / $512\times512$ | **14 ms (B0) / 28 ms (B2)** | ~450 ms (ViT-B) | ~110 ms | ~8 ms (YOLO11s) | ~32 ms | ~18 ms |
| **Inference Time (CPU)** | ~1,200 ms | **65 ms (B0)** | ~4,200 ms | ~1,600 ms | ~45 ms | ~280 ms | ~160 ms |
| **VRAM Footprint** | ~3.8 GB (FP16) | **0.8 GB (B0) / 1.6 GB (B2)** | ~4.5 GB | ~3.2 GB | ~1.1 GB | ~1.4 GB | ~1.8 GB |
| **Browser/ONNX Export** | Complex (custom 3D ops) | **Native (ONNX / WebGL)** | Medium (Encoder heavy) | Complex | Native ONNX | Native ONNX | Native ONNX |
| **Model License** | Apache 2.0 | **Apache 2.0** | Apache 2.0 | Apache 2.0 | **AGPL-3.0 (Commercial Restrictive)** | **MIT License** | **Apache 2.0** |
| **Commercial Freedom** | Full | **Full** | Full | Full | Requires Enterprise License | **Full** | **Full** |
| **Suitability for MVP** | Regional Basin / Change | **PRIMARY MVP (LULC 8-Class)** | Secondary (Interactive Click) | Prompt Auditing | High Risk (License) | **PRIMARY (Individual Trees)**| Secondary (Object Spotting)|

---

## 3. Detailed Model Evaluations

### 3.1. SegFormer (Mix Transformer — MiT-B0 / MiT-B2)
* **Architecture:** Hierarchical Transformer encoder generating multi-scale features ($1/4, 1/8, 1/16, 1/32$) without positional embeddings (uses $3\times3$ depthwise convolutions in Mix-FFN), coupled to a lightweight All-MLP decoder.
* **Why it Excels for BHU LOKA:**
  1. **Extreme Efficiency:** MiT-B0 has only 3.7 million parameters. It achieves 37.4% mIoU on ADE20K and >78% mIoU on urban land-cover datasets while executing in 14ms on a cheap T4 GPU or 65ms on standard cloud CPUs.
  2. **Resolution Invariance:** Because it avoids fixed positional encodings, an arbitrary-sized cropped AOI tile (e.g. $640\times640$ or $1024\times1024$) can be directly fed into the network without distorting spatial aspect ratios.
  3. **Sharp Boundary Recovery:** The multi-scale hierarchical feature fusion prevents the "blob" effect common in standard U-Nets, keeping road corridors and building boundaries rectilinear.
* **Limitations:** Semantic segmentation only; does not separate touching building polygons into individual instances (requires watershed or connected-component post-processing).

### 3.2. IBM-NASA Prithvi-EO 2.0
* **Architecture:** Pretrained on 100M / 300M parameters across multi-temporal Harmonized Landsat Sentinel-2 (HLS) tiles spanning North America and global sites. Incorporates temporal dimension ($T$) directly into 3D patch embeddings.
* **Why it Matters:** Prithvi is the most scientifically sound model for **long-term bi-temporal change detection (e.g., 2016 vs 2026)** and multi-spectral index tracking (NDVI, NDWI, SWIR soil moisture).
* **Critical Limitation for Site Analytics:** Native patch resolution is 30m. While it can ingest 10m Sentinel-2 bands, it **cannot** detect individual tree crowns, narrow residential roads ($<10\text{m}$), or small residential houses ($<100\text{ m}^2$).
* **Role in BHU LOKA:** Dedicated regional change-detection backbone for Sentinel-2 basin monitoring (macro LULC), not high-resolution site parcel analytics.

### 3.3. DeepForest (Weinstein et al., University of Florida)
* **Architecture:** PyTorch implementation of RetinaNet with a ResNet-50 backbone, pretrained on airborne RGB/LiDAR from the NEON network (>30 million crown annotations).
* **Task Specificity:** Delineating **Individual Tree Crowns (ITC)** and estimating tree count, canopy area, and crown diameter.
* **Resolution Dependency:** Requires sub-meter imagery ($0.1\text{m} - 0.4\text{m}$ drone or $0.3\text{m} - 0.5\text{m}$ VHR satellite). On 10m Sentinel-2 imagery, individual trees cannot be detected.
* **License & Usability:** MIT License. 100% free, production-ready Python package with pre-built model weights (`deepforest.main.deepforest()`).

### 3.4. SAMGeo (Segment Anything for Geospatial — Qiusheng Wu)
* **Architecture:** Adapts Meta's Segment Anything Model (SAM) with raster/vector spatial operators, supporting point prompts, bounding box prompts, and regular grid prompts over GeoTIFF rasters.
* **Role in BHU LOKA:** Perfect for **Interactive Site Refinement**. When a municipal officer or surveyor clicks on a disputed water body or illegal encroachment, SAMGeo expands the precise vector boundary in zero-shot mode without fine-tuning.

### 3.5. Grounding DINO + SAM (Grounded-SAM)
* **Architecture:** Connects text query understanding ("temporary tin shed on lake bed", "brick kiln", "swimming pool") to open-set bounding box detection (Grounding DINO), which then feeds prompts into SAM for pixel-perfect segmentation.
* **Role in BHU LOKA:** High-value for administrative audits and statutory Lake FTL buffer enforcement, allowing plain-English queries to generate geospatial masks.

---

## 4. The Tree Species & Resolution Scientific Reality Check

> [!IMPORTANT]
> **Scientific Integrity Mandate:** Tree species classification CANNOT be performed on 10m Sentinel-2 or standard RGB imagery.

* **Physics of Tree Species Identification:** Discriminating species (e.g., *Azadirachta indica* / Neem vs. *Tectona grandis* / Teak vs. *Eucalyptus*) requires:
  1. Hyperspectral signatures (>30 narrow bands capturing leaf cellular structure, water absorption dips, and chlorophyll fluorescence), OR
  2. Multi-temporal phenological phenograms (observing exact leaf-fall and flowering weeks across 12 consecutive months at 10m resolution), OR
  3. Ultra-high-resolution drone imagery ($< 5\text{cm}$ GSD) where leaf morphology and branching patterns are visually discernible.
* **BHU LOKA Protocol:**
  - On Sentinel-2 (10m): Detect **Macro Vegetation & Forest Canopy** (NDVI / EVI2 / Red-Edge index).
  - On VHR Satellite (0.5m): Detect **Tree Canopy Clusters & Tree Rows**.
  - On Drone Orthomosaics ($< 0.1\text{m}$): Delineate **Individual Tree Crowns** (DeepForest).
  - Tree Species: Flag as *"Requires Hyperspectral / Drone Phenology Survey"* unless certified multi-temporal regional ground-truth (FSI / Bhuvan) is uploaded.

---

## 5. Architectural Recommendation

```
                                  AOI INPUT
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
         REGIONAL SCALE (10m - 30m)                 LOCAL SITE (0.1m - 0.5m)
         Copernicus Sentinel-2 & SAR                VHR Satellite / Drone Ortho
                 │                                         │
                 ▼                                         ▼
        ┌──────────────────┐                     ┌──────────────────┐
        │  Prithvi-EO 2.0  │                     │   SegFormer-B0   │
        │  (Bi-Temporal    │                     │  (8-Class LULC   │
        │   Change & LULC) │                     │   Segmentation)  │
        └──────────────────┘                     └─────────┬────────┘
                 │                                         │
                 │                               ┌─────────┴─────────┐
                 │                               ▼                   ▼
                 │                      ┌─────────────────┐ ┌────────────────┐
                 │                      │   DeepForest    │ │     SAMGeo     │
                 │                      │ (Individual Tree│ │  (Interactive  │
                 │                      │     Crowns)     │ │ Click-Refine)  │
                 │                      └─────────────────┘ └────────────────┘
                 │                               │                   │
                 └───────────────────────┬───────┴───────────────────┘
                                         ▼
                             GEOSPATIAL VECTOR ENGINE
                             (Rasterio · GeoPandas · UTM)
                                         │
                                         ▼
                           BHU LOKA INTERACTIVE STUDIO
```
