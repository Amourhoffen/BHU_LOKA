"""
BHU LOKA — Phase 2 India Sovereign 2D GIS & Land Studio Verification Tests
==========================================================================
Validates:
1. All 28 Indian States and 8 Union Territories are comprehensively indexed with
   authentic centroids, bounding boxes, and hierarchy metadata.
2. GeoJSON boundary vectors exist for all 36 sovereign administrative units.
3. Clean, professional 2D GIS workspace with the interactive #sovereign-state-select
   dropdown and #state-sovereign-card, with unscientific sub-bars removed.
4. Land Studio rewrite replacing automated demolition mandates with
   'POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION' under BSA 2023 §63.
5. All 38 districts of Bihar exist with verified boundary vectors.
"""

import json
import re
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

BHU_ROOT = Path(__file__).resolve().parent.parent
LEAFMAP_HTML_PATH = BHU_ROOT / "bhu_loka_leafmap_interactive.html"
ADMIN_INDEX_JS_PATH = BHU_ROOT / "Data" / "08_Processed_Outputs" / "bhu_loka_india_admin_index.js"
REAL_DATA_JS_PATH = BHU_ROOT / "Data" / "08_Processed_Outputs" / "bhu_loka_real_geodata.js"
URBAN_STUDIO_JS_PATH = BHU_ROOT / "Assets" / "vendor" / "bhu_loka_urban_studio.js"


def _load_admin_index():
    assert ADMIN_INDEX_JS_PATH.exists(), f"Missing {ADMIN_INDEX_JS_PATH}"
    text = ADMIN_INDEX_JS_PATH.read_text(encoding="utf-8")
    idx = text.find("{")
    end_idx = text.rfind("}")
    return json.loads(text[idx:end_idx + 1])


def _load_real_geodata():
    assert REAL_DATA_JS_PATH.exists(), f"Missing {REAL_DATA_JS_PATH}"
    text = REAL_DATA_JS_PATH.read_text(encoding="utf-8")
    idx = text.find("{")
    end_idx = text.rfind("}")
    return json.loads(text[idx:end_idx + 1])


def test_all_28_states_and_8_uts_indexed():
    """Verify that all 28 States and 8 UTs (36 total) are present in the sovereign index."""
    data = _load_admin_index()
    states = data.get("states", [])
    assert len(states) == 36, f"Expected 36 states/UTs, found {len(states)}"

    state_units = [s for s in states if s["unit_type"] == "State"]
    ut_units = [s for s in states if s["unit_type"] == "Union Territory"]
    assert len(state_units) == 28, f"Expected 28 States, found {len(state_units)}"
    assert len(ut_units) == 8, f"Expected 8 Union Territories, found {len(ut_units)}"

    # Check key states & UTs
    names = {s["name_en"] for s in states}
    expected_states = {
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
        "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
        "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
        "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal"
    }
    expected_uts = {
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    }
    assert expected_states.issubset(names), f"Missing States: {expected_states - names}"
    assert expected_uts.issubset(names), f"Missing UTs: {expected_uts - names}"

    # Verify geodetic bounding boxes and centroids
    for s in states:
        assert len(s["centroid"]) == 2, f"Invalid centroid for {s['name_en']}"
        assert len(s["bbox"]) == 4, f"Invalid bbox for {s['name_en']}"
        lat, lon = s["centroid"]
        assert 6.0 <= lat <= 38.0, f"Lat {lat} out of range for {s['name_en']}"
        assert 68.0 <= lon <= 98.0, f"Lon {lon} out of range for {s['name_en']}"


