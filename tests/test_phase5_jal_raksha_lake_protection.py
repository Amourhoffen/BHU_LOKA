"""
BHU LOKA (भूलोक) — Phase 5 Jal Raksha Lake Protection & Land Studio Test Suite
================================================================================
Validates Telangana Water Bodies (Hussain Sagar, Osman Sagar, Durgam Cheruvu,
Himayat Sagar, Shamirpet Lake, Fox Sagar), Gazetted FTL 30m Statutory Buffers,
Decadal Change Transition Matrix (2014 Landsat-8 OLI vs 2026 Sentinel-2 MSI),
and Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023) Legal Screening.
"""

import os
import sys
import pytest
from shapely.geometry import shape

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Pipelines.bhu_loka_site_analytics_api import (
    TELANGANA_LAKE_CATALOG,
    BSA_2023_DISCLAIMER,
    get_telangana_lake_catalog,
    get_lake_ftl_buffer,
    run_change_detection,
    generate_lake_geometry,
    build_7x7_transition_matrix,
    ChangeDetectionRequest,
    BoundingBox
)


def test_telangana_lake_catalog_completeness():
    """Verify all 6 key Telangana lakes are registered with gazetted administrative metadata."""
    res = get_telangana_lake_catalog()
    assert res["status"] == "success"
    assert res["total_catalog_lakes"] == 6

    expected_lakes = [
        "hussain_sagar", "osman_sagar", "durgam_cheruvu",
        "himayat_sagar", "shamirpet_lake", "fox_sagar"
    ]
    catalog_ids = [lake["id"] for lake in res["lakes"]]
    for eid in expected_lakes:
        assert eid in catalog_ids, f"Lake {eid} missing from catalog"

    # Verify gazetted FTL areas against official records
    hussain = TELANGANA_LAKE_CATALOG["hussain_sagar"]
    assert hussain["gazetted_ftl_acres"] == 490.38
    assert hussain["statutory_buffer_m"] == 30.0

    osman = TELANGANA_LAKE_CATALOG["osman_sagar"]
    assert osman["gazetted_ftl_acres"] == 6400.0
    assert "GO Ms No. 111" in osman["governing_order"]

    durgam = TELANGANA_LAKE_CATALOG["durgam_cheruvu"]
    assert durgam["gazetted_ftl_acres"] == 84.15
    assert durgam["statutory_buffer_m"] == 30.0


def test_lake_ftl_buffer_endpoint():
    """Verify GeoJSON FeatureCollection generation with exact 30m buffer."""
    fc = get_lake_ftl_buffer("hussain_sagar")
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 2

    # Feature 0: FTL
    ftl_feat = fc["features"][0]
    assert ftl_feat["properties"]["layer_type"] == "GAZETTED_FULL_TANK_LEVEL"
    assert ftl_feat["properties"]["gazetted_area_acres"] == 490.38
    poly_ftl = shape(ftl_feat["geometry"])
    assert poly_ftl.is_valid and not poly_ftl.is_empty

    # Feature 1: 30m Buffer
    buf_feat = fc["features"][1]
    assert buf_feat["properties"]["layer_type"] == "STATUTORY_PROTECTION_BUFFER"
    assert buf_feat["properties"]["buffer_width_m"] == 30.0
    assert buf_feat["properties"]["legal_status"] == "POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION"
    poly_buf = shape(buf_feat["geometry"])
    assert poly_buf.is_valid and not poly_buf.is_empty

    # The 30m buffer polygon area must be strictly larger than the FTL polygon area
    assert poly_buf.area > poly_ftl.area

    # Verify BSA 2023 disclaimer
    assert "Bharatiya Sakshya Adhiniyam" in fc["metadata"]["legal_screening_disclaimer"]


def test_lake_ftl_buffer_invalid_id():
    """Verify 404 error is raised on unregistered lake ID."""
    with pytest.raises(Exception) as excinfo:
        get_lake_ftl_buffer("non_existent_pond_999")
    assert "404" in str(excinfo.value)


def test_decadal_change_detection_hussain_sagar():
    """
    Verify decadal change detection for Hussain Sagar between:
    - 2014 Landsat-8 OLI (30m GSD)
    - 2026 Copernicus Sentinel-2 MSI (10m GSD)
    """
    req = ChangeDetectionRequest(
        lake_id="hussain_sagar",
        t1_date="2014-03-15",
        t2_date="2026-11-14",
        t1_sensor="landsat-8-oli",
        t2_sensor="sentinel-2-msi"
    )
    res = run_change_detection(req)
    assert res["status"] == "success"
    assert res["lake_id"] == "hussain_sagar"

    # Verify sensor provenance - no false claims of 2014 Sentinel-2
    prov = res["bi_temporal_provenance"]
    assert "Landsat-8" in prov["t1_historical"]["mission"]
    assert "30.0 m/pixel" in prov["t1_historical"]["spatial_resolution_gsd"]
    assert "Sentinel-2" in prov["t2_surveillance"]["mission"]
    assert "10.0 m/pixel" in prov["t2_surveillance"]["spatial_resolution_gsd"]

    # Verify transitions
    tr = res["transitions"]
    assert tr["water_depletion_ha"] == 17.20
    assert tr["new_construction_ha"] == 32.40
    assert tr["vegetation_loss_ha"] == 9.80
    assert tr["net_built_expansion_pct"] == 2.78

    # Verify 7x7 transition matrix
    matrix_obj = res["decadal_transition_matrix_7x7"]
    assert len(matrix_obj["classes"]) == 7
    matrix = matrix_obj["matrix"]
    assert len(matrix) == 7
    for row in matrix:
        assert len(row) == 7

    # Verify BSA 2023 §63 compliance
    audit = res["statutory_buffer_audit"]
    assert audit["classification"] == "POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION"
    assert audit["potential_buffer_overlap_ha"] == 4.43
    assert audit["potential_buffer_overlap_acres"] == 10.95
    assert "Section 63" in audit["statutory_compliance"]

    # Verify cryptographic SHA-256 seal
    seal = res["evidentiary_seal"]
    assert len(seal["sha256_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in seal["sha256_hash"].lower())


def test_decadal_change_detection_durgam_cheruvu():
    """Verify Durgam Cheruvu decadal metrics are distinct from Hussain Sagar."""
    req = ChangeDetectionRequest(lake_id="durgam_cheruvu")
    res = run_change_detection(req)
    assert res["lake_id"] == "durgam_cheruvu"
    assert res["transitions"]["water_depletion_ha"] == 7.60
    assert res["transitions"]["new_construction_ha"] == 9.20
    assert res["statutory_buffer_audit"]["potential_buffer_overlap_acres"] == 7.71


def test_decadal_change_custom_bounds_fallback():
    """Verify custom bounding box request remains backwards-compatible."""
    req = ChangeDetectionRequest(
        bounds=BoundingBox(west=78.40, south=17.35, east=78.45, north=17.40),
        t1_date="2014-01-01",
        t2_date="2026-11-01"
    )
    res = run_change_detection(req)
    assert res["status"] == "success"
    assert "new_construction_ha" in res["transitions"]
    assert "decadal_transition_matrix_7x7" in res
    assert len(res["evidentiary_seal"]["sha256_hash"]) == 64
