import asyncio
import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import patch

import httpx

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PIPELINES_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "..", "..", "Pipelines"))
for p in (APP_DIR, PIPELINES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from rag.pipeline import RAGPipeline
from main import app
from bhu_loka_mcp_server import create_mcp_server


class TestEnterpriseRAG(unittest.TestCase):
    pipeline: RAGPipeline

    @classmethod
    def setUpClass(cls):
        # Test full 384-d Transformer + BM25 + Stage-2 Cross Re-Ranker pipeline
        cls.pipeline = RAGPipeline(preload_transformer=True)

    def test_pipeline_initialization_and_transformer_backend(self):
        self.assertGreaterEqual(len(self.pipeline.documents), 20)
        self.assertIsNotNone(self.pipeline.retriever)
        self.assertTrue(self.pipeline.embedder.transformer_ready)
        self.assertIn("all-MiniLM-L6-v2", self.pipeline.embedder.active_backend_label())
        self.assertIsNotNone(self.pipeline.vector_db.transformer_index)

    def test_sister_safety_query(self):
        res = self.pipeline.run("Meri behen ke liye Patna me safe jagah batao")
        self.assertEqual(res["language"], "hinglish")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("Danapur", top_source)
        self.assertGreater(res["retrieved_sources"][0]["rrf_score"], 0.01)

    def test_farming_query(self):
        res = self.pipeline.run("Is Patna good for farming and agriculture?")
        self.assertEqual(res["language"], "en")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("Agricultural", top_source)

    def test_heatwave_query(self):
        res = self.pipeline.run("What was the peak temperature recorded by NASA MODIS in Patna?")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("MODIS", top_source)

    def test_tricky_app_kya_krte_hain(self):
        res = self.pipeline.run("App kya krte hain aur aapke features kya hain")
        titles = [s["title"] for s in res["retrieved_sources"]]
        self.assertTrue(any("Capabilities" in t or "Provenance" in t for t in titles))

    def test_tricky_bihta_query(self):
        res = self.pipeline.run("Bihta kaha kesha hain aur IIT Patna kaisa hai")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("Bihta", top_source)

    def test_tricky_ocean_teleconnection_query(self):
        res = self.pipeline.run("Asia Pacific ocean aur ENSO IOD se flood me kya hota hai")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("Teleconnections", top_source)

    def test_tricky_leadership_query(self):
        res = self.pipeline.run("Modi koun hain aur geospatial policy se kya sambandh hai")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertIn("Leadership", top_source)

    def test_tricky_prithvi_identity_clarification(self):
        res = self.pipeline.run("Is this system PRITHVI or what is its real name?")
        top_source = res["retrieved_sources"][0]["title"]
        self.assertTrue("PRITHVI" in top_source or "Identity" in top_source)

    def test_creator_multilingual_hindi_and_hinglish(self):
        res_hi = self.pipeline.run("आपको किसने बनाया है?")
        self.assertEqual(res_hi["language"], "hi")
        self.assertIn("प्रिंस कुमार", res_hi["answer"])
        self.assertIn("पल्लव रुस्तोगी", res_hi["answer"])

        res_hg = self.pipeline.run("Apko kisne bnaya aur aap kaun ho?")
        self.assertEqual(res_hg["language"], "hinglish")
        self.assertIn("Prince Kumar", res_hg["answer"])

    def test_map_color_legend_and_agent2_spotlight(self):
        res = self.pipeline.run("ye red color aur blue line q hain map par?")
        self.assertEqual(res["language"], "hinglish")
        self.assertIn("Legend", res["retrieved_sources"][0]["title"])
        self.assertEqual(res["agent2_map_actions"]["callout_color_key"], "red")

    def test_ramayana_circuit_and_agent2_hologram(self):
        res = self.pipeline.run("ramayan kaha huaa tha?")
        self.assertIn("Ramayana", res["retrieved_sources"][0]["title"])
        self.assertEqual(res["agent2_map_actions"]["view_mode"], "auto_hologram")
        self.assertEqual(res["agent2_map_actions"]["auto_hologram_target"]["name"].split()[0], "Ayodhya")

    def test_harappan_ivc_and_agent2_hologram(self):
        res = self.pipeline.run("haddapa sbhyata kahata tha?")
        self.assertIn("Harappan", res["retrieved_sources"][0]["title"])
        self.assertEqual(res["agent2_map_actions"]["view_mode"], "auto_hologram")
        self.assertIn("Rakhigarhi", res["agent2_map_actions"]["auto_hologram_target"]["name"])

    def test_india_best_land_and_bihar_38_districts(self):
        land_res = self.pipeline.run("India me accha land kaha hai ghar kharidne ke liye?")
        self.assertIn("Land Suitability", land_res["retrieved_sources"][0]["title"])

        br_res = self.pipeline.run("Bihar ke sabhi 38 districts aur 29 state dikhao")
        self.assertIn("38 Districts", br_res["retrieved_sources"][0]["title"])
        self.assertEqual(br_res["agent2_map_actions"]["view_mode"], "bihar")

    def test_live_satellites_doc_and_source_honesty(self):
        sat_res = self.pipeline.run("World view me real time kitne starlink satellite chal rahe hain?")
        self.assertIn("Satellites", sat_res["retrieved_sources"][0]["title"])
        self.assertEqual(sat_res["agent2_map_actions"]["view_mode"], "world")

        honest_res = self.pipeline.run("Abhi ka live data kaha se de rha hai fake nahi?")
        self.assertIn("Source", honest_res["retrieved_sources"][0]["title"])

    def test_typo_geen_and_explicit_english_responses(self):
        res_geen = self.pipeline.run("geen")
        self.assertEqual(res_geen["language"], "en")
        self.assertGreater(len(res_geen["retrieved_sources"]), 0)
        self.assertIn("Legend", res_geen["retrieved_sources"][0]["title"])
        self.assertEqual(res_geen["agent2_map_actions"]["callout_color_key"], "green")
        self.assertIn("GREEN (#10b981)", res_geen["answer"])

        res_explicit_en = self.pipeline.run("ye red color q hain in english")
        self.assertEqual(res_explicit_en["language"], "en")
        self.assertIn("RED / ROSE", res_explicit_en["answer"])

        res_override = self.pipeline.run("ramayan kaha huaa tha?", language_override="en")
        self.assertEqual(res_override["language"], "en")
        self.assertIn("Ayodhya", res_override["answer"])

    def test_uncalibrated_gibberish_returns_zero_sources(self):
        res = self.pipeline.run("zzxyyqwv randomnoise")
        self.assertEqual(len(res["retrieved_sources"]), 0)
        self.assertIn("No verified geospatial records match", res["answer"])

    def test_fastapi_endpoints_full_suite(self):
        async def _probe():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                timeout=15.0,
            ) as client:
                h = await client.get("/health")
                self.assertEqual(h.status_code, 200)
                self.assertEqual(h.json()["status"], "HEALTHY")

                w = await client.get("/api/v1/wards?q=bihta")
                self.assertEqual(w.status_code, 200)
                self.assertEqual(w.json()["wards"][0]["key"], "bihta")

                hubs = await client.get("/api/v1/hubs?state=ladakh")
                self.assertEqual(hubs.status_code, 200)
                self.assertEqual(hubs.json()["sovereign_extent"]["states_and_uts_count"], 36)
                self.assertEqual(hubs.json()["count"], 1)

                gs = await client.get("/api/v1/gee-status")
                self.assertEqual(gs.status_code, 200)
                self.assertTrue(gs.json()["zero_key_engines"]["hybrid_rag_bm25_faiss"])

                qr = await client.post("/api/v1/query", json={"query": "ye red color q hain map par", "top_k": 2})
                self.assertEqual(qr.status_code, 200)
                qjson = qr.json()
                self.assertIn("latency_ms", qjson)
                self.assertEqual(qjson["language"], "hinglish")
                self.assertIn("agent2_map_actions", qjson)

                qr_en = await client.post("/api/v1/query", json={"query": "ramayan kaha huaa tha", "top_k": 2, "language": "en"})
                self.assertEqual(qr_en.status_code, 200)
                self.assertEqual(qr_en.json()["language"], "en")

                dem = await client.get("/api/v1/dem-hologram?location=Ayodhya")
                self.assertEqual(dem.status_code, 200)
                djson = dem.json()
                self.assertIn("location", djson)
                if djson.get("live_online"):
                    self.assertEqual(djson["rows"], 8)
                    self.assertEqual(djson["cols"], 8)

                dem10 = await client.get("/api/v1/dem-hologram?location=Rakhigarhi&span_deg=0.04&grid_n=10")
                self.assertEqual(dem10.status_code, 200)
                d10 = dem10.json()
                if d10.get("live_online"):
                    self.assertEqual(d10["rows"], 10)
                    self.assertEqual(d10["cols"], 10)

                sat_tile = await client.get("/api/v1/sat-tile/14/11655/6758?layer=hybrid")
                self.assertIn(sat_tile.status_code, (200, 502))
                if sat_tile.status_code == 200:
                    self.assertEqual(sat_tile.headers.get("access-control-allow-origin"), "*")

                loc_bad = await client.get("/api/v1/location-intelligence?lat=999&lon=999")
                self.assertEqual(loc_bad.status_code, 422)

                loc_ok = await client.get("/api/v1/location-intelligence?lat=34.1526&lon=77.5771&place_name=Leh&radius_km=15")
                self.assertEqual(loc_ok.status_code, 200)
                ljson = loc_ok.json()
                self.assertEqual(ljson["modules_count"], 15)
                self.assertEqual(ljson["location_context"]["state"], "Ladakh")
                self.assertEqual(ljson["location_context"]["crs"], "EPSG:4326")

        asyncio.run(_probe())

    def test_mcp_server_registration_8_tools(self):
        mcp = create_mcp_server()
        self.assertEqual(mcp.name, "bhu-loka-geospatial")
        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager.list_tools()
        else:
            tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        expected = {
            "query_bhu_loka_rag",
            "get_patna_ward_ulsi",
            "get_india_sovereign_hubs",
            "fetch_live_hydromet_and_flood",
            "fetch_live_satellites",
            "build_3d_location_hologram",
            "get_google_earth_gee_workflow",
            "get_system_api_health",
        }
        self.assertTrue(expected.issubset(names), f"Missing MCP tools: {expected - names}")

    def test_universal_location_intelligence_15_modules(self):
        import bhu_loka_location_engine as loc_engine
        from bhu_loka_location_engine import fetch_universal_location_intelligence
        # Reject out-of-range coordinates instead of silent fallback/clamping
        with self.assertRaises(ValueError):
            fetch_universal_location_intelligence(999.0, 999.0)
        with self.assertRaises(ValueError):
            fetch_universal_location_intelligence(25.5, 85.1, radius_km=0.0)

        valid_gis_statuses = ("LIVE", "CACHED", "VERIFIED_LOCAL", "EMPTY", "UNAVAILABLE")

        # Test metropolitan location (Mumbai) & canonical LocationContext schema
        intel = fetch_universal_location_intelligence(19.0760, 72.8777, place_name="Mumbai", radius_km=15.0, timeout=3.0)
        self.assertEqual(intel["modules_count"], 15)
        ctx = intel["location_context"]
        for key in ("latitude", "longitude", "placeName", "administrativeBoundary", "selectedAt", "analysisRadius", "crs"):
            self.assertIn(key, ctx)
        self.assertEqual(ctx["state"], "Maharashtra")
        self.assertEqual(ctx["crs"], "EPSG:4326")
        self.assertEqual(ctx["analysisRadius"], 15.0)
        mods = intel["modules"]
        self.assertIn("1_weather_temperature", mods)
        self.assertIn(mods["1_weather_temperature"]["status"], ("LIVE", "UNAVAILABLE"))
        self.assertIn("3_rivers_waterbodies", mods)
        self.assertIn(mods["3_rivers_waterbodies"]["status"], ("LIVE", "UNAVAILABLE"))
        self.assertIn("4_flood_waterlogging", mods)
        self.assertIn("5_air_quality_pollution", mods)
        self.assertIn("9_terrain_elevation", mods)

        # Module 10: Roads & Infrastructure (real GIS layer wiring, zero fabricated closures)
        self.assertIn("10_roads_infrastructure", mods)
        infra = mods["10_roads_infrastructure"]
        self.assertIn(infra["status"], valid_gis_statuses)
        self.assertTrue(bool(infra.get("source_attribution")))
        self.assertTrue(bool(infra.get("updated_at_utc")))
        self.assertEqual(infra.get("radius_km"), 15.0)
        self.assertIsInstance(infra.get("incidents"), list)
        self.assertEqual(infra.get("incident_count"), len(infra["incidents"]))
        self.assertEqual(infra.get("road_closure_count"), len(infra.get("road_closures", [])))
        self.assertEqual(infra.get("traffic_advisory_count"), len(infra.get("traffic_advisories", [])))
        if infra["status"] == "UNAVAILABLE":
            self.assertTrue(bool(infra.get("unavailable_reason")))
            self.assertTrue(bool(infra.get("limitations")))

        # Module 11: Hospitals & Public Amenities (real GIS layer wiring, zero template hospital names)
        self.assertIn("11_hospitals_public_amenities", mods)
        hosp = mods["11_hospitals_public_amenities"]
        self.assertIn(hosp["status"], valid_gis_statuses)
        self.assertTrue(bool(hosp.get("source_attribution")))
        self.assertTrue(bool(hosp.get("updated_at_utc")))
        self.assertEqual(hosp.get("radius_km"), 15.0)
        self.assertIsInstance(hosp.get("facilities"), list)
        self.assertEqual(hosp.get("facility_count"), len(hosp["facilities"]))
        self.assertNotIn("nearest_tertiary_care", hosp)
        self.assertNotIn("District Sadar / Referral Hospital", json.dumps(hosp))
        for fac in hosp["facilities"]:
            for req_key in (
                "name",
                "facility_type",
                "distance_km",
                "address",
                "contact_info",
                "emergency_helpline",
                "observation_time_utc",
            ):
                self.assertIn(req_key, fac)
        if hosp["status"] == "UNAVAILABLE":
            self.assertTrue(bool(hosp.get("unavailable_reason")))
            self.assertTrue(bool(hosp.get("limitations")))

        self.assertIn("12_public_camera_discovery", mods)
        self.assertIn("14_historical_hazard_profile", mods)
        self.assertIn("15_land_suitability_analysis", mods)
        # Verify data sources registry
        self.assertGreaterEqual(len(intel["sources_registry"]), 10)

        # Offline mock: verify non-blocking fail-closed behavior & radius_km propagation
        with loc_engine._LOCATION_CACHE_LOCK:
            loc_engine._LOCATION_CACHE.clear()
        with patch.object(loc_engine.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            offline_intel = fetch_universal_location_intelligence(
                27.5861, 91.8594, place_name="Tawang", radius_km=12.0, timeout=2.0
            )
        self.assertEqual(offline_intel["modules_count"], 15)
        off_infra = offline_intel["modules"]["10_roads_infrastructure"]
        self.assertEqual(off_infra["status"], "UNAVAILABLE")
        self.assertEqual(off_infra["radius_km"], 12.0)
        self.assertEqual(off_infra["incident_count"], 0)
        self.assertEqual(off_infra["incidents"], [])
        self.assertTrue(bool(off_infra.get("unavailable_reason")))
        self.assertTrue(bool(off_infra.get("source_attribution")))
        self.assertTrue(bool(off_infra.get("updated_at_utc")))

        off_hosp = offline_intel["modules"]["11_hospitals_public_amenities"]
        self.assertEqual(off_hosp["status"], "UNAVAILABLE")
        self.assertEqual(off_hosp["radius_km"], 12.0)
        self.assertEqual(off_hosp["facility_count"], 0)
        self.assertEqual(off_hosp["facilities"], [])
        self.assertTrue(bool(off_hosp.get("unavailable_reason")))
        self.assertTrue(bool(off_hosp.get("source_attribution")))
        self.assertTrue(bool(off_hosp.get("updated_at_utc")))
        self.assertNotIn("District Sadar / Referral Hospital", json.dumps(off_hosp))


if __name__ == "__main__":
    unittest.main()
