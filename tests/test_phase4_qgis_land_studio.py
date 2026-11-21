"""
BHU LOKA — Phase 4 Automated Test Suite
========================================
Validates the QGIS-Inspired Professional Web GIS Workspace & Land Studio Engine:
1. Client-side GIS Engine (Assets/vendor/bhu_loka_qgis_workspace.js)
   - CRS catalogue (EPSG:4326, EPSG:3857, EPSG:32643, EPSG:32644, EPSG:32645)
   - Multi-format ingestion (CSV, KML, GeoJSON, Shapefile ZIP)
   - Vector operations (Buffer, Clip, Union, Difference, Centroid, Area, Distance)
2. FastAPI Backend GIS Processing Endpoints:
   - POST /api/v1/gis/buffer
   - POST /api/v1/gis/overlay (intersection, union, difference, clip)
   - POST /api/v1/gis/zonal-stats (Copernicus DEM elevation & slope)
   - POST /api/v1/gis/site-report (Full multi-dimensional site intelligence dossier)
3. Zero-Fabrication & Statutory BSA 2023 §63 Integrity
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent

# Import FastAPI backend
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Pipelines.bhu_loka_site_analytics_api import app

client = TestClient(app)

# Sample WGS84 Test Geometries (Hyderabad - Hussain Sagar vicinity)
SAMPLE_POLYGON_A = {
    "type": "Feature",
    "id": "feat_poly_a",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [78.4700, 17.4200],
            [78.4750, 17.4200],
            [78.4750, 17.4250],
            [78.4700, 17.4250],
            [78.4700, 17.4200]
        ]]
    },
    "properties": {"name": "Test Parcel A", "zone": "Commercial"}
}

SAMPLE_POLYGON_B = {
    "type": "Feature",
    "id": "feat_poly_b",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [78.4720, 17.4220],
            [78.4770, 17.4220],
            [78.4770, 17.4270],
            [78.4720, 17.4270],
            [78.4720, 17.4220]
        ]]
    },
    "properties": {"name": "Test Parcel B", "zone": "Residential"}
}


def test_qgis_workspace_js_asset_integrity():
    """Verify that bhu_loka_qgis_workspace.js is authored, mirrored, and contains CRS & GIS tools."""
    js_root = REPO_ROOT / "Assets" / "vendor" / "bhu_loka_qgis_workspace.js"
    js_public = REPO_ROOT / "public" / "Assets" / "vendor" / "bhu_loka_qgis_workspace.js"

    assert js_root.exists(), "Assets/vendor/bhu_loka_qgis_workspace.js missing"
    assert js_public.exists(), "public/Assets/vendor/bhu_loka_qgis_workspace.js missing"

    content = js_root.read_text(encoding="utf-8")
    assert "EPSG:4326" in content
    assert "EPSG:3857" in content
    assert "EPSG:32644" in content
    assert "parseCsv" in content
    assert "parseKml" in content
    assert "runBuffer" in content
    assert "runClip" in content
    assert "runUnion" in content
    assert "runDifference" in content
    assert "runCentroids" in content
    assert "runZonalStats" in content
    assert "runSiteReport" in content
    assert "startDistanceMeasurement" in content
    assert "startAreaMeasurement" in content
    assert "BhuLokaQgisWorkspace" in content


def test_backend_gis_buffer_endpoint():
    """Test POST /api/v1/gis/buffer computes metric UTM buffer and returns GeoJSON with processing log."""
    payload = {
        "geojson": {
            "type": "FeatureCollection",
            "features": [SAMPLE_POLYGON_A]
        },
        "distance_m": 50.0,
        "target_crs": "EPSG:4326"
    }

    resp = client.post("/api/v1/gis/buffer", json=payload)
    assert resp.status_code == 200, f"Buffer failed: {resp.text}"

    data = resp.json()
    assert data["status"] == "success"
    assert "Vector Buffer" in data["algorithm"]
    assert data["parameters"]["distance_meters"] == 50.0

    out = data["output"]
    assert out["feature_count"] == 1
    assert out["total_area_m2"] > 0
    assert out["total_area_ha"] > 0

    log = data["processing_log"]
    assert log["status"] == "COMPLETED"
    assert log["duration_ms"] >= 0


def test_backend_gis_overlay_endpoints():
    """Test POST /api/v1/gis/overlay for intersection, union, and difference operations."""
    base_fc = {"type": "FeatureCollection", "features": [SAMPLE_POLYGON_A]}
    overlay_fc = {"type": "FeatureCollection", "features": [SAMPLE_POLYGON_B]}

    for op in ["intersection", "union", "difference", "clip"]:
        payload = {
            "base_geojson": base_fc,
            "overlay_geojson": overlay_fc,
            "operation": op,
            "target_crs": "EPSG:4326"
        }
        resp = client.post("/api/v1/gis/overlay", json=payload)
        assert resp.status_code == 200, f"Overlay {op} failed: {resp.text}"

        data = resp.json()
        assert data["status"] == "success"
        assert op.upper() in data["algorithm"]
        assert data["output"]["feature_count"] >= 1
        assert data["processing_log"]["status"] == "COMPLETED"


def test_backend_gis_zonal_stats_endpoint():
    """Test POST /api/v1/gis/zonal-stats calculates topographic elevation and slope statistics."""
    payload = {
        "bounds": {
            "south": 17.4200,
            "west": 78.4700,
            "north": 17.4300,
            "east": 78.4800
        }
    }
    resp = client.post("/api/v1/gis/zonal-stats", json=payload)
    assert resp.status_code == 200, f"Zonal stats failed: {resp.text}"

    data = resp.json()
    assert data["status"] == "success"
    assert "Topographic Zonal Statistics" in data["algorithm"]

    stats = data["statistics"]
    assert "elevation_m_min" in stats
    assert "elevation_m_max" in stats
    assert "elevation_m_mean" in stats
    assert "slope_deg_mean" in stats
    assert "slope_category" in stats
    assert stats["elevation_m_min"] <= stats["elevation_m_max"]
    assert "Copernicus GLO-90" in stats["source"]


def test_backend_gis_site_report_endpoint():
    """Test POST /api/v1/gis/site-report compiles complete multi-dimensional site intelligence dossier."""
    payload = {
        "site_id": "hussain_sagar",
        "site_name": "Hussain Sagar Lake, Hyderabad"
    }
    resp = client.post("/api/v1/gis/site-report", json=payload)
    assert resp.status_code == 200, f"Site report failed: {resp.text}"

    data = resp.json()
    assert data["status"] == "success"
    assert "dossier_id" in data
    assert "Hussain Sagar" in data["site_name"]

    aoi = data["aoi_metrics"]
    assert aoi["area_ha"] > 0
    assert aoi["area_acres"] > 0
    assert aoi["area_m2"] > 0

    built = data["built_environment"]
    assert built["building_count"] > 0
    assert built["building_footprint_ha"] > 0
    assert built["road_network_total_km"] > 0
    assert "arterial_km" in built["road_hierarchy_breakdown"]

    nat = data["natural_environment"]
    assert nat["surface_water_ha"] > 0
    assert "elevation_stats" in nat

    haz = data["hazard_and_statutory_screening"]
    assert "Section 63, Bharatiya Sakshya Adhiniyam, 2023" in haz["statutory_framework"]
    assert len(haz["sha256_cryptographic_digest"]) == 64  # SHA-256 length

    reg = data["data_coverage_register"]
    assert len(reg) >= 5
    statuses = {item["status"] for item in reg}
    assert "OBSERVED" in statuses
    assert "UNAVAILABLE" in statuses
