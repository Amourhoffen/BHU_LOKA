# Folder 01: Administrative Boundaries (Patna District)

## Status: ALREADY DOWNLOADED (Real Data Present)

| File | Size | Source | Status |
|:---|:---:|:---|:---:|
| `patna_district_boundary.geojson` | 474 KB | OpenStreetMap Nominatim | DONE |
| `patna_urban_boundary.geojson` | 168 KB | OpenStreetMap Nominatim | DONE |
| `patna_metadata.json` | 1 KB | Computed BBox | DONE |

## What These Files Contain

- `patna_district_boundary.geojson`: Official Patna District polygon with 5,649 real coordinate vertices.
- `patna_urban_boundary.geojson`: Patna Municipal Corporation (PMC) urban boundary.
- `patna_metadata.json`: Bounding box — Longitude 84.68 to 86.07 E, Latitude 25.20 to 25.73 N.

## If You Need to Re-Download

**Website:** https://nominatim.openstreetmap.org

**Direct API call (paste in browser):**
```
https://nominatim.openstreetmap.org/search?q=Patna+District,+Bihar,+India&format=geojson&polygon_geojson=1
```

**Alternative (GADM — Higher quality administrative boundaries):**

1. Go to: https://gadm.org/download_country.html
2. Select Country: **India**
3. Select Level: **Level 2** (District level)
4. Download format: **GeoJSON**
5. Open in QGIS or Python, filter for `NAME_2 == "Patna"`
6. Save filtered file as `patna_district_boundary_gadm.geojson` in this folder.

## No Registration Required for Either Source.

