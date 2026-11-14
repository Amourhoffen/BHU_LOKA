import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "..", ".."))
PIPELINES_DIR = os.path.abspath(os.path.join(ROOT_DIR, "Pipelines"))
for p in (APP_DIR, PIPELINES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_live_api as live_api
import bhu_loka_location_engine as loc_engine
import main


def _asgi_request(method: str, url: str, headers: dict = None, json_body: dict = None) -> httpx.Response:
    async def _call():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, headers=headers, json=json_body)

    return asyncio.run(_call())


class TestPhase1EarthIntelligence(unittest.TestCase):
    def test_security_headers_and_audit_endpoint(self):
        resp = _asgi_request("GET", "/api/v1/system/security-audit")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(resp.headers.get("x-frame-options"), "SAMEORIGIN")
        self.assertEqual(resp.headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        body = resp.json()
        self.assertEqual(body["status"], "ACTIVE")
        self.assertIn("viewer", body["rbac_roles"])
        self.assertIn("analyst", body["rbac_roles"])

    def test_viewer_role_blocked_on_mutating_refresh(self):
        resp = _asgi_request(
            "POST",
            "/api/v1/india/news/refresh",
            headers={"X-Bhu-Role": "viewer"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("viewer", resp.json()["detail"].lower())

    def test_sources_provenance_separates_eo_ephemeris_and_cloud(self):
        resp = _asgi_request("GET", "/api/v1/sources/provenance")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("aws", payload["cloud_infrastructure_exclusion"].lower())
        domains = {c["domain"]: c["sources"] for c in payload["categories"]}
        self.assertIn("Earth Observation & Satellite Imagery", domains)
        self.assertIn("Orbital Tracking (Ephemeris Only)", domains)
        eo_names = " ".join(s["name"] for s in domains["Earth Observation & Satellite Imagery"])
        self.assertIn("NASA EOSDIS GIBS", eo_names)
        orb_limits = " ".join(s["limitation"] for s in domains["Orbital Tracking (Ephemeris Only)"])
        self.assertIn("not live onboard spacecraft", orb_limits.lower())

    def test_satellite_propagate_record_marks_ephemeris_only(self):
        now = datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc)
        rec = {
            "NORAD_CAT_ID": 25544,
            "OBJECT_NAME": "ISS (ZARYA)",
            "EPOCH": "2026-11-12T10:00:00Z",
            "MEAN_MOTION": 15.5,
            "ECCENTRICITY": 0.0005,
            "INCLINATION": 51.64,
            "RA_OF_ASC_NODE": 120.0,
            "ARG_OF_PERICENTER": 45.0,
            "MEAN_ANOMALY": 10.0,
        }
        prop = live_api._propagate_gp_record(rec, now)
        self.assertIsNotNone(prop)
        self.assertEqual(prop["tracking_type"], "ORBITAL_EPHEMERIS_ONLY")
        self.assertEqual(prop["epoch_utc"], "2026-11-12T10:00:00+00:00")

    def test_location_engine_satellite_and_rainfall_modules_include_provenance(self):
        sat_mod = loc_engine._build_satellite_imagery_module(25.6, 85.1)
        self.assertEqual(sat_mod["status"], "LIVE_TILES")
        self.assertTrue(sat_mod.get("updated_at_utc"))
        layer_ids = [item["id"] for item in sat_mod["eosdis_gibs_layers"]]
        self.assertIn("MODIS_Terra_NDVI_8Day", layer_ids)
        self.assertIn("MODIS_Terra_Land_Surface_Temp_Day", layer_ids)
        self.assertIn("limitations", sat_mod)

        with patch.object(loc_engine, "_http_get_json", return_value=None):
            wx, rn, soil = loc_engine._build_weather_and_climate_soil(25.6, 85.1, "Bihar")
            self.assertEqual(wx["status"], "UNAVAILABLE")
            self.assertEqual(rn["status"], "UNAVAILABLE")
            self.assertEqual(rn["dry_spell_flag"], "UNAVAILABLE")
            self.assertEqual(soil["status"], "STATUTORY_ONLY")

    def test_dashboard_html_contains_phase1_workstation_elements(self):
        html_path = Path(ROOT_DIR) / "bhu_loka_cyber_dashboard.html"
        txt = html_path.read_text(encoding="utf-8")
        for marker in (
            'id="btn-solar"',
            "ensureSolarSystemScene",
            "orbitalPathsGroup",
            "toggleOrbitalPaths",
            "toggleAtmosphereLimb",
            "ORBITAL EPHEMERIS ONLY",
            "bhu-agent-trace",
            "Agent Activity &amp; Technical Details",
        ):
            self.assertIn(marker, txt)


if __name__ == "__main__":
    unittest.main()

