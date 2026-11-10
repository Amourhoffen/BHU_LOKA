
"""
BHU LOKA - Automated Data Availability Check
Tests which datasets can be downloaded without login/credentials.
"""
import urllib.request
import urllib.error
import json

results = {}

def check_url(name, url, expected_content_type=None):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            content_type = r.headers.get("Content-Type", "")
            size = r.headers.get("Content-Length", "unknown")
            results[name] = {
                "status": "ACCESSIBLE",
                "http_code": r.status,
                "content_type": content_type,
                "size_bytes": size,
                "url": url
            }
            print(f"[OK]  {name}: {r.status}, size={size}, type={content_type[:40]}")
    except urllib.error.HTTPError as e:
        results[name] = {"status": f"HTTP_ERROR_{e.code}", "url": url}
        print(f"[ERR] {name}: HTTP {e.code}")
    except Exception as e:
        results[name] = {"status": f"FAILED: {str(e)[:60]}", "url": url}
        print(f"[ERR] {name}: {str(e)[:80]}")

print("=" * 70)
print("CHECKING NO-LOGIN DATA SOURCES FOR BHU LOKA")
print("=" * 70)

# 1. GADM Boundaries (India Level 2)
check_url(
    "GADM_India_L2_GeoPackage",
    "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_IND.gpkg"
)

# 2. OpenTopography SRTM API (public endpoint, no key for small areas)
check_url(
    "OpenTopography_SRTM_API",
    "https://portal.opentopography.org/API/globaldem?demtype=SRTMGL1&south=25.20&north=25.75&west=84.68&east=86.10&outputFormat=GTiff&API_Key=demoapikeyot"
)

# 3. WorldPop India 2020 1km
check_url(
    "WorldPop_India_2020_1km",
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/IND/ind_ppp_2020_1km_Aggregated.tif"
)

# 4. WorldPop India 2020 100m (constrained)
check_url(
    "WorldPop_India_2020_100m_constrained",
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/IND/ind_ppp_2020_UNadj_constrained.tif"
)

# 5. Planetary Computer STAC API (public, no auth for metadata)
check_url(
    "PlanetaryComputer_Sentinel1_STAC_API",
    "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-1-grd"
)

# 6. Copernicus 30m DEM (GLO-30) via AWS Open Data
check_url(
    "Copernicus_GLO30_DEM_AWS",
    "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N25_00_E084_00_DEM/Copernicus_DSM_COG_10_N25_00_E084_00_DEM.tif"
)

# 7. CGIAR SRTM (Alternative)
check_url(
    "CGIAR_SRTM_Tile_N25E084",
    "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_55_07.zip"
)

# 8. IMD Gridded Data (check if public page accessible)
check_url(
    "IMD_GridData_Portal",
    "https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html"
)

# 9. NASA EarthData MODIS public endpoint
check_url(
    "NASA_CMR_MODIS_LST_Search",
    "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MOD11A1&bounding_box=84.68,25.20,86.10,25.75&temporal=2019-04-01T00:00:00Z,2019-06-30T23:59:59Z&page_size=5"
)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
accessible = [k for k, v in results.items() if v["status"] == "ACCESSIBLE"]
print(f"Accessible without login: {len(accessible)}/{len(results)}")
for k in accessible:
    print(f"  - {k}")
