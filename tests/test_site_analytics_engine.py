import sys
import os
import pytest
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Pipelines.bhu_loka_site_analytics_api import (
    health_check,
    search_satellite_imagery,
    run_site_analytics,
    run_change_detection,
    BoundingBox,
    ImagerySearchRequest,
    SiteAnalysisRequest,
    ChangeDetectionRequest,
    get_utm_epsg,
    run_segformer_inference,
    vectorize_class_mask,
    clean_binary_mask,
    CLASS_METADATA
)

def test_health_endpoint():
    data = health_check()
    assert data["status"] == "healthy"
    assert "segformer-b0" in data["supported_models"]
    assert "sentinel-2-l2a" in data["sensors"]

def test_utm_epsg_pan_india():
    # Patna / Bihar: ~85.15°E -> UTM Zone 45N -> EPSG:32645
    assert get_utm_epsg(85.15, 25.60) == 32645
    # Hyderabad: ~78.48°E -> UTM Zone 44N -> EPSG:32644
    assert get_utm_epsg(78.48, 17.38) == 32644
    # Mumbai: ~72.87°E -> UTM Zone 43N -> EPSG:32643
    assert get_utm_epsg(72.87, 19.07) == 32643
    # Assam / Guwahati: ~91.73°E -> UTM Zone 46N -> EPSG:32646
    assert get_utm_epsg(91.73, 26.14) == 32646

def test_imagery_search_endpoint():
    req = ImagerySearchRequest(
        bounds=BoundingBox(west=85.13, south=25.58, east=85.17, north=25.62),
        start_date="2026-01-01",
        end_date="2026-11-20",
        max_cloud_cover_pct=15.0,
        sensor="sentinel-2-l2a"
    )
    data = search_satellite_imagery(req)
    assert data["status"] == "success"
    assert data["total_matching_scenes"] >= 1
    assert "scenes" in data
    assert data["scenes"][0]["gsd_m"] == 10.0

def test_site_analysis_endpoint():
    req = SiteAnalysisRequest(
        bounds=BoundingBox(west=85.14, south=25.59, east=85.16, north=25.61),
        sensor="sentinel-2-l2a",
        model_name="segformer-b0",
        enable_ftl_buffer_audit=True,
        enable_rail_anti_hallucination=True
    )
    data = run_site_analytics(req)
    assert data["status"] == "success"
    assert "class_summary" in data
    assert "geojson" in data
    assert len(data["class_summary"]) > 0
    class_names = [c["class_name"] for c in data["class_summary"]]
    assert any(c in class_names for c in ["building", "road", "water", "canopy", "agriculture", "barren"])
    assert "EPSG:32645" in data["metadata"]["utm_crs_applied"]

def test_change_detection_endpoint():
    req = ChangeDetectionRequest(
        bounds=BoundingBox(west=85.14, south=25.59, east=85.16, north=25.61),
        t1_date="2024-03-15",
        t2_date="2026-11-14",
        sensor="sentinel-2-l2a"
    )
    data = run_change_detection(req)
    assert data["status"] == "success"
    assert "transitions" in data
    assert "new_construction_ha" in data["transitions"]

def test_morphological_noise_cleaning():
    mask = np.zeros((10, 10), dtype=bool)
    mask[2, 2] = True # Noise pixel
    mask[5:9, 5:9] = True # Real 4x4 object
    cleaned = clean_binary_mask(mask, min_pixel_size=2)
    assert cleaned[2, 2] == False # Noise removed
    assert np.all(cleaned[6:8, 6:8] == True) # Preserved
