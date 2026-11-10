"""
BHU LOKA (भूलोक) - Google Earth Engine (GEE) & Google Earth Tile Connector
Integrates the local `Repos/earthengine-api` Python SDK with BHU LOKA's
sovereign multi-hazard analytics for All-India (36 Sovereign States/UTs)
and Patna/Bihar core micro-topography.

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


WORKSPACE_DIR = Path(__file__).resolve().parent.parent
GEE_REPO_PYTHON = WORKSPACE_DIR / "Repos" / "earthengine-api" / "python"

if GEE_REPO_PYTHON.exists() and str(GEE_REPO_PYTHON) not in sys.path:
    sys.path.insert(0, str(GEE_REPO_PYTHON))


GOOGLE_EARTH_TILE_ENDPOINTS: Dict[str, Dict[str, Any]] = {
    "google_earth_hybrid_india": {
        "label": "Google Earth Satellite + India Borders Hybrid (gl=IN)",
        "url": "https://mt{s}.google.com/vt/lyrs=y&gl=IN&x={x}&y={y}&z={z}",
        "subdomains": ["0", "1", "2", "3"],
        "attribution": "Google Earth Imagery &amp; Survey-aligned India View (gl=IN)",
        "max_zoom": 20,
    },
    "google_maps_india_sovereign": {
        "label": "Google Maps Official India View (gl=IN)",
        "url": "https://mt{s}.google.com/vt/lyrs=m&gl=IN&x={x}&y={y}&z={z}",
        "subdomains": ["0", "1", "2", "3"],
        "attribution": "Google Maps India (gl=IN)",
        "max_zoom": 20,
    },
    "google_earth_satellite": {
        "label": "Google Earth Pure High-Res Satellite",
        "url": "https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "subdomains": ["0", "1", "2", "3"],
        "attribution": "Google Earth Satellite",
        "max_zoom": 20,
    },
    "google_terrain_india": {
        "label": "Google Terrain & Relief (gl=IN)",
        "url": "https://mt{s}.google.com/vt/lyrs=p&gl=IN&x={x}&y={y}&z={z}",
        "subdomains": ["0", "1", "2", "3"],
        "attribution": "Google Terrain India (gl=IN)",
        "max_zoom": 20,
    },
}


GEE_COLLECTIONS: Dict[str, str] = {
    "sentinel1_sar": "COPERNICUS/S1_GRD",
    "copernicus_dem_30m": "COPERNICUS/DEM/GLO30",
    "modis_lst_daily": "MODIS/061/MOD11A1",
    "jrc_surface_water": "JRC/GSW1_4/GlobalSurfaceWater",
    "worldpop_population": "WorldPop/GP/100m/pop",
}


class BhuLokaGoogleEarthConnector:
    """
    Connects BHU LOKA (भूलोक) to `Repos/earthengine-api` Python client &
    verified Google Earth / Google Maps (gl=IN) geospatial data layers.
    """

    def __init__(self, project_id: Optional[str] = None) -> None:
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("EE_PROJECT")
        self.ee = None
        self.sdk_available = False
        self.credentials_present = self._has_ee_credentials()
        self.initialized = False
        self._load_sdk()

    @staticmethod
    def _has_ee_credentials() -> bool:
        cred_file = Path.home() / ".config" / "earthengine" / "credentials"
        return cred_file.exists() or bool(os.environ.get("EARTHENGINE_TOKEN"))

    def _load_sdk(self) -> None:
        try:
            import ee  # type: ignore
            self.ee = ee
            self.sdk_available = True
        except Exception:
            self.sdk_available = False

    def initialize(self) -> Dict[str, Any]:
        """Attempt live GEE initialization only when local OAuth/service credentials exist."""
        if not self.sdk_available or self.ee is None:
            return {
                "ok": False,
                "reason": "earthengine Python runtime dependencies (e.g. httplib2/google-auth) missing in active interpreter.",
                "repo_path": str(GEE_REPO_PYTHON),
            }
        if not self.credentials_present:
            return {
                "ok": False,
                "reason": "No ~/.config/earthengine/credentials found. Run `earthengine authenticate` to query live cloud rasters; Google Earth gl=IN tile layers & local GeoTIFFs remain active.",
                "sdk_available": True,
            }
        try:
            if self.project_id:
                self.ee.Initialize(project=self.project_id)
            else:
                self.ee.Initialize()
            self.initialized = True
            return {"ok": True, "project_id": self.project_id or "default", "sdk_available": True}
        except Exception as exc:
            return {"ok": False, "reason": str(exc), "sdk_available": True}

    def get_tile_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Return verified Google Earth & Google Maps India (gl=IN) tile definitions."""
        return GOOGLE_EARTH_TILE_ENDPOINTS

    def generate_gee_patna_workflow(
        self,
        bbox: Optional[List[float]] = None,
        start_date: str = "2019-09-20",
        end_date: str = "2019-10-05",
    ) -> str:
        """
        Return an exact reproducible Earth Engine Python script grounded in BHU LOKA's
        verified satellite collection IDs (COPERNICUS/S1_GRD, GLO30, MOD11A1, JRC GSW).
        """
        w, s, e, n = bbox or [84.95, 25.52, 85.28, 25.66]
        return f"""# BHU LOKA (भूलोक) - Live Google Earth Engine Multi-Hazard Extractor
import ee
ee.Initialize()

aoi = ee.Geometry.Rectangle([{w}, {s}, {e}, {n}])

# 1. ESA Sentinel-1 C-Band SAR Flood & Urban Double-Bounce
s1_flood = (
    ee.ImageCollection("{GEE_COLLECTIONS['sentinel1_sar']}")
    .filterBounds(aoi)
    .filterDate("{start_date}", "{end_date}")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .select(["VV", "VH"])
    .median()
    .clip(aoi)
)

# 2. Copernicus 30m DEM & Depression Sink Terrain
dem = (
    ee.ImageCollection("{GEE_COLLECTIONS['copernicus_dem_30m']}")
    .filterBounds(aoi)
    .mosaic()
    .select("DEM")
    .clip(aoi)
)

# 3. NASA Terra MODIS Peak Summer Heatwave LST (2019)
modis_lst = (
    ee.ImageCollection("{GEE_COLLECTIONS['modis_lst_daily']}")
    .filterBounds(aoi)
    .filterDate("2019-04-01", "2019-06-30")
    .select("LST_Day_1km")
    .max()
    .multiply(0.02)
    .subtract(273.15)
    .clip(aoi)
)

# 4. JRC Permanent vs Seasonal Water Occurrence
gsw = ee.Image("{GEE_COLLECTIONS['jrc_surface_water']}").select("occurrence").clip(aoi)
"""

    def summary(self) -> Dict[str, Any]:
        return {
            "repo_sdk_path": str(GEE_REPO_PYTHON),
            "repo_exists": GEE_REPO_PYTHON.exists(),
            "sdk_importable": self.sdk_available,
            "credentials_present": self.credentials_present,
            "live_gee_initialized": self.initialized,
            "collections": GEE_COLLECTIONS,
            "tile_endpoints": list(GOOGLE_EARTH_TILE_ENDPOINTS.keys()),
        }


if __name__ == "__main__":
    conn = BhuLokaGoogleEarthConnector()
    print("=== BHU LOKA GOOGLE EARTH & GEE CONNECTOR STATUS ===")
    for k, v in conn.summary().items():
        print(f"  {k}: {v}")
