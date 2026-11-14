# Folder 03: Optical Sentinel-2 Data (Land Cover, NDVI, NDBI, Impervious Surface)

## Status: NOT DOWNLOADED — Full Download Needed

| File to Download | Description | Period |
|:---|:---|:---:|
| `S2_Patna_20190501_B04_B08_B11.tif` | Bands 4, 8, 11 (pre-monsoon land cover) | May 2019 |
| `S2_Patna_20191101_B04_B08_B11.tif` | Bands 4, 8, 11 (post-flood land cover) | Nov 2019 |

---

## What is Sentinel-2?

Sentinel-2 is an ESA optical satellite with 13 spectral bands at 10m to 60m resolution.

We use 3 specific bands:
| Band | Wavelength | Use in BHU LOKA |
|:---:|:---:|:---|
| Band 4 (Red) | 665 nm | NDVI vegetation calculation |
| Band 8 (NIR) | 842 nm | NDVI vegetation calculation |
| Band 11 (SWIR) | 1610 nm | NDBI built-up / impervious surface |

**Key indices we compute:**
- `NDVI = (B8 - B4) / (B8 + B4)` — Vegetation density
- `NDBI = (B11 - B8) / (B11 + B8)` — Built-up / impervious fraction
- `MNDWI = (B3 - B11) / (B3 + B11)` — Surface water extent

---

## Download Instructions (Copernicus Data Space — Same Account as Sentinel-1)

**Website:** https://browser.dataspace.copernicus.eu

**Search Filters:**
```
Data Collection : Sentinel-2
Product Type    : S2MSI2A  (Level-2A, atmospherically corrected — ALWAYS use L2A)
Cloud Cover     : Less than 20%
Date Range 1    : 2019-05-01  to  2019-05-31    (pre-monsoon, dry season)
Date Range 2    : 2019-11-01  to  2019-11-30    (post-flood, dry again)
Area            : Patna (draw box on map, 25.2N–25.75N, 84.7E–86.1E)
```

**Step-by-step:**
1. Login at https://dataspace.copernicus.eu
2. Go to https://browser.dataspace.copernicus.eu
3. Draw bounding box over Patna district.
4. Set above filters, click "Search".
5. Pick a scene with cloud cover under 15% — look at the thumbnail preview.
6. Click Download. File downloads as a `.zip` (approx 800 MB to 1 GB).
7. Extract. Inside the `GRANULE/.../IMG_DATA/R10m/` folder you will find:
   - `*_B04_10m.jp2` (Red)
   - `*_B08_10m.jp2` (NIR)
   - `*_B11_20m.jp2` (SWIR, 20m — will be resampled to 10m)
8. Save these in this folder.

---

## Shortcut: EO Browser (Easier Visual Interface)

**Website:** https://apps.sentinel-hub.com/eo-browser

1. Create free account at https://www.sentinel-hub.com
2. Browse to Patna on the map.
3. Select Sentinel-2 L2A.
4. Set date and cloud cover filter.
5. Use "Analytical" download to get specific bands as GeoTIFF.

---

## Why Do We Choose May 2019?

May 2019 is pre-monsoon — maximum land surface temperature, minimum vegetation, clearest view of impervious built-up areas. This matches our thermodynamic desiccation hypothesis: recording land cover and heat stress just before the June monsoon onset.

