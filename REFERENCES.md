# Scientific References & Data Provenance

This document lists exclusively the scientific literature, satellite missions, data archives, and algorithms used in the **BHU LOKA · Dancing with the SARs** project for the NASA Space Apps Challenge 2026.

---

## 1. Satellite Remote Sensing Data & Archives

### Primary Radar (SAR) Observations: Copernicus Sentinel-1
- **Platform / Sensors**:
  - Copernicus Sentinel-1A C-band SAR (ESA)
  - Copernicus Sentinel-1B C-band SAR (ESA)
- **Swath Mode & Product**: Interferometric Wide (IW), Ground Range Detected (GRD) at High Resolution.
- **Center Frequency**: $5.405\text{ GHz}$ (C-band, wavelength $\lambda \approx 5.55\text{ cm}$).
- **Polarisation**: VV (Vertical Transmit, Vertical Receive).
- **Pixel Spacing**: $10.0\text{ m} \times 10.0\text{ m}$.
- **Data Archive & Access**:
  - Alaska Satellite Facility (ASF) Data Search Vertex: [search.asf.alaska.edu](https://search.asf.alaska.edu/)
  - NASA Earthdata Search: [search.earthdata.nasa.gov](https://search.earthdata.nasa.gov/)
- **Exact Granule / Scene IDs**:
  1. **Pre-Flood Dry Baseline**:
     - `S1A_IW_GRDH_1SDV_20190923T002026_20190923T002051_029141_034EEC`
     - Acquisition Time: `2019-09-23T00:20:38Z` (Descending Pass)
  2. **Peak Flood Deluge**:
     - `S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB`
     - Acquisition Time: `2019-09-29T00:19:37Z` (Descending Pass)

### Context Optical Imagery
- **Provider**: ESRI World Imagery Tile Service via ArcGIS REST Services.
- **Role**: High-resolution optical background context (used strictly for geographic orientation; not used for flood delineation due to cloud-cover opacity during monsoon).

---

## 2. Peer-Reviewed Methodology & Calibration Literature

1. **Otsu Bimodal Thresholding**:
   - Otsu, N. (1979). "A threshold selection method from gray-level histograms." *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. [doi:10.1109/TSMC.1979.4310076](https://doi.org/10.1109/TSMC.1979.4310076)
   - *Application*: Automated derivation of backscatter drop threshold ($T^* = -3.80\text{ dB}$) separating water surfaces from land.

2. **SAR Radiometric Calibration & Speckle Suppression**:
   - European Space Agency (ESA). *Sentinel-1 Radiometric Calibration Technical Guide*.
   - Formula: $\sigma^0_{\text{dB}} = 10 \cdot \log_{10}(\text{DN}^2 + \epsilon) - 83.0\text{ dB}$.
   - Lee, J. S. (1980). "Digital image enhancement and noise filtering by use of local statistics." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-2(2), 165–168.

3. **SAR Water Specular Scattering Principles**:
   - Ulaby, F. T., Moore, R. K., & Fung, A. K. (1982). *Microwave Remote Sensing: Active and Passive*. Addison-Wesley.
   - *Principle*: Smooth surface water behaves as a specular reflector at microwave frequencies, directing radar energy away from the sensor ($<-15.5\text{ dB}$).

4. **NISAR Mission Formulation & Applications**:
   - Rosen, P. A., et al. (2017). "The NASA-ISRO SAR (NISAR) Mission Dual-band Radar Instrument." *IEEE Radar Conference*.
   - NASA Applied Remote Sensing Training Program (ARSET). *Applications of SAR for Disaster Management*.

---

## 3. Software Libraries & Open Standards
- **Python**: `numpy`, `scipy.ndimage`, `PIL` (Pillow), `scipy.interpolate`.
- **Frontend / GIS**: Leaflet.js 1.9.4, Tailwind CSS, GeoJSON (RFC 7946), WGS84 (EPSG:4326).
