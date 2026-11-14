"""
Unit and Integration Tests for BHU LOKA Human Intelligence Engine (bhu_loka_worker_health.py)

Validates:
1. ISO 7243 WBGT calculation & Stull (2011) empirical natural wet-bulb approximation
2. Work-rest cycle tiers (SAFE, CAUTION, WARNING, DANGER, EXTREME)
3. CPCB 2014 NAQI PM2.5 tier classification
4. Combined exposure risk scoring & fail-closed behavior
5. Zero-fabrication fail-closed responses when external APIs are unavailable
6. FastAPI worker router endpoints (/api/v1/worker/*)

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = APP_DIR.parent.parent.parent
PIPELINES_DIR = ROOT_DIR / "Pipelines"

for p in (str(APP_DIR), str(PIPELINES_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_worker_health as wh
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestWorkerHealthEngine(unittest.TestCase):
    def setUp(self):
        wh.clear_worker_health_caches()

    def test_stull_natural_wetbulb_physical_consistency(self):
        # At 100% RH, wet-bulb temperature should approximately equal dry-bulb temperature
        tw_100 = wh._natural_wet_bulb(30.0, 99.0)
        self.assertAlmostEqual(tw_100, 30.0, delta=1.5)

        # At lower RH, wet bulb must be strictly less than dry bulb
        tw_50 = wh._natural_wet_bulb(35.0, 50.0)
        self.assertLess(tw_50, 35.0)

        # At dry desert conditions, wet bulb is substantially lower
        tw_15 = wh._natural_wet_bulb(45.0, 15.0)
        self.assertLess(tw_15, 30.0)

    def test_wbgt_calculation_tiers(self):
        # Mild / cool day -> SAFE
        res_safe = wh.compute_wbgt(t_dry_c=20.0, rh_pct=40.0, wind_speed_ms=3.0, solar_rad_wm2=200.0)
        self.assertEqual(res_safe["tier"], "SAFE")
        self.assertIn("No work restrictions", res_safe["work_rest_advice"])
        self.assertLess(res_safe["wbgt_celsius"], 25.0)

        # Warm moderate day -> CAUTION (25 - 28 C)
        res_caution = wh.compute_wbgt(t_dry_c=31.0, rh_pct=60.0, wind_speed_ms=1.5, solar_rad_wm2=500.0)
        self.assertIn(res_caution["tier"], ("CAUTION", "WARNING"))

        # Extreme heatwave (e.g. 44 C, 70% RH, still air) -> EXTREME (>= 33 C WBGT)
        res_extreme = wh.compute_wbgt(t_dry_c=44.0, rh_pct=70.0, wind_speed_ms=0.5, solar_rad_wm2=800.0)
        self.assertEqual(res_extreme["tier"], "EXTREME")
        self.assertIn("Work cessation", res_extreme["work_rest_advice"])
        self.assertGreaterEqual(res_extreme["wbgt_celsius"], 33.0)

    def test_naqi_pm25_classification(self):
        self.assertEqual(wh._classify_naqi_pm25(15.0)[0], "GOOD")
        self.assertEqual(wh._classify_naqi_pm25(45.0)[0], "SATISFACTORY")
        self.assertEqual(wh._classify_naqi_pm25(75.0)[0], "MODERATE")
        self.assertEqual(wh._classify_naqi_pm25(110.0)[0], "POOR")
        self.assertEqual(wh._classify_naqi_pm25(200.0)[0], "VERY_POOR")
        self.assertEqual(wh._classify_naqi_pm25(350.0)[0], "SEVERE")

    def test_exposure_risk_composite(self):
        # Both available: SAFE + GOOD -> LOW
        res_low = wh.compute_exposure_risk({"tier": "SAFE"}, {"naqi_category": "GOOD"})
        self.assertEqual(res_low["risk_level"], "LOW")
        self.assertEqual(res_low["composite_score"], 0)

        # Extreme heat + severe smog -> EXTREME
        res_ext = wh.compute_exposure_risk({"tier": "EXTREME"}, {"naqi_category": "SEVERE"})
        self.assertEqual(res_ext["risk_level"], "EXTREME")
        self.assertEqual(res_ext["composite_score"], 100)

        # Partial availability: heat available, air quality unavailable
        res_part = wh.compute_exposure_risk({"tier": "DANGER"}, {"naqi_category": "UNAVAILABLE"})
        self.assertEqual(res_part["status"], "COMPUTED")
        self.assertEqual(res_part["primary_hazard"], "HEAT")
        self.assertIn("Air quality data unavailable", res_part["computation_note"])

        # Both unavailable -> fail-closed UNAVAILABLE
        res_unavail = wh.compute_exposure_risk({"tier": "UNAVAILABLE"}, {"naqi_category": "UNAVAILABLE"})
        self.assertEqual(res_unavail["status"], "UNAVAILABLE")
        self.assertIsNone(res_unavail["composite_score"])
        self.assertIn("Network offline", res_unavail["recommendation"])

    def test_zero_fabrication_on_network_failure(self):
        wh.clear_worker_health_caches()
        # Mock urllib to simulate offline environment
        with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
            wbgt_res = wh.fetch_wbgt_for_location(25.5941, 85.1376)
            self.assertEqual(wbgt_res["status"], "UNAVAILABLE")
            self.assertIn("unreachable", wbgt_res["reason"].lower())
            self.assertIsNone(wbgt_res["wbgt_celsius"])

            aqi_res = wh.fetch_aqi_for_location(25.5941, 85.1376)
            self.assertEqual(aqi_res["status"], "UNAVAILABLE")
            self.assertIsNone(aqi_res["pm25_ugm3"])

            shelters_res = wh.fetch_cooling_shelters(25.5941, 85.1376)
            self.assertEqual(shelters_res["status"], "UNAVAILABLE")
            self.assertEqual(shelters_res["shelters"], [])

    def test_fastapi_worker_endpoints_mocked(self):
        # Test endpoints with deterministic mocked data
        mock_wbgt = {
            "status": "OBSERVED",
            "source": "Open-Meteo",
            "wbgt_celsius": 24.2,
            "tier": "SAFE",
            "work_rest_advice": "No work restrictions.",
        }
        mock_aqi = {
            "status": "OBSERVED",
            "source": "OpenAQ",
            "pm25_ugm3": 45.0,
            "naqi_category": "SATISFACTORY",
        }
        mock_shelters = {
            "status": "OBSERVED",
            "source": "OSM",
            "count": 1,
            "shelters": [{"name": "Community Health Centre", "distance_m": 450}],
        }

        with patch("bhu_loka_worker_health.fetch_wbgt_for_location", return_value=mock_wbgt), \
             patch("bhu_loka_worker_health.fetch_aqi_for_location", return_value=mock_aqi), \
             patch("bhu_loka_worker_health.fetch_cooling_shelters", return_value=mock_shelters):

            resp = client.get("/api/v1/worker/health?lat=25.5941&lon=85.1376")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["wbgt"]["status"], "OBSERVED")
            self.assertEqual(data["aqi"]["naqi_category"], "SATISFACTORY")
            self.assertEqual(data["exposure_risk"]["risk_level"], "LOW")
            self.assertEqual(len(data["cooling_shelters"]["shelters"]), 1)

            resp_wbgt = client.get("/api/v1/worker/wbgt?lat=25.5941&lon=85.1376")
            self.assertEqual(resp_wbgt.status_code, 200)
            self.assertEqual(resp_wbgt.json()["tier"], "SAFE")

            resp_aqi = client.get("/api/v1/worker/aqi?lat=25.5941&lon=85.1376")
            self.assertEqual(resp_aqi.status_code, 200)
            self.assertEqual(resp_aqi.json()["pm25_ugm3"], 45.0)

            resp_shelters = client.get("/api/v1/worker/shelters?lat=25.5941&lon=85.1376")
            self.assertEqual(resp_shelters.status_code, 200)
            self.assertEqual(resp_shelters.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
