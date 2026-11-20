"""
BHU LOKA — Multi-Source Extraction Service & AOI Pipeline Tests
================================================================
Validates multi-source building footprint extraction (OSM + Google Open Buildings v3 + Vision ML),
IoU > 0.5 deduplication, Sentinel-2 L2A NDVI > 0.4 canopy raster reporting, comprehensive road network,
density modes (Strict, Balanced, Dense), spatial chunking for AOIs > 1 km², and completeness reports.
"""

import sys
from pathlib import Path
import pytest

BHU_ROOT = Path(__file__).resolve().parent.parent
PIPELINES_DIR = BHU_ROOT / "Pipelines"
if str(PIPELINES_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINES_DIR))

from bhu_loka_extraction_service import (
    MultiSourceExtractionService,
    MultiSourceMetrics,
    LayerCompleteness,
    calculate_polygon_iou,
    bounds_area_m2,
    haversine_distance_m,
    extraction_service
)


def test_extraction_service_instance():
    """Verify that extraction service instance is initialized and operational."""
    service = MultiSourceExtractionService(cache_ttl_seconds=300)
    assert service is not None
    assert service.cache_ttl == 300
    assert len(service._cache) == 0


def test_polygon_iou_calculation():
    """Verify IoU calculation for identical, non-overlapping, and intersecting polygons."""
    import shapely.geometry as sgeom

    # Identical 10x10 squares
    poly_a = sgeom.box(0, 0, 10, 10)
    poly_b = sgeom.box(0, 0, 10, 10)
    assert abs(calculate_polygon_iou(poly_a, poly_b) - 1.0) < 1e-4

    # Non-overlapping squares
    poly_c = sgeom.box(20, 20, 30, 30)
    assert calculate_polygon_iou(poly_a, poly_c) == 0.0

    # 50% overlapping squares (5x10 overlap inside two 10x10 = 50 / 150 = 0.333)
    poly_d = sgeom.box(5, 0, 15, 10)
    iou_d = calculate_polygon_iou(poly_a, poly_d)
    assert abs(iou_d - (50.0 / 150.0)) < 1e-3


def test_spatial_chunking_grid_for_large_aoi():
    """Verify AOIs > 1 km² are chunked into tiles."""
    service = MultiSourceExtractionService()

    # Small AOI (500m x 500m) -> 1 chunk
    small_chunks = service.chunk_aoi_if_needed(25.5900, 85.1500, 25.5945, 85.1550, max_chunk_km=1.0)
    assert len(small_chunks) == 1

    # Large AOI (2.5 km x 2.5 km) -> multiple chunks
    large_chunks = service.chunk_aoi_if_needed(25.5700, 85.1300, 25.6000, 85.1600, max_chunk_km=1.0)
    assert len(large_chunks) >= 4
    for chk in large_chunks:
        assert "south" in chk and "north" in chk and "west" in chk and "east" in chk
        assert chk["north"] > chk["south"]
        assert chk["east"] > chk["west"]


def test_density_modes_and_source_tagging():
    """
    Verify density modes:
    - Strict: OSM only
    - Balanced: OSM + Google Open Buildings v3 (deduped by IoU > 0.5)
    - Dense: All sources + Vision ML
    Each feature must carry a `source` property.
    """
    service = MultiSourceExtractionService()
    south, west, north, east = 25.5895, 85.1530, 25.5985, 85.1630

    # 1. Strict mode
    res_strict = service.extract_aoi(south, west, north, east, location_name="Rajendra Nagar", mode="strict")
    assert res_strict["ok"] is True
    assert res_strict["metrics"]["density_mode"] == "strict"
    for feat in res_strict["layers"]["buildings"]["features"]:
        assert feat["properties"]["source"] == "osm"

    # 2. Balanced mode
    res_balanced = service.extract_aoi(south, west, north, east, location_name="Rajendra Nagar", mode="balanced")
    assert res_balanced["ok"] is True
    assert res_balanced["metrics"]["density_mode"] == "balanced"
    sources_balanced = {f["properties"]["source"] for f in res_balanced["layers"]["buildings"]["features"]}
    assert "osm" in sources_balanced
    assert "open_buildings" in sources_balanced
    assert "microsoft_ml" in sources_balanced
    assert res_balanced["metrics"]["microsoft_buildings"] > 0
    # Balanced count must strictly exceed Strict count
    assert res_balanced["metrics"]["total_buildings"] > res_strict["metrics"]["total_buildings"]

    # 3. Dense mode
    res_dense = service.extract_aoi(south, west, north, east, location_name="Rajendra Nagar", mode="dense")
    assert res_dense["ok"] is True
    assert res_dense["metrics"]["density_mode"] == "dense"
    sources_dense = {f["properties"]["source"] for f in res_dense["layers"]["buildings"]["features"]}
    assert "osm" in sources_dense
    assert "open_buildings" in sources_dense
    assert "ml" in sources_dense
    assert res_dense["metrics"]["total_buildings"] >= res_balanced["metrics"]["total_buildings"]


def test_rajendra_nagar_patna_before_after_comparison():
    """
    Direct test comparing baseline counts before vs after for Rajendra Nagar, Patna AOI.
    Problem: OSM alone had only ~167–194 buildings and ~7% green.
    Task: Multi-source extraction must recover full building stock and true Sentinel-2 canopy.
    """
    service = MultiSourceExtractionService()
    south, west, north, east = 25.5895, 85.1530, 25.5985, 85.1630

    res = service.extract_aoi(south, west, north, east, location_name="Rajendra Nagar, Patna", mode="balanced")
    m = res["metrics"]

    # Buildings: Baseline was 194 (OSM only). Multi-source should be >= 500
    assert m["osm_buildings"] >= 100
    assert m["open_buildings"] >= 400
    assert m["total_buildings"] >= 500, f"Expected >= 500 buildings, got {m['total_buildings']}"

    # Vegetation: Baseline was 7.3% (sparse OSM parks). Sentinel-2 NDVI > 0.4 should be >= 18%
    assert m["canopy_coverage_pct"] >= 18.0, f"Expected >= 18% canopy, got {m['canopy_coverage_pct']}%"

    # Roads: Full highway hierarchy included
    assert m["total_roads"] >= 100
    assert m["road_density_km_per_km2"] >= 15.0

    # Status line must accurately report counts per source
    assert "OSM" in res["status_line"]
    assert "Open Buildings" in res["status_line"]
    assert "Canopy" in res["status_line"]
    assert "DEM OK" in res["status_line"]


def test_completeness_report_zero_fake_data():
    """Verify structured completeness report has valid layer metadata, confidence, and status."""
    service = MultiSourceExtractionService()
    res = service.extract_aoi(25.5895, 85.1530, 25.5985, 85.1630, mode="balanced")
    report = res["completeness_report"]

    assert len(report) >= 5
    layer_names = [r["layer_name"] for r in report]
    assert any("Buildings" in name for name in layer_names)
    assert any("Road Network" in name for name in layer_names)
    assert any("Canopy" in name for name in layer_names)
    assert any("Water" in name for name in layer_names)
    assert any("DEM" in name for name in layer_names)

    for item in report:
        assert 0.0 <= item["confidence_score"] <= 1.0
        assert item["status"] in ("observed", "partial", "modelled", "unavailable")
        assert len(item["sources_used"]) >= 1
        assert item["area_m2"] >= 0
