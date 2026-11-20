import pytest
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_watermark_free_basemaps():
    """Verify that CartoDB raster tile watermarked URL is removed from urban studio and html."""
    studio_path = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
    with open(studio_path, "r", encoding="utf-8") as f:
        studio_js = f.read()

    # Must NOT have CartoDB voyager watermark in active baseLayers
    assert "rastertiles/voyager" not in studio_js, "Found legacy CartoDB voyager basemap which shows API KEY REQUIRED watermark"
    assert "tile.openstreetmap.fr/osmfr" in studio_js, "Missing OpenStreetMap France clean basemap"
    assert "Canvas/World_Dark_Gray_Base" in studio_js, "Missing Esri Dark Gray Canvas basemap"

def test_railway_and_road_anti_hallucination_in_building_generators():
    """Verify that building generators contain railway, road, water, and park anti-hallucination masks."""
    studio_path = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
    with open(studio_path, "r", encoding="utf-8") as f:
        studio_js = f.read()

    # Check _generateOpenBuildingsClientSide
    assert "railSegments" in studio_js, "Missing railway segment extraction in building generators"
    assert "roadSegments" in studio_js, "Missing road segment extraction in building generators"
    assert "isOverRail" in studio_js, "Missing railway collision check in building generators"
    assert "isOverRoad" in studio_js, "Missing road collision check in building generators"
    assert "isOverWater" in studio_js, "Missing water polygon collision check"
    assert "isOverPark" in studio_js, "Missing park / sports pitch collision check"

def test_circle_aoi_support():
    """Verify Circle AOI draw method and conversion exist in urban studio."""
    studio_path = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
    with open(studio_path, "r", encoding="utf-8") as f:
        studio_js = f.read()

    assert "startCircleDraw" in studio_js, "Missing startCircleDraw in UrbanLeafletEngine"
    assert "window.startUrbanCircleDraw" in studio_js, "Missing window.startUrbanCircleDraw global binding"
    assert "drawCircle: true" in studio_js, "Geoman controls missing drawCircle: true"
    assert "getRadius" in studio_js, "Missing L.Circle radius extraction for polygon approximation"

def test_dual_mode_spatial_mesh():
    """Verify dual-mode micro-zoning supporting both Hex (honeycomb) and Square grid."""
    studio_path = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
    with open(studio_path, "r", encoding="utf-8") as f:
        studio_js = f.read()

    assert "_buildSpatialMesh" in studio_js, "Missing _buildSpatialMesh method"
    assert "meshType === 'square'" in studio_js, "Missing Square micro-grid mode logic"
    assert "window.setUrbanMeshType" in studio_js, "Missing window.setUrbanMeshType global switcher"
    assert "isRailwayCorridor" in studio_js, "Missing railway corridor detection in spatial mesh"

def test_html_ui_controls():
    """Verify HTML UI contains Circle AOI, Zone Grid toggle, and AI Spectral Object Decoder."""
    for html_file in ["index.html", "bhu_loka_cyber_dashboard.html"]:
        p = os.path.join(BASE_DIR, html_file)
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        assert "urban-draw-circle" in content, f"{html_file} missing #urban-draw-circle button"
        assert "urban-mesh-hex" in content, f"{html_file} missing #urban-mesh-hex toggle"
        assert "urban-mesh-square" in content, f"{html_file} missing #urban-mesh-square toggle"
        assert "urban-spectral-legend" in content, f"{html_file} missing #urban-spectral-legend AI Decoder"
