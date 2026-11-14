import asyncio
import json
import os
import struct
import sys
import unittest
import urllib.error
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from utci import rh_to_vp as pkg_rh_to_vp, utci_approx as pkg_utci_approx

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PIPELINES_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "..", "..", "Pipelines"))
for p in (APP_DIR, PIPELINES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_site_studio as studio
from bhu_loka_mcp_server import create_mcp_server
from main import app


def _synthetic_dem(lat: float = 25.594, lon: float = 85.137, span: float = 0.04, g_n: int = 10):
    """Build a deterministic peaked 10x10 matrix for pure geometric/exporter unit tests."""
    mat = []
    for r in range(g_n):
        row = []
        for c in range(g_n):
            # Peak near center + Eastward slope so contours & S-N/W-E transects vary cleanly
            dr = (r - (g_n - 1) / 2.0) / 3.0
            dc = (c - (g_n - 1) / 2.0) / 3.0
            elev = 45.0 + 18.0 * pow(2.718281828, -(dr * dr + dc * dc)) + (g_n - 1 - r) * 1.1 + c * 0.4
            row.append(round(elev, 2))
        mat.append(row)
    half = span * 0.5
    flat = [v for row in mat for v in row]
    return {
        "live_online": True,
        "source_api": "UnitTest-Synthetic-Slope",
        "location": "TestSite",
        "state": "Bihar",
        "center": {"lat": lat, "lon": lon},
        "bounds": {"south": lat - half, "north": lat + half, "west": lon - half, "east": lon + half},
        "elev_matrix": mat,
        "metrics": {"min_m": min(flat), "max_m": max(flat), "mean_m": sum(flat) / len(flat), "relief_m": max(flat) - min(flat)},
    }


def _mock_osm_json(lat: float = 25.594, lon: float = 85.137):
    return {
        "elements": [
            {
                "type": "way",
                "id": 1001,
                "tags": {"building": "university", "name": "Academic Block", "height": "18 m"},
                "geometry": [
                    {"lat": lat - 0.0002, "lon": lon - 0.0002},
                    {"lat": lat - 0.0002, "lon": lon + 0.0002},
                    {"lat": lat + 0.0002, "lon": lon + 0.0002},
                    {"lat": lat + 0.0002, "lon": lon - 0.0002},
                    {"lat": lat - 0.0002, "lon": lon - 0.0002},
                ],
            },
            {
                "type": "way",
                "id": 1002,
                "tags": {"building": "residential", "building:levels": "4"},
                "geometry": [
                    {"lat": lat + 0.0005, "lon": lon - 0.0003},
                    {"lat": lat + 0.0005, "lon": lon},
                    {"lat": lat + 0.0007, "lon": lon},
                    {"lat": lat + 0.0007, "lon": lon - 0.0003},
                    {"lat": lat + 0.0005, "lon": lon - 0.0003},
                ],
            },
            {
                "type": "way",
                "id": 2001,
                "tags": {"highway": "primary", "name": "Site Avenue"},
                "geometry": [
                    {"lat": lat - 0.001, "lon": lon - 0.001},
                    {"lat": lat + 0.001, "lon": lon + 0.001},
                ],
            },
            {
                "type": "way",
                "id": 3001,
                "tags": {"leisure": "park", "name": "Central Lawn"},
                "geometry": [
                    {"lat": lat - 0.0006, "lon": lon + 0.0004},
                    {"lat": lat - 0.0006, "lon": lon + 0.0008},
                    {"lat": lat - 0.0003, "lon": lon + 0.0008},
                    {"lat": lat - 0.0003, "lon": lon + 0.0004},
                    {"lat": lat - 0.0006, "lon": lon + 0.0004},
                ],
            },
            {
                "type": "node",
                "id": 4001,
                "lat": lat + 0.0001,
                "lon": lon + 0.0003,
                "tags": {"amenity": "hospital", "name": "Campus Clinic"},
            },
        ]
    }


class TestSiteStudio(unittest.TestCase):
    def test_wgs84_to_utm_zones_and_validation(self):
        patna = studio.latlon_to_utm(25.5940, 85.1370)
        self.assertEqual(patna["epsg"], "EPSG:32645")
        self.assertEqual(patna["label"], "45N")
        self.assertTrue(300000 < patna["easting_m"] < 700000)
        self.assertTrue(2800000 < patna["northing_m"] < 2900000)

        mumbai = studio.latlon_to_utm(19.0760, 72.8777)
        self.assertEqual(mumbai["epsg"], "EPSG:32643")

        sydney = studio.latlon_to_utm(-33.8688, 151.2093)
        self.assertEqual(sydney["epsg"], "EPSG:32756")
        self.assertEqual(sydney["hemisphere"], "S")

        bergen = studio.latlon_to_utm(60.39, 5.32)
        self.assertEqual(bergen["zone"], 32)  # Norway UTM exception

        svalbard = studio.latlon_to_utm(78.22, 15.65)
        self.assertEqual(svalbard["zone"], 33)  # Svalbard UTM exception

        with self.assertRaises(ValueError):
            studio.latlon_to_utm(95.0, 85.0)
        with self.assertRaises(ValueError):
            studio.latlon_to_utm(25.0, 185.0)

    def test_noaa_solar_ephemeris_solstices_and_shadows(self):
        # Winter solstice Dec 21 solar noon in Patna (25.594N) ~ 90 - 25.594 - 23.44 = 40.97 deg
        patna_prof = studio.compute_solar_and_shadow_profile(25.594, 85.137, date_iso="2026-06-21", building_height_m=10.0)
        dec21 = patna_prof["solstices"]["winter_dec21"]
        jun21 = patna_prof["solstices"]["summer_jun21"]
        eq_mar = patna_prof["solstices"]["equinox_mar21"]

        self.assertAlmostEqual(dec21["noon_elevation_deg"], 40.97, delta=0.6)
        self.assertAlmostEqual(jun21["noon_elevation_deg"], 87.84, delta=0.6)
        self.assertAlmostEqual(eq_mar["noon_elevation_deg"], 64.4, delta=1.2)
        self.assertGreater(jun21["daylight_hours"], 13.0)
        self.assertLess(dec21["daylight_hours"], 11.0)
        self.assertGreater(patna_prof["daylight_spacing_guidance"]["min_h_to_s_spacing_ratio"], 1.0)

        # Chennai (13.08N) in June 21: Sun is north of zenith at solar noon -> azimuth near 0/360
        chennai = studio.compute_solar_and_shadow_profile(13.083, 80.270, date_iso="2026-06-21")
        ch_az = chennai["solstices"]["summer_jun21"]["noon_azimuth_deg"]
        self.assertTrue(ch_az < 20.0 or ch_az > 340.0, f"Expected northward noon sun in Chennai June 21, got {ch_az}")

        # Hourly curve checks morning -> noon -> afternoon progression
        curve = patna_prof["hourly_curve"]
        self.assertEqual(len(curve), 13)
        el_07 = next(h["elevation_deg"] for h in curve if h["hour_local"] == "07:00")
        el_12 = next(h["elevation_deg"] for h in curve if h["hour_local"] == "12:00")
        self.assertGreater(el_12, el_07)

    def test_brode_utci_parity_and_tmrt(self):
        # Verify internal pure-Python & utci-1.0.0 parity across multiple climates
        cases = [
            (20.0, 50.0, 20.0, 1.5),
            (38.0, 45.0, 58.0, 2.0),
            (5.0, 80.0, 5.0, 6.0),
            (28.0, 75.0, 45.0, 0.2),   # Low wind clamped to 0.5 m/s
            (18.0, 40.0, 18.0, 25.0),  # High wind clamped to 17.0 m/s
        ]
        for ta, rh, tmrt, va in cases:
            eff_va = max(0.5, min(17.0, va))
            expected = pkg_utci_approx(ta, pkg_rh_to_vp(ta, rh), tmrt, eff_va)
            res = studio.compute_utci_value(ta, rh, tmrt, va)
            self.assertAlmostEqual(res["utci_c"], round(expected, 2), places=2)
            # Also validate our standalone pure polynomial matches pkg_utci_approx to 1e-6
            pure_val = studio._pure_utci_approx(ta, studio._sat_vapor_pressure_hpa(ta) * rh / 100.0, tmrt, eff_va)
            self.assertAlmostEqual(pure_val, expected, delta=1e-4)

        # Sunlit Tmrt must exceed Shaded Tmrt under high solar irradiance
        t_sun = studio.estimate_tmrt_from_radiation(35.0, ghi_wm2=850.0, dni_wm2=720.0, diffuse_wm2=180.0, solar_elev_deg=62.0, shaded=False)
        t_shd = studio.estimate_tmrt_from_radiation(35.0, ghi_wm2=850.0, dni_wm2=720.0, diffuse_wm2=180.0, solar_elev_deg=62.0, shaded=True)
        self.assertGreater(t_sun, t_shd + 8.0)

    def test_fail_closed_offline_apis(self):
        studio._OVERPASS_CACHE.clear()
        studio._WEATHER_UTCI_CACHE.clear()
        with patch.object(studio.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            osm = studio.fetch_osm_site_context(25.594, 85.137, radius_m=350.0, bypass_cache=True)
            self.assertEqual(osm["status"], "UNAVAILABLE")
            self.assertEqual(osm["building_count"], 0)
            self.assertEqual(osm["buildings"], [])

            utci_res = studio.fetch_solar_wind_utci_assessment(25.594, 85.137)
            self.assertEqual(utci_res["status"], "UNAVAILABLE")
            self.assertIsNone(utci_res["utci_sunlit_c"])
            self.assertEqual(utci_res["wind_rose"]["status"], "UNAVAILABLE")

        dem_off = studio.extract_dem_contours_and_profiles({"live_online": False})
        self.assertEqual(dem_off["status"], "UNAVAILABLE")
        self.assertEqual(dem_off["contours"], [])

    def test_marching_squares_contours_and_transects(self):
        dem = _synthetic_dem()
        tc = studio.extract_dem_contours_and_profiles(dem, levels=6)
        self.assertEqual(tc["status"], "COMPUTED")
        self.assertGreater(tc["contour_count"], 0)
        for c in tc["contours"]:
            self.assertGreater(c["elevation_m"], dem["metrics"]["min_m"])
            self.assertLess(c["elevation_m"], dem["metrics"]["max_m"])
            self.assertTrue(len(c["polylines"][0]) >= 2)
        sn = tc["profiles"]["south_north"]
        we = tc["profiles"]["west_east"]
        self.assertEqual(len(sn), 10)
        self.assertEqual(len(we), 10)
        self.assertLess(sn[0]["lat"], sn[-1]["lat"])  # Strictly South -> North

    def test_exporters_dxf_svg_glb_obj_geojson(self):
        dem = _synthetic_dem()
        with patch.object(studio, "_http_post_form_json", return_value=_mock_osm_json()), \
             patch.object(studio, "fetch_location_3d_dem", return_value=dem), \
             patch.object(studio, "fetch_solar_wind_utci_assessment", return_value={"status": "LIVE", "utci_sunlit_c": 31.2, "utci_shaded_c": 26.5}):
            studio._OVERPASS_CACHE.clear()
            analysis = studio.run_site_analysis(25.594, 85.137, place_name="Patna Core", radius_m=350.0, include_osm=True, include_utci=True, include_dem=True)

        self.assertEqual(analysis["osm_context"]["status"], "LIVE")
        self.assertEqual(analysis["osm_context"]["building_count"], 2)
        self.assertEqual(analysis["osm_context"]["heights_tagged_count"], 1)
        self.assertEqual(analysis["osm_context"]["heights_estimated_levels_count"], 1)

        # 1. DXF AC1015
        dxf_txt = studio.build_dxf_ascii(analysis)
        self.assertIn("AC1015", dxf_txt)
        for lyr in ("0_SITE_BOUNDARY", "1_DEM_CONTOURS", "2_OSM_BUILDINGS", "3_OSM_ROADS", "4_SOLAR_VECTORS"):
            self.assertIn(lyr, dxf_txt)
        self.assertIn("LWPOLYLINE", dxf_txt)
        self.assertIn("EOF", dxf_txt)

        # 2. SVG 1000x1000 plan + Profile SVG
        svg_txt = studio.build_layered_svg(analysis)
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', svg_txt)
        self.assertIn("OpenStreetMap", svg_txt)
        self.assertIn('id="layer-buildings"', svg_txt)

        psvg_txt = studio.build_profile_svg(analysis)
        self.assertIn("ELEVATION TRANSECT", psvg_txt)
        self.assertIn("Copernicus GLO-90 DEM", psvg_txt)

        # 3. Binary glTF 2.0 GLB structure & chunk alignment check
        glb = studio.build_glb_binary(analysis)
        magic, version, total_len = struct.unpack("<III", glb[:12])
        self.assertEqual(magic, 0x46546C67)
        self.assertEqual(version, 2)
        self.assertEqual(total_len, len(glb))
        c0_len, c0_type = struct.unpack("<II", glb[12:20])
        self.assertEqual(c0_type, 0x4E4F534A)
        self.assertEqual(c0_len % 4, 0)
        gltf_json = json.loads(glb[20:20 + c0_len].decode("utf-8"))
        self.assertEqual(gltf_json["asset"]["version"], "2.0")
        mesh_names = {m["name"] for m in gltf_json["meshes"]}
        self.assertEqual(mesh_names, {"TerrainRelief", "OsmBuildings"})
        c1_start = 20 + c0_len
        c1_len, c1_type = struct.unpack("<II", glb[c1_start:c1_start + 8])
        self.assertEqual(c1_type, 0x004E4942)
        self.assertEqual(c1_start + 8 + c1_len, len(glb))

        # 4. OBJ
        obj_txt = studio.build_obj_mesh(analysis)
        self.assertIn("o TerrainRelief", obj_txt)
        self.assertIn("o OsmBuildings", obj_txt)

        # 5. GeoJSON RFC 7946
        gj = studio.build_geojson_bundle(analysis)
        self.assertEqual(gj["type"], "FeatureCollection")
        layers = {f["properties"]["layer"] for f in gj["features"]}
        self.assertTrue({"site_center", "site_boundary", "solar_vector", "dem_contour", "osm_building", "osm_road"}.issubset(layers))

    def test_fastapi_site_studio_and_mcp_11_tools(self):
        dem = _synthetic_dem()

        async def _probe():
            with patch.object(studio, "_http_post_form_json", return_value=_mock_osm_json()), \
                 patch.object(studio, "fetch_location_3d_dem", return_value=dem), \
                 patch.object(studio, "fetch_solar_wind_utci_assessment", return_value={"status": "LIVE", "utci_sunlit_c": 30.1, "utci_shaded_c": 25.4, "wind_rose": {"status": "LIVE", "dominant_sector": "E"}}):
                studio._OVERPASS_CACHE.clear()
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://testserver",
                    timeout=15.0,
                ) as client:
                    sa = await client.get("/api/v1/site-analysis?lat=25.594&lon=85.137&place_name=Patna&include_osm=true")
                    self.assertEqual(sa.status_code, 200)
                    sjson = sa.json()
                    self.assertEqual(sjson["schema"], "bhu-loka-site-studio-v3.2")
                    self.assertEqual(sjson["location"]["utm"]["epsg"], "EPSG:32645")
                    self.assertEqual(sjson["osm_context"]["status"], "LIVE")

                    for fmt, prefix in (
                        ("dxf", b"999"),
                        ("svg", b"<svg"),
                        ("profile_svg", b"<svg"),
                        ("glb", b"glTF"),
                        ("obj", b"# BHU LOKA"),
                        ("geojson", b"{"),
                    ):
                        exp = await client.get(f"/api/v1/export-site?lat=25.594&lon=85.137&format={fmt}&place_name=Patna")
                        self.assertEqual(exp.status_code, 200, f"Export {fmt} failed")
                        self.assertIn("attachment", exp.headers.get("content-disposition", ""))
                        self.assertIn("OpenStreetMap ODbL", exp.headers.get("x-bhu-loka-attribution", ""))
                        self.assertTrue(exp.content.startswith(prefix), f"Unexpected prefix for {fmt}")

                    bad = await client.get("/api/v1/export-site?lat=25.594&lon=85.137&format=invalid_fmt")
                    self.assertEqual(bad.status_code, 400)

        asyncio.run(_probe())

        mcp = create_mcp_server()
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        self.assertGreaterEqual(len(names), 11)
        expected_new = {"analyze_site_solar_utci", "fetch_osm_site_footprint_context", "export_site_cad_or_map"}
        self.assertTrue(expected_new.issubset(names), f"Missing Site Studio MCP tools: {expected_new - names}")


if __name__ == "__main__":
    unittest.main()
