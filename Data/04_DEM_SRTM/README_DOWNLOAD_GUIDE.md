# Folder 04: DEM — NASA SRTM 30m Elevation Data

## Status: NOT DOWNLOADED

| File to Download | Description |
|:---|:---|
| `srtm_patna_30m_elevation.tif` | SRTM 30m elevation raster clipped to Patna |

---

## What is SRTM DEM?

The Shuttle Radar Topography Mission (SRTM) produced a near-global digital elevation model at 30m (1 arc-second) resolution in 2000. For Patna — a flat alluvial plain — elevation ranges from about 42m to 58m above mean sea level (MSL).

We use elevation to compute:
- **Slope** (hydraulic gradient for runoff direction)
- **Topographic Wetness Index (TWI)** = ln(a / tan(slope)) — where a = upslope contributing area
- **Depression sinks** (micro-topographic low points where water ponds)
- **Elevation class** for each 50m hex cell

---

## Download Instructions — Option A: USGS EarthExplorer (Most Complete, Free)

**Website:** https://earthexplorer.usgs.gov

**Step 1: Create Free Account**
- Click "Login" then "Create New Account"
- Fill form, verify email.

**Step 2: Set Area of Interest**
- Under "Search Criteria", enter coordinates:
  ```
  North: 25.75    South: 25.20
  East:  86.10    West:  84.68
  ```
- Or click "Polygon" and draw Patna district.

**Step 3: Select Dataset**
- Click "Data Sets" tab.
- Navigate to: `Digital Elevation > SRTM > SRTM 1 Arc-Second Global`
- Check the checkbox next to it.

**Step 4: Results and Download**
- Click "Results" tab.
- Download tiles covering your area. For Patna, you likely need tiles:
  - `N25E084.hgt` and `N25E085.hgt`
- Each tile is about 25 MB.

**Step 5: Convert and Save**
- Save `.hgt` files to this folder.
- Our processing script will merge and clip them to Patna boundary automatically.

---

## Download Instructions — Option B: OpenTopography (Easiest, No Account Needed)

**Website:** https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1

1. Click "Select a Region".
2. Draw a box over Patna (25.2N–25.75N, 84.68E–86.1E).
3. Select Output Format: **GeoTiff**.
4. Select Dataset: **SRTM GL1 (Global 30m)**.
5. Click "Submit".
6. Download GeoTIFF directly (no account needed for small areas).
7. Save as `srtm_patna_30m_elevation.tif` in this folder.

---

## Why 30m SRTM?

Patna's flood risk is driven by micro-topographic depressions (Rajendra Nagar underpass, Kankarbagh bowl). At 30m resolution, SRTM captures these depression sinks. The 90m SRTM (3 arc-second) is too coarse for urban flood modeling.

