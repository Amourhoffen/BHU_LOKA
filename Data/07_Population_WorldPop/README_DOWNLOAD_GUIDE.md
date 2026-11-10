# Folder 07: WorldPop Population Density Data

## Status: NOT DOWNLOADED

| File to Download | Description |
|:---|:---|
| `worldpop_india_2020_100m.tif` | India-wide 100m population density raster |
| `worldpop_patna_2020_100m.tif` | Clipped to Patna district (our processing script does this) |

---

## What is WorldPop?

WorldPop is a peer-reviewed, freely available population dataset published by the University of Southampton. It provides population density estimates at 100m resolution, based on census data plus satellite imagery-based disaggregation.

For BHU LOKA, population density is the **Exposure (E)** term in the Risk equation:

```
Risk(s) = Hazard(s) × Exposure(s) × Vulnerability(s)
```

Where Exposure(s) = number of people at coordinate s who would be affected by the flood.

---

## Download Instructions (Direct Download — No Account Needed)

**Website:** <https://www.worldpop.org/geodata/listing?id=29>

**Step 1: Go to the portal**

- URL: <https://hub.worldpop.org/geodata/listing?id=29>

**Step 2: Select Parameters**

```
Country     : India (IND)
Year        : 2020  (most recent with high accuracy)
Resolution  : 100m  (1km is too coarse for ward-level analysis)
Type        : Population Count (not density)
```

**Step 3: Download**

- Click Download for `ind_ppp_2020_1km_Aggregated.tif` (1km, 15 MB) OR
- Click Download for `ind_ppp_2020_UNadj_constrained.tif` (100m, ~600 MB — preferred)
- Save to this folder.

**Direct FTP Link (Faster):**

```
https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/IND/ind_ppp_2020_1km_Aggregated.tif
```

---

## Alternative: ArcGIS Hub India Census Data

**Website:** <https://hub.arcgis.com/datasets/india-census-2011-district-wise-population>

- Download district-wise 2011 census data as shapefile.
- Merge with Patna District boundary.
- Use as coarse population estimate for ward-level disaggregation.

---

## Why Population Data Matters

Without population density:

- We know WHERE flooding happens (from SAR).
- We know HOW SEVERELY (from elevation and rainfall).
- But we do NOT know HOW MANY PEOPLE are at risk.

Population density is essential to convert a physical hazard map into a human risk map — which is the actual BHU LOKA output for urban planners and BSDMA.