def test_india_states_geojson_features():
    """Verify that BHU_LOKA_REAL_DATA contains GeoJSON features for all 36 States/UTs."""
    data = _load_real_geodata()
    states_coll = data.get("india_states", {})
    assert states_coll.get("type") == "FeatureCollection"
    features = states_coll.get("features", [])
    assert len(features) == 36, f"Expected 36 features in india_states, found {len(features)}"

    feat_names = {f["properties"]["name"] for f in features if "properties" in f and "name" in f["properties"]}
    assert len(feat_names) == 36

    # Verify geometry type
    for f in features:
        geom = f.get("geometry", {})
        assert geom.get("type") in ("Polygon", "MultiPolygon"), f"Invalid geometry for {f['properties']['name']}"
        assert len(geom.get("coordinates", [])) > 0


def test_bihar_38_districts_boundary_vectors():
    """Verify that all 38 districts of Bihar have verified polygon boundaries."""
    data = _load_real_geodata()
    dist_coll = data.get("bihar_districts", {})
    assert dist_coll.get("type") == "FeatureCollection"
    features = dist_coll.get("features", [])
    assert len(features) == 38, f"Expected 38 Bihar districts, found {len(features)}"

    dist_names = {f["properties"]["name"] for f in features}
    assert "Patna" in dist_names
    assert "Gaya" in dist_names
    assert "Muzaffarpur" in dist_names
    assert "Bhagalpur" in dist_names
    assert "Nalanda" in dist_names


def test_bhu_loka_leafmap_clean_sovereign_ui():
    """Verify 2D GIS workspace has clean sovereign controls and unscientific items removed."""
    html = LEAFMAP_HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # 1. State / UT Dropdown
    sel = soup.find("select", id="sovereign-state-select")
    assert sel is not None, "Missing #sovereign-state-select dropdown"
    opt_states = soup.find("optgroup", id="optgroup-states")
    assert opt_states is not None, "Missing #optgroup-states"
    opt_uts = soup.find("optgroup", id="optgroup-uts")
    assert opt_uts is not None, "Missing #optgroup-uts"

    # 2. Sovereign State Info Card
    card = soup.find("div", id="state-sovereign-card")
    assert card is not None, "Missing #state-sovereign-card info card"
    assert soup.find("div", id="ssc-name-en") is not None
    assert soup.find("strong", id="ssc-capital") is not None
    assert soup.find("strong", id="ssc-districts") is not None

    # 3. Unscientific Street Intel sub-bar removed
    unscientific_nav = soup.find("nav", id="india-intel-main-nav")
    assert unscientific_nav is None, "Unscientific #india-intel-main-nav must be removed"

    # 4. Joke/hackathon buttons removed or scientifically renamed
    assert "Dancing with the SARs" not in html, "Joke button 'Dancing with the SARs' must be removed"
    assert "SAR Hero (NASA 2026)" not in html, "Joke link 'SAR Hero (NASA 2026)' must be removed"
    assert soup.find("button", id="btn-sar-deluge") is not None, "Missing scientific #btn-sar-deluge button"

    # 5. Scientific functions wired
    assert "selectSovereignState" in html
    assert "populateSovereignStateDropdown" in html
    assert "STATE_CAPITALS" in html


def test_urban_studio_land_intelligence_screening_labels():
    """Verify Land Studio rewrite: zero automated demolition claims, BSA 2023 compliance."""
    js_text = URBAN_STUDIO_JS_PATH.read_text(encoding="utf-8")

    # 1. Zero automated demolition mandate claims
    assert "DEMOLITION / NOTICE MANDATED" not in js_text, "DEMOLITION / NOTICE MANDATED must not exist"
    assert "Section 23 Demolition Mandated" not in js_text, "Section 23 Demolition Mandated must not exist"

    # 2. Proper scientific screening terminology
    assert "POTENTIAL SPATIAL OVERLAP" in js_text
    assert "REQUIRES OFFICIAL VERIFICATION" in js_text or "Requires Official Verification" in js_text

    # 3. Legal and electronic evidence references
    assert "BSA 2023" in js_text or "Bharatiya Sakshya Adhiniyam" in js_text

    # 4. Unverified boundaries marked properly
    assert "LEGAL BOUNDARY UNVERIFIED" in js_text
