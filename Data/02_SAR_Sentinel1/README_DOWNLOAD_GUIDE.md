# Folder 02: SAR Sentinel-1 Data (Flood Mapping)

## Status: PREVIEW DOWNLOADED — Full GeoTIFF Rasters Pending

| File | Status | Description |
|:---|:---:|:---|
| `pre_flood_20190923_preview.png` | DONE | Preview image of dry scene 23 Sep 2019 |
| `peak_flood_20190929_preview.png` | DONE | Preview image of peak flood 29 Sep 2019 |
| `sentinel1_2019_deluge_manifest.json` | DONE | STAC metadata with download links |
| `S1A_IW_GRDH_VV_20190923_Patna.tif` | **DOWNLOAD NEEDED** | Full VV raster pre-flood |
| `S1A_IW_GRDH_VH_20190923_Patna.tif` | **DOWNLOAD NEEDED** | Full VH raster pre-flood |
| `S1A_IW_GRDH_VV_20190929_Patna.tif` | **DOWNLOAD NEEDED** | Full VV raster peak flood |
| `S1A_IW_GRDH_VH_20190929_Patna.tif` | **DOWNLOAD NEEDED** | Full VH raster peak flood |

---

## What is Sentinel-1?

Sentinel-1 is a European Space Agency (ESA) C-band Synthetic Aperture Radar (SAR) satellite.

- It sees through clouds and rain — perfect for monsoon flood mapping.
- Flood water appears as **dark pixels** (backscatter sigma-0 < -18 dB) because water reflects radar away.
- Urban buildings appear as **bright pixels** (backscatter > -8 dB).
- File size per scene: approximately 800 MB to 1.2 GB (IW GRD format).

---

## Option A: Download from Copernicus Data Space (FREE, Recommended)

**Step 1: Create Account (Free)**
- Website: https://dataspace.copernicus.eu
- Click "Register" (top right)
- Use your email, create a password.
- Verify your email.

**Step 2: Go to Browser**
- After login, click: https://browser.dataspace.copernicus.eu

**Step 3: Search for Scenes**
Draw a box over Patna on the map, then use these exact search filters:

```
Data Collection : Sentinel-1
Product Type    : GRD
Beam Mode       : IW (Interferometric Wide Swath)
Polarisation    : VV+VH
Date Range 1    : 2019-09-20  to  2019-09-25     (Pre-flood scene)
Date Range 2    : 2019-09-27  to  2019-10-01     (Peak flood scene)
```

**Step 4: Download**
- Select the scenes that cover Patna (25.3N to 25.7N, 84.8E to 85.4E).
- Click the Download button (cloud icon).
- File downloads as a `.zip` containing `.SAFE` folder.
- Extract the zip. Inside look for files ending in `measurement/*.tiff`.

**Step 5: Save to This Folder**
- Rename and save as `S1A_IW_GRDH_VV_20190923_Patna.tif` etc.

---

## Option B: Download from Microsoft Planetary Computer (Faster, No Login for Browse)

**Website:** https://planetarycomputer.microsoft.com/explore

1. Click "Explore" and search for `Sentinel-1 GRD`.
2. Set spatial filter to Patna bounding box.
3. Set date filter to September 2019.
4. Click on a scene to see STAC metadata and download links.

---

## Why Do We Need These Specific Dates?

| Date | Event |
|:---|:---|
| 23 September 2019 | Dry / Pre-flood baseline for Patna |
| 29 September 2019 | Peak of the 2019 Patna deluge (340mm in 72 hours) |

The difference (delta sigma-0) between these two scenes isolates the flooded pixels.

