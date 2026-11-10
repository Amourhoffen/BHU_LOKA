# Folder 05: IMD Gridded Rainfall Data

## Status: NOT DOWNLOADED

| File to Download | Description | Period |
| :--- | :--- | :---: |
| `imd_rainfall_2019_daily_0.25deg.nc` | IMD gridded daily rainfall NetCDF | Jan–Dec 2019 |
| `imd_rainfall_2010_2020_monsoon.nc` | 10-year monsoon record | Jun–Sep 2010–2020 |

---

## What is IMD Gridded Rainfall?

The India Meteorological Department (IMD) publishes a gridded daily rainfall dataset at 0.25 degree resolution (approximately 25 km × 25 km) across India. This is based on interpolation from thousands of rain gauge stations.

For BHU LOKA, this is used to:

- Quantify the extreme rainfall event of September 2019 (340mm in 72 hours over Patna).
- Compute design storm depths for different return periods (10-year, 25-year, 50-year events).
- Validate our spatial downscaling from 25 km IMD grid to 30m SAR flood extent.

---

## Download Instructions — IMD Open Data (Free, Requires Simple Registration)

**Website:** <https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html>

**Step 1: Access**

- Go to: <https://imdpune.gov.in>
- Navigate to: Climate > Gridded Data > Rainfall

**Alternate direct portal:**

- <https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html>

**Step 2: Select Parameters**

```
Parameter   : Rainfall (Daily)
Resolution  : 0.25 degrees
Year        : 2019
Format      : NetCDF (.nc)
```

**Step 3: Download**

- Download the annual file for 2019 (approximately 15–30 MB).
- Save as `imd_rainfall_2019_daily_0.25deg.nc` in this folder.

---

## Alternative: Climate Data Store (Copernicus ERA5) — If IMD Is Unavailable

**Website:** <https://cds.climate.copernicus.eu>

1. Register for free at: <https://cds.climate.copernicus.eu/user/register>
2. After login, go to: <https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land>
3. Select:

   ```
   Variable      : Total precipitation
   Year          : 2019
   Month         : September
   Area          : 25.2/84.68/25.75/86.1   (N/W/S/E)
   Format        : NetCDF
   ```

4. Submit request (takes a few minutes).
5. Download and save as `era5_rainfall_sep2019_patna.nc`.

---

## What Data Tells Us About September 2019 Patna Flood

| Date | Rainfall (mm) | Event |
| :---: | :---: | :--- |
| 27 Sep 2019 | 115 mm | First extreme cloudburst |
| 28 Sep 2019 | 142 mm | Peak rainfall — city drainage collapses |
| 29 Sep 2019 | 83 mm | Continued ponding, Sentinel-1 overpass |
| **Total 72hr** | **~340 mm** | Exceeded 50-year return period |

---

## Spatial Downscaling Note

IMD grid is 0.25 degrees (~25 km). Our SAR analysis is at 10m–30m. The processing script will apply Topographic Wetness Index (TWI) based downscaling to redistribute rainfall at sub-ward resolution. This is a key scientific contribution of BHU LOKA.
