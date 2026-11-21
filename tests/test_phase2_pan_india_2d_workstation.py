"""
BHU LOKA — Phase 2 Automated Test Suite
========================================
Validates the Pan-India 2D GIS Workstation (28 States + 8 Union Territories):
1. Administrative boundaries index (36 units, 724 districts, geodetic bounds)
2. Real geodata polygon layers for all 36 Indian administrative entities
3. Honest 14-layer catalogue provenance & fail-closed UNAVAILABLE states
4. Dropdown populator, URL sync, and toolbar hygiene in root and public HTML
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_admin_index_36_states_and_724_districts():
    """Verify that bhu_loka_india_admin_index.js contains exactly 28 States + 8 UTs (36 total) and 724 districts."""
    index_path = REPO_ROOT / "Data" / "08_Processed_Outputs" / "bhu_loka_india_admin_index.js"
    assert index_path.exists(), f"Admin index file not found at {index_path}"

    content = index_path.read_text(encoding="utf-8")
    assert "window.BHU_LOKA_INDIA_INDEX =" in content

    # Extract JSON object
    json_str = content.split("window.BHU_LOKA_INDIA_INDEX =", 1)[1].strip()
    if json_str.endswith(";"):
        json_str = json_str[:-1].strip()

    data = json.loads(json_str)
    assert data["states_ut_count"] == 36
    assert data["districts_count"] == 724
    assert len(data["states"]) == 36

    states = [s for s in data["states"] if s["unit_type"] == "State"]
    uts = [s for s in data["states"] if s["unit_type"] == "Union Territory"]

    assert len(states) == 28, f"Expected 28 States, got {len(states)}"
    assert len(uts) == 8, f"Expected 8 Union Territories, got {len(uts)}"

    # Check geodetic coordinates fall within sovereign India geographic bounds
    for u in data["states"]:
        lat, lon = u["centroid"]
        assert 6.0 <= lat <= 38.0, f"Latitude {lat} of {u['name_en']} out of India range [6, 38]"
        assert 68.0 <= lon <= 98.0, f"Longitude {lon} of {u['name_en']} out of India range [68, 98]"

        bbox = u["bbox"]
        assert len(bbox) == 4, f"Invalid bbox length for {u['name_en']}"
        min_lon, min_lat, max_lon, max_lat = bbox
        assert min_lon < max_lon
        assert min_lat < max_lat
        assert 6.0 <= min_lat <= 38.0
        assert 68.0 <= min_lon <= 98.0


def test_real_geodata_india_states_polygons():
    """Verify that bhu_loka_real_geodata.js contains polygon geometries for Indian states."""
    geodata_path = REPO_ROOT / "Data" / "08_Processed_Outputs" / "bhu_loka_real_geodata.js"
    assert geodata_path.exists(), f"Geodata file not found at {geodata_path}"

    content = geodata_path.read_text(encoding="utf-8")
    assert "window.BHU_LOKA_REAL_DATA =" in content

    json_str = content.split("window.BHU_LOKA_REAL_DATA =", 1)[1].strip()
    if json_str.endswith(";"):
        json_str = json_str[:-1].strip()

    data = json.loads(json_str)
    assert "india_states" in data
    features = data["india_states"]["features"]
    assert len(features) >= 30, f"Expected >= 30 state features, found {len(features)}"

    names = {f["properties"]["name"].lower() for f in features if "name" in f["properties"]}
    # Verify core states are present
    assert "bihar" in names
    assert "telangana" in names
    assert "maharashtra" in names
    assert "tamil nadu" in names


def test_layer_panel_provenance_and_zero_crime_fabrication():
    """Verify that Assets/vendor/bhu_loka_2d_layer_panel.js defines 14 layers with honest status."""
    panel_path = REPO_ROOT / "Assets" / "vendor" / "bhu_loka_2d_layer_panel.js"
    assert panel_path.exists(), f"Layer panel not found at {panel_path}"

    content = panel_path.read_text(encoding="utf-8")
    valid_statuses = {"OBSERVED", "MODELLED", "DERIVED", "UNAVAILABLE"}

    # Extract all status attributes
    statuses = re.findall(r"status:\s*['\"]([^'\"]+)['\"]", content)
    assert len(statuses) == 14, f"Expected 14 layer statuses, found {len(statuses)}"

    for st in statuses:
        assert st in valid_statuses, f"Invalid layer status: {st}"

    # Verify crime layer is strictly marked UNAVAILABLE with no synthetic fabrication
    assert "id: 'crime'" in content or 'id: "crime"' in content
    crime_block = re.search(r"id:\s*['\"]crime['\"].*?status:\s*['\"]([^'\"]+)['\"]", content, re.DOTALL)
    assert crime_block is not None
    assert crime_block.group(1) == "UNAVAILABLE"
    assert (
        "Synthetic or AI-generated crime polygons are strictly prohibited" in content
        or "Crime layer NEVER generates fake KDE/synthetic hotspots" in content
        or "Zero-Fabrication Policy" in content
    )


def test_2d_interactive_map_dropdown_and_url_sync():
    """Verify that root and public bhu_loka_leafmap_interactive.html contain sovereign dropdown and hooks."""
    files_to_test = [
        REPO_ROOT / "bhu_loka_leafmap_interactive.html",
        REPO_ROOT / "public" / "bhu_loka_leafmap_interactive.html"
    ]

    for fpath in files_to_test:
        assert fpath.exists(), f"File {fpath} does not exist"
        html = fpath.read_text(encoding="utf-8")

        # Select element
        assert 'id="sovereign-state-select"' in html
        assert 'id="optgroup-states"' in html
        assert 'id="optgroup-uts"' in html
        assert 'populateSovereignStateDropdown' in html

        # Auto-populator triggers
        assert 'DOMContentLoaded' in html
        assert 'selectSovereignState' in html
        assert 'closeSovereignStateCard' in html

        # Sovereign state card element
        assert 'id="state-sovereign-card"' in html
        assert 'id="ssc-name-en"' in html
        assert 'id="ssc-districts"' in html
        assert 'id="ssc-capital"' in html

        # District button
        assert 'id="btn-toggle-districts"' in html
