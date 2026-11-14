"""
Unit Tests for BHU LOKA Module 04: Business & Urban Intelligence Engine
=======================================================================
Verifies:
1. Copernicus 30m GLO-30 DEM elevation zoning, micro-relief and slope calculations.
2. Copernicus Sentinel-1 SAR empirical flood benchmark & GloFAS river discharge coupling.
3. OSM Overpass CCTV surveillance nodes and emergency facilities parsing.
4. Strict fail-closed policy (zero synthetic data on network failure).
5. FastAPI router endpoints under /api/v1/urban/*.

Author: Prince Kumar (IIT Patna, PA2511CDH37)
Supervisor: Pallav Rustogi
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

APP_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = APP_DIR.parent.parent.parent
PIPELINES_DIR = ROOT_DIR / "Pipelines"
for p in (str(APP_DIR), str(PIPELINES_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_urban_business as urban


def _create_mock_response(data: dict):
    m = MagicMock()
    m.read.return_value = json.dumps(data).encode("utf-8")
    m.__enter__.return_value = m
    return m


class TestUrbanBusinessIntelligence(unittest.TestCase):
    def setUp(self):
        urban.clear_urban_business_caches()

    def tearDown(self):
        urban.clear_urban_business_caches()

    def test_dem_elevation_zoning_patna_raster(self):
        """Test empirical 30m GLO-30 DEM micro-relief extraction within Patna PMC bounds."""
        res = urban.compute_dem_elevation_zoning(lat=25.594, lon=85.137)
        self.assertEqual(res["status"], "ONLINE")
        self.assertIn("elevation_m", res)
        self.assertIn("slope_deg", res)
        self.assertIn(res["zoning_tier"], ["DEPRESSION_SINK", "TRANSITIONAL_PLAIN", "NATURAL_LEVEE_HIGHLAND"])
        self.assertIn(res["commercial_resilience_rating"], ["VULNERABLE", "MODERATE", "HIGH"])
        self.assertGreaterEqual(res["elevation_m"], 35.0)
        self.assertLessEqual(res["elevation_m"], 80.0)
        self.assertGreaterEqual(res["slope_deg"], 0.0)
        self.assertIn("provenance", res)
        self.assertEqual(res["provenance"]["nominal_resolution_m"], 30.0)

    def test_dem_elevation_zoning_fail_closed_on_network_error(self):
        """Outside Patna raster bounds, network error must return UNAVAILABLE without synthetic fabrication."""
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            res = urban.compute_dem_elevation_zoning(lat=12.9716, lon=77.5946)
            self.assertEqual(res["status"], "UNAVAILABLE")
            self.assertIn("error", res)

    def test_sar_flood_inundation_coupling_benchmark(self):
        """Verify empirical Sentinel-1 SAR flood benchmark (2019 Patna deluge)."""
        mock_flood_data = {"daily": {"river_discharge": [21500.0]}}
        with patch("urllib.request.urlopen", return_value=_create_mock_response(mock_flood_data)):
            res = urban.get_sar_flood_inundation_coupling(lat=25.594, lon=85.137)
            self.assertEqual(res["status"], "ONLINE")
            sar = res["empirical_sar_benchmark"]
            self.assertIn("event", sar)
            self.assertEqual(sar["polarization"], "VV")
            self.assertAlmostEqual(sar["otsu_threshold_dB"], -3.7978, delta=0.01)
            self.assertGreater(sar["empirical_flooded_area_km2"], 20.0)
            self.assertEqual(res["hydrological_coupling"]["status"], "ONLINE")
            self.assertEqual(res["hydrological_coupling"]["river_discharge_m3_s"], 21500.0)
            self.assertIn("compounding_flood_vulnerability", res)

    def test_sar_flood_coupling_fail_closed_discharge(self):
        """River discharge telemetry failure must report UNAVAILABLE for discharge while keeping SAR benchmark intact."""
        with patch("urllib.request.urlopen", side_effect=Exception("Gateway Timeout")):
            res = urban.get_sar_flood_inundation_coupling(lat=25.594, lon=85.137)
            self.assertEqual(res["status"], "ONLINE")
            hydro = res["hydrological_coupling"]
            self.assertEqual(hydro["status"], "UNAVAILABLE")
            self.assertIsNone(hydro["river_discharge_m3_s"])
            self.assertAlmostEqual(res["empirical_sar_benchmark"]["otsu_threshold_dB"], -3.7978, delta=0.01)

    def test_urban_infrastructure_overpass_success(self):
        """Verify parsing of OSM Overpass CCTV surveillance nodes and emergency facilities."""
        mock_overpass_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 1001,
                    "lat": 25.595,
                    "lon": 85.138,
                    "tags": {
                        "man_made": "surveillance",
                        "surveillance": "outdoor",
                        "camera:type": "dome",
                        "camera:mount": "pole",
                        "operator": "Patna Smart City Ltd"
                    }
                },
                {
                    "type": "node",
                    "id": 1002,
                    "lat": 25.596,
                    "lon": 85.139,
                    "tags": {
                        "amenity": "hospital",
                        "name": "Patna Medical College Hospital (PMCH)",
                        "emergency": "yes"
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen", return_value=_create_mock_response(mock_overpass_response)):
            res = urban.get_urban_infrastructure_nodes(lat=25.594, lon=85.137, radius_m=1000)
            self.assertEqual(res["status"], "ONLINE")
            self.assertEqual(len(res["cctv_nodes"]), 1)
            self.assertEqual(len(res["emergency_facilities"]), 1)
            self.assertEqual(res["cctv_nodes"][0]["osm_id"], 1001)
            self.assertEqual(res["emergency_facilities"][0]["name"], "Patna Medical College Hospital (PMCH)")
            self.assertEqual(res["total_nodes"], 2)

    def test_urban_infrastructure_fail_closed_offline(self):
        """When Overpass is down, return UNAVAILABLE with zero synthetic nodes."""
        with patch("urllib.request.urlopen", side_effect=Exception("504 Gateway Timeout")):
            res = urban.get_urban_infrastructure_nodes(lat=25.594, lon=85.137, radius_m=1000)
            self.assertEqual(res["status"], "UNAVAILABLE")
            self.assertEqual(len(res["cctv_nodes"]), 0)
            self.assertEqual(len(res["emergency_facilities"]), 0)
            self.assertEqual(res["total_nodes"], 0)

    def test_urban_business_summary_composition(self):
        """Verify get_urban_business_summary produces composite commercial suitability score."""
        mock_dem = {
            "status": "ONLINE",
            "elevation_m": 52.3,
            "slope_deg": 1.1,
            "risk_score": 0.15,
            "zoning_tier": "NATURAL_LEVEE_HIGHLAND",
            "commercial_resilience_rating": "HIGH"
        }
        mock_flood = {
            "status": "ONLINE",
            "compounding_flood_vulnerability": {"score": 0.25}
        }
        mock_infra = {
            "status": "ONLINE",
            "emergency_facilities": [{"osm_id": 2002, "name": "Patna Hospital"}],
            "total_nodes": 1
        }
        with patch.object(urban, "compute_dem_elevation_zoning", return_value=mock_dem), \
             patch.object(urban, "get_sar_flood_inundation_coupling", return_value=mock_flood), \
             patch.object(urban, "get_urban_infrastructure_nodes", return_value=mock_infra):

            summary = urban.get_urban_business_summary(lat=25.594, lon=85.137)
            self.assertEqual(summary["status"], "ONLINE")
            self.assertIn("commercial_suitability_score", summary)
            self.assertGreaterEqual(summary["commercial_suitability_score"], 50.0)
            self.assertEqual(summary["dem_zoning"]["zoning_tier"], "NATURAL_LEVEE_HIGHLAND")


if __name__ == "__main__":
    unittest.main()
