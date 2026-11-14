import asyncio
import contextlib
import gc
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "..", ".."))
PIPELINES_DIR = os.path.abspath(os.path.join(ROOT_DIR, "Pipelines"))
for p in (APP_DIR, PIPELINES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_agri_engine as agri
import bhu_loka_india_db_setup as db_setup
import main


def _patna_box(half_deg: float = 0.0009):
    c_lat, c_lon = 25.536, 84.851
    return {
        "type": "Polygon",
        "coordinates": [[
            [c_lon - half_deg, c_lat - half_deg],
            [c_lon + half_deg, c_lat - half_deg],
            [c_lon + half_deg, c_lat + half_deg],
            [c_lon - half_deg, c_lat + half_deg],
            [c_lon - half_deg, c_lat - half_deg],
        ]],
    }


class TestAgriEngineCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prod_db_path = Path(ROOT_DIR) / "Data" / "01_Boundaries" / "bhu_loka_india_intel.sqlite"
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = Path(cls.tmp_dir.name) / "test_agri.sqlite"
        shutil.copy2(cls.prod_db_path, cls.test_db_path)
        cls._prev_env = os.environ.get("BHU_LOKA_INDIA_DB_PATH")
        os.environ["BHU_LOKA_INDIA_DB_PATH"] = str(cls.test_db_path)
        with contextlib.closing(sqlite3.connect(str(cls.test_db_path))) as conn:
            db_setup.ensure_normalized_schema(conn)

    @classmethod
    def tearDownClass(cls):
        if cls._prev_env is None:
            os.environ.pop("BHU_LOKA_INDIA_DB_PATH", None)
        else:
            os.environ["BHU_LOKA_INDIA_DB_PATH"] = cls._prev_env
        gc.collect()
        cls.tmp_dir.cleanup()

    def test_polygon_utm_area_and_validation(self):
        # 0.0018 deg x 0.0018 deg box around Patna (~25.536N, 84.851E) -> ~199.3m x ~180.9m = ~3.60 ha
        m = agri.validate_and_measure_polygon(_patna_box(0.0009))
        self.assertEqual(m["crs"], "EPSG:4326")
        self.assertEqual(m["utm_epsg"], "EPSG:32645")
        self.assertEqual(m["utm_zone_label"], "45N")
        self.assertAlmostEqual(m["area_hectares"], 3.60, delta=0.25)
        self.assertAlmostEqual(m["area_acres"], m["area_hectares"] * 2.4710538, delta=0.01)
        self.assertGreater(m["perimeter_m"], 700.0)

        with self.assertRaises(ValueError):
            agri.validate_and_measure_polygon({"type": "Point", "coordinates": [84.85, 25.53]})
        with self.assertRaises(ValueError):
            agri.validate_and_measure_polygon({"type": "Polygon", "coordinates": [[[84.85, 25.53], [84.86, 25.53]]]})
        with self.assertRaises(ValueError):
            agri.validate_and_measure_polygon({"type": "Polygon", "coordinates": [[[210.0, 25.5], [84.86, 25.5], [84.86, 25.51]]]})

    def test_farm_crud_multiplot_scouting_and_geojson(self):
        parent = agri.create_farm(
            farm_name="Bihta Block North",
            geometry=_patna_box(0.0009),
            crop_name="Wheat HD-2967",
            growth_stage="Tillering",
            state_name="Bihar",
            district_name="Patna",
            db_path=self.test_db_path,
        )
        self.assertTrue(parent["farm_id"].startswith("FARM_"))
        self.assertIn("NOT claimed", parent["ownership_disclaimer"])

        child = agri.create_farm(
            farm_name="Bihta Plot B",
            geometry=_patna_box(0.0005),
            crop_name="Paddy",
            growth_stage="Vegetative",
            parent_farm_id=parent["farm_id"],
            db_path=self.test_db_path,
        )
        self.assertEqual(child["parent_farm_id"], parent["farm_id"])

        with self.assertRaises(ValueError):
            agri.create_farm("Bad Parent Plot", _patna_box(0.0005), parent_farm_id="FARM_MISSING", db_path=self.test_db_path)

        log = agri.add_scouting_log(
            farm_id=parent["farm_id"],
            category="moisture",
            severity="MODERATE",
            notes="Topsoil cracking noted along east bund after 9 dry days.",
            crop_stage="Tillering",
            yield_kg_per_ha=4150.0,
            db_path=self.test_db_path,
        )
        self.assertTrue(log["log_id"].startswith("LOG_"))

        loaded = agri.get_farm(parent["farm_id"], db_path=self.test_db_path)
        self.assertEqual(len(loaded["scouting_logs"]), 1)
        self.assertEqual(loaded["scouting_logs"][0]["yield_kg_per_ha"], 4150.0)

        fc = agri.export_farm_geojson(parent["farm_id"], db_path=self.test_db_path)
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertIn("CRS84", fc["crs"]["properties"]["name"])
        self.assertIn("NOT verified", fc["attribution"])
        self.assertEqual(fc["features"][0]["id"], parent["farm_id"])

        updated = agri.update_farm(
            parent["farm_id"],
            geometry=_patna_box(0.0012),
            growth_stage="Booting",
            db_path=self.test_db_path,
        )
        self.assertGreater(updated["area_hectares"], parent["area_hectares"])
        self.assertEqual(updated["growth_stage"], "Booting")

        self.assertTrue(agri.delete_farm(child["farm_id"], db_path=self.test_db_path))
        self.assertTrue(agri.delete_farm(parent["farm_id"], db_path=self.test_db_path))

    def test_satellite_indices_offline_empty_and_live_delta(self):
        farm = agri.create_farm("SatTestPlot", _patna_box(0.0009), crop_name="Paddy", db_path=self.test_db_path)
        try:
            # 1. Fail-closed offline test (must NOT fabricate or cache)
            with patch.object(agri, "_http_json", side_effect=OSError("network unreachable")):
                offline = agri.fetch_farm_satellite_indices(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(offline["status"], "UNAVAILABLE")
            self.assertIsNone(offline["latest_indices"])
            self.assertIn("zero synthetic", offline["unavailable_reason"])

            # 2. Cloud filter empty response
            with patch.object(agri, "_http_json", return_value={"features": []}):
                empty_res = agri.fetch_farm_satellite_indices(farm["farm_id"], max_cloud_pct=5.0, db_path=self.test_db_path)
            self.assertEqual(empty_res["status"], "EMPTY")
            self.assertEqual(empty_res["scenes"], [])

            # 3. Two Sentinel-2 L2A scenes with TiTiler band reflectance stats
            def fake_http(url, method="GET", payload=None, timeout=7.0):
                if url == agri.STAC_SEARCH_URL:
                    return {
                        "features": [
                            {
                                "id": "S2A_MSIL2A_20261110_PATNA",
                                "properties": {"datetime": "2026-11-10T04:55:00Z", "eo:cloud_cover": 4.2},
                                "assets": {"rendered_preview": {"href": "https://planetarycomputer.microsoft.com/preview1.png"}},
                            },
                            {
                                "id": "S2B_MSIL2A_20261026_PATNA",
                                "properties": {"datetime": "2026-10-26T04:55:00Z", "eo:cloud_cover": 8.0},
                                "assets": {"rendered_preview": {"href": "https://planetarycomputer.microsoft.com/preview2.png"}},
                            },
                        ]
                    }
                if url.startswith(agri.SAS_SIGN_URL):
                    return {"href": "https://planetarycomputer.microsoft.com/signed.png?sig=abc"}
                if "S2A_MSIL2A_20261110_PATNA" in url:
                    return {
                        "properties": {
                            "statistics": {
                                "B02": {"mean": 600, "valid_percent": 98.5, "count": 400},
                                "B03": {"mean": 900, "valid_percent": 98.5, "count": 400},
                                "B04": {"mean": 700, "valid_percent": 98.5, "count": 400},
                                "B05": {"mean": 1500, "valid_percent": 98.5, "count": 100},
                                "B08": {"mean": 3500, "std": 350, "min": 2800, "max": 4200, "valid_percent": 98.5, "count": 400},
                                "B11": {"mean": 2100, "valid_percent": 98.5, "count": 100},
                            }
                        }
                    }
                return {
                    "properties": {
                        "statistics": {
                            "B02": {"mean": 700, "valid_percent": 96.0},
                            "B03": {"mean": 950, "valid_percent": 96.0},
                            "B04": {"mean": 1000, "valid_percent": 96.0},
                            "B05": {"mean": 1600, "valid_percent": 96.0},
                            "B08": {"mean": 2500, "std": 450, "min": 1800, "max": 3100, "valid_percent": 96.0, "count": 385},
                            "B11": {"mean": 2000, "valid_percent": 96.0},
                        }
                    }
                }

            with patch.object(agri, "_http_json", side_effect=fake_http):
                live = agri.fetch_farm_satellite_indices(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(live["status"], "LIVE")
            self.assertFalse(live["cached"])
            self.assertEqual(len(live["scenes"]), 2)
            # Latest: (0.35 - 0.07)/(0.35 + 0.07) = 0.28/0.42 = 0.6667
            self.assertAlmostEqual(live["latest_indices"]["ndvi"], 0.6667, places=4)
            # GNDVI: (0.35 - 0.09)/(0.35 + 0.09) = 0.26/0.44 = 0.5909
            self.assertAlmostEqual(live["latest_indices"]["gndvi"], 0.5909, places=4)
            # BSI: ((0.21 + 0.07) - (0.35 + 0.06)) / ((0.21 + 0.07) + (0.35 + 0.06)) = (0.28 - 0.41) / 0.69 = -0.1884
            self.assertAlmostEqual(live["latest_indices"]["bsi"], -0.1884, places=4)
            # Baseline: (0.25 - 0.10)/(0.25 + 0.10) = 0.15/0.35 = 0.4286; delta = +0.2381
            self.assertIsNotNone(live["ndvi_delta"])
            self.assertAlmostEqual(live["ndvi_delta"]["delta_ndvi"], 0.2381, places=4)
            for idx_key in ("ndvi", "ndre", "evi", "savi", "ndwi_gao", "ndwi_mcfeeters", "gndvi", "bsi"):
                self.assertIsNotNone(live["latest_indices"][idx_key])
            zonal = live["latest_zonal_dispersion"]
            self.assertIsNotNone(zonal)
            self.assertEqual(zonal["nir_cv_pct"], 10.0)
            self.assertEqual(zonal["uniformity_class"], "UNIFORM_CANOPY")
            self.assertEqual(zonal["valid_pixels"], 400)

            # Second call hits SQLite cache without calling _http_json
            with patch.object(agri, "_http_json", side_effect=AssertionError("should read cache")):
                cached = agri.fetch_farm_satellite_indices(farm["farm_id"], db_path=self.test_db_path)
            self.assertTrue(cached["cached"])
            self.assertAlmostEqual(cached["latest_indices"]["ndvi"], 0.6667, places=4)
        finally:
            agri.delete_farm(farm["farm_id"], db_path=self.test_db_path)

    def test_sar_wetness_offline_empty_and_live_classification(self):
        farm = agri.create_farm("SarWetnessPlot", _patna_box(0.0009), crop_name="Paddy", db_path=self.test_db_path)
        try:
            with patch.object(agri, "_http_json", side_effect=OSError("offline-sar")):
                off = agri.fetch_farm_sar_wetness(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(off["status"], "UNAVAILABLE")
            self.assertIsNone(off["latest_sar"])
            self.assertIn("zero synthetic SAR", off["unavailable_reason"])

            with patch.object(agri, "_http_json", return_value={"features": []}):
                emp = agri.fetch_farm_sar_wetness(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(emp["status"], "EMPTY")
            self.assertEqual(emp["scenes"], [])

            def fake_sar_http(url, method="GET", payload=None, timeout=10.0):
                if url == agri.STAC_SEARCH_URL:
                    return {
                        "features": [
                            {
                                "id": "S1D_IW_GRDH_LATEST_RTC",
                                "properties": {
                                    "datetime": "2026-11-08T12:21:00Z",
                                    "sat:orbit_state": "ascending",
                                    "sar:instrument_mode": "IW",
                                    "sar:polarizations": ["VV", "VH"],
                                },
                            },
                            {
                                "id": "S1A_IW_GRDH_PREV_RTC",
                                "properties": {
                                    "datetime": "2026-10-27T12:21:00Z",
                                    "sat:orbit_state": "ascending",
                                    "sar:instrument_mode": "IW",
                                    "sar:polarizations": ["VV", "VH"],
                                },
                            },
                        ]
                    }
                if "S1D_IW_GRDH_LATEST_RTC" in url:
                    return {
                        "vv_b1": {"mean": 0.17, "valid_pixels": 380, "valid_percent": 100.0},
                        "vh_b1": {"mean": 0.054, "valid_pixels": 380, "valid_percent": 100.0},
                    }
                return {
                    "vv_b1": {"mean": 0.025, "valid_pixels": 380, "valid_percent": 100.0},
                    "vh_b1": {"mean": 0.006, "valid_pixels": 380, "valid_percent": 100.0},
                }

            with patch.object(agri, "_http_json", side_effect=fake_sar_http):
                live = agri.fetch_farm_sar_wetness(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(live["status"], "LIVE")
            self.assertFalse(live["cached"])
            self.assertEqual(len(live["scenes"]), 2)
            # 10*log10(0.17) = -7.70 dB; 10*log10(0.054) = -12.68 dB; VH/VV = -4.98 dB
            self.assertAlmostEqual(live["latest_sar"]["vv_mean_db"], -7.70, places=2)
            self.assertAlmostEqual(live["latest_sar"]["vh_mean_db"], -12.68, places=2)
            self.assertAlmostEqual(live["latest_sar"]["vh_vv_ratio_db"], -4.98, places=2)
            self.assertEqual(live["latest_sar"]["wetness_class"], "DENSE_CANOPY_OR_HIGH_MOISTURE_VOLUME")
            # Earlier flooded paddy scene: 10*log10(0.025) = -16.02 dB
            self.assertEqual(live["scenes"][1]["wetness_class"], "SMOOTH_WATER_OR_FLOODED_SURFACE")
            self.assertAlmostEqual(live["vv_delta_db"], 8.32, places=2)

            with patch.object(agri, "_http_json", side_effect=AssertionError("should hit SAR cache")):
                cached = agri.fetch_farm_sar_wetness(farm["farm_id"], db_path=self.test_db_path)
            self.assertTrue(cached["cached"])
        finally:
            agri.delete_farm(farm["farm_id"], db_path=self.test_db_path)

    def test_water_soil_offline_and_live_advisories(self):
        farm = agri.create_farm("SoilWaterPlot", _patna_box(0.0009), crop_name="Wheat", db_path=self.test_db_path)
        try:
            with patch.object(agri, "_http_json", side_effect=OSError("offline")), patch.object(
                agri, "fetch_location_3d_dem", return_value={"live_online": False}
            ):
                off = agri.fetch_farm_water_soil_profile(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(off["agro_weather"]["status"], "UNAVAILABLE")
            self.assertEqual(off["nasa_power"]["status"], "UNAVAILABLE")
            self.assertEqual(off["terrain_drainage"]["status"], "UNAVAILABLE")
            self.assertIn("OUT OF CURRENT SCOPE", off["scope_and_roadmap_status"]["iot_hardware_and_wearables"])

            mock_om = {
                "current": {
                    "soil_moisture_0_to_7cm": 0.14,
                    "soil_moisture_7_to_28cm": 0.15,
                    "soil_temperature_0cm": 29.4,
                    "vapour_pressure_deficit": 2.35,
                },
                "daily": {
                    "time": ["2026-11-12", "2026-11-13", "2026-11-14"],
                    "precipitation_sum": [0.0, 0.5, 0.0],
                    "et0_fao_evapotranspiration": [9.0, 9.2, 8.8],
                    "temperature_2m_max": [36.0, 41.2, 38.0],
                },
            }
            mock_power = {
                "properties": {
                    "parameter": {
                        "T2M_MAX": {"20261108": 32.0, "20261109": -999.0},
                        "T2M_MIN": {"20261108": 18.0},
                        "PRECTOTCORR": {"20261108": 1.2},
                        "ALLSKY_SFC_SW_DWN": {"20261108": 16.5},
                        "RH2M": {"20261108": 62.0},
                        "GWETROOT": {"20261108": 0.58},
                    }
                }
            }
            mock_dem = {"live_online": True, "source_api": "Copernicus GLO-90 DEM", "metrics": {"mean_m": 51.0, "relief_m": 4.0}}
            with patch.object(agri, "_http_json", side_effect=[mock_om, mock_power]), patch.object(
                agri, "fetch_location_3d_dem", return_value=mock_dem
            ):
                live = agri.fetch_farm_water_soil_profile(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(live["agro_weather"]["status"], "LIVE")
            self.assertEqual(live["nasa_power"]["status"], "LIVE")
            self.assertEqual(live["nasa_power"]["t2m_max_mean_c"], 32.0)
            self.assertEqual(live["nasa_power"]["solar_irradiance_mean_mj_m2_day"], 16.5)
            self.assertEqual(live["nasa_power"]["root_zone_wetness_gwetroot"], 0.58)
            self.assertEqual(live["terrain_drainage"]["status"], "LIVE")
            self.assertAlmostEqual(live["agro_weather"]["water_balance_7d_mm"], -26.5, places=2)
            joined_adv = " ".join(live["advisories"])
            self.assertIn("Moisture Deficit Signal", joined_adv)
            self.assertIn("Heatwave Watch", joined_adv)
            # FAO-56 Wheat Tillering -> vegetative Kc = 0.80; ET0 7d = 27.0 -> ETc_7d = 21.6 mm
            fao = live["fao56_etc"]
            self.assertEqual(fao["status"], "LIVE")
            self.assertEqual(fao["crop_key"], "wheat")
            self.assertEqual(fao["stage_key"], "vegetative")
            self.assertAlmostEqual(fao["kc"], 0.80, places=2)
            self.assertAlmostEqual(fao["etc_7d_mm"], 21.6, places=2)
            self.assertGreater(fao["gross_volume_m3_7d"], 0.0)
        finally:
            agri.delete_farm(farm["farm_id"], db_path=self.test_db_path)

    def test_soil_health_card_parser_classification_and_fao56_helpers(self):
        farm = agri.create_farm("ShcTestPlot", _patna_box(0.0009), crop_name="Paddy", growth_stage="Heading", db_path=self.test_db_path)
        try:
            csv_payload = "sample_date,lab_name,pH,EC (dS/m),OC (%),Available N (kg/ha),P (kg/ha),K (kg/ha),Zn (ppm)\n2026-11-05,Patna KVK Lab,7.1,0.42,0.44,210,16,245,0.45\n"
            r1 = agri.save_soil_health_report(farm["farm_id"], csv_text=csv_payload, db_path=self.test_db_path)
            self.assertTrue(r1["report_id"].startswith("SHC_"))
            self.assertEqual(r1["source_format"], "CSV_TEXT_PARSER")
            self.assertEqual(r1["classification"]["ratings"]["ph"], "NEUTRAL_OPTIMAL")
            self.assertEqual(r1["classification"]["ratings"]["ec_ds_m"], "NORMAL_NON_SALINE")
            self.assertEqual(r1["classification"]["ratings"]["organic_carbon_pct"], "LOW")
            self.assertEqual(r1["classification"]["ratings"]["nitrogen_kg_ha"], "LOW")
            self.assertEqual(r1["classification"]["ratings"]["phosphorus_kg_ha"], "MEDIUM")
            self.assertEqual(r1["classification"]["ratings"]["potassium_kg_ha"], "MEDIUM")
            self.assertEqual(r1["classification"]["ratings"]["zinc_ppm"], "DEFICIENT")

            kv_payload = "pH: 8.8; EC: 2.3; OC: 0.82; N: 610"
            r2 = agri.save_soil_health_report(farm["farm_id"], csv_text=kv_payload, db_path=self.test_db_path)
            self.assertEqual(r2["classification"]["ratings"]["ph"], "STRONGLY_ALKALINE")
            self.assertEqual(r2["classification"]["ratings"]["ec_ds_m"], "SALINE_HIGH_RISK")
            self.assertEqual(r2["classification"]["ratings"]["organic_carbon_pct"], "HIGH")
            self.assertEqual(r2["classification"]["ratings"]["nitrogen_kg_ha"], "HIGH")

            reports = agri.list_soil_health_reports(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(len(reports), 2)

            with self.assertRaises(ValueError):
                agri.save_soil_health_report(farm["farm_id"], csv_text="invalid non-numeric text", db_path=self.test_db_path)
            with self.assertRaises(ValueError):
                agri.save_soil_health_report(farm["farm_id"], ph=14.0, db_path=self.test_db_path)

            # FAO-56 offline vs live volumetric check (1 mm * 2 ha = 20 m3)
            off_etc = agri.compute_fao56_etc("Paddy", "Heading", 2.0, None, None, None)
            self.assertEqual(off_etc["status"], "UNAVAILABLE")
            self.assertIsNone(off_etc["etc_7d_mm"])

            live_etc = agri.compute_fao56_etc("Paddy", "Heading", 2.0, et0_today_mm=5.0, et0_7d_mm=30.0, precip_7d_mm=10.0)
            self.assertEqual(live_etc["status"], "LIVE")
            self.assertAlmostEqual(live_etc["kc"], 1.20, places=2)
            self.assertAlmostEqual(live_etc["etc_7d_mm"], 36.0, places=2)
            self.assertAlmostEqual(live_etc["net_crop_water_deficit_7d_mm"], -26.0, places=2)
            self.assertAlmostEqual(live_etc["gross_volume_m3_7d"], 520.0, places=1)
        finally:
            agri.delete_farm(farm["farm_id"], db_path=self.test_db_path)

    def test_nasa_cmr_and_landsat_discovery(self):
        farm = agri.create_farm("NasaEoPlot", _patna_box(0.0009), crop_name="Paddy", db_path=self.test_db_path)
        try:
            with patch.object(agri, "_http_json", side_effect=OSError("offline")):
                off = agri.fetch_nasa_earthdata_granules(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(off["status"], "UNAVAILABLE")
            self.assertEqual(len(off["datasets"]), 4)
            self.assertTrue(all(d["status"] == "UNAVAILABLE" for d in off["datasets"]))

            def fake_nasa_http(url, method="GET", payload=None, timeout=7.0):
                if "cmr.earthdata.nasa.gov" in url:
                    return {
                        "feed": {
                            "entry": [
                                {
                                    "id": "G123456-LPCLOUD",
                                    "title": "MODIS_GRANULE_PATNA",
                                    "time_start": "2026-11-01T00:00:00Z",
                                    "time_end": "2026-11-08T23:59:59Z",
                                    "cloud_cover": "5",
                                }
                            ]
                        }
                    }
                return {
                    "features": [
                        {
                            "id": "LC09_L2SP_141042_20261104",
                            "properties": {"datetime": "2026-11-04T04:45:00Z", "eo:cloud_cover": 6.5, "platform": "landsat-9"},
                        }
                    ]
                }

            with patch.object(agri, "_http_json", side_effect=fake_nasa_http):
                live = agri.fetch_nasa_earthdata_granules(farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(live["status"], "LIVE")
            self.assertEqual(len(live["datasets"]), 4)
            for ds in live["datasets"]:
                for key in ("provider", "product_id", "acquisition_date", "spatial_resolution", "temporal_resolution", "crs", "license_and_usage", "processing_methodology", "quality_and_missing_data", "source_attribution"):
                    self.assertIn(key, ds)
                    self.assertTrue(ds[key])
        finally:
            agri.delete_farm(farm["farm_id"], db_path=self.test_db_path)

    def test_fastapi_agri_endpoints_and_farm_aware_rag_asgi(self):
        async def _run():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                c_res = await client.post(
                    "/api/v1/agri/farms",
                    json={
                        "farm_name": "ASGI Wheat Field",
                        "geometry": _patna_box(0.0009),
                        "crop_name": "Wheat",
                        "growth_stage": "Heading",
                        "state_name": "Bihar",
                        "district_name": "Patna",
                    },
                )
                self.assertEqual(c_res.status_code, 200)
                created = c_res.json()
                fid = created["farm_id"]

                try:
                    l_res = await client.get("/api/v1/agri/farms")
                    self.assertEqual(l_res.status_code, 200)
                    self.assertTrue(any(f["farm_id"] == fid for f in l_res.json()["farms"]))

                    g_res = await client.get(f"/api/v1/agri/farms/{fid}/export-geojson")
                    self.assertEqual(g_res.status_code, 200)
                    self.assertIn("application/geo+json", g_res.headers["content-type"])

                    with patch.object(agri, "_http_json", side_effect=OSError("offline-mock")), patch.object(
                        agri, "fetch_location_3d_dem", return_value={"live_online": False}
                    ):
                        sat_res = await client.get(f"/api/v1/agri/farms/{fid}/satellite")
                        self.assertEqual(sat_res.status_code, 200)
                        self.assertEqual(sat_res.json()["status"], "UNAVAILABLE")

                        ws_res = await client.get(f"/api/v1/agri/farms/{fid}/water-soil")
                        self.assertEqual(ws_res.status_code, 200)
                        self.assertEqual(ws_res.json()["agro_weather"]["status"], "UNAVAILABLE")
                        self.assertEqual(ws_res.json()["nasa_power"]["status"], "UNAVAILABLE")

                        nasa_res = await client.get(f"/api/v1/agri/farms/{fid}/nasa-eo")
                        self.assertEqual(nasa_res.status_code, 200)
                        self.assertEqual(nasa_res.json()["status"], "UNAVAILABLE")

                        sar_res = await client.get(f"/api/v1/agri/farms/{fid}/sar-wetness")
                        self.assertEqual(sar_res.status_code, 200)
                        self.assertEqual(sar_res.json()["status"], "UNAVAILABLE")

                        etc_off = await client.get(f"/api/v1/agri/farms/{fid}/fao56-etc")
                        self.assertEqual(etc_off.status_code, 200)
                        self.assertEqual(etc_off.json()["fao56_etc"]["status"], "UNAVAILABLE")

                    shc_post = await client.post(
                        f"/api/v1/agri/farms/{fid}/soil-health",
                        json={"ph": 7.2, "ec_ds_m": 0.45, "organic_carbon_pct": 0.44, "nitrogen_kg_ha": 230.0, "phosphorus_kg_ha": 18.0, "potassium_kg_ha": 220.0},
                    )
                    self.assertEqual(shc_post.status_code, 200)
                    shc_saved = shc_post.json()
                    self.assertEqual(shc_saved["classification"]["ratings"]["nitrogen_kg_ha"], "LOW")

                    shc_list = await client.get(f"/api/v1/agri/farms/{fid}/soil-health")
                    self.assertEqual(shc_list.status_code, 200)
                    self.assertEqual(shc_list.json()["count"], 1)

                    cad_res = await client.get(f"/api/v1/agri/farms/{fid}/cadastral-advisory")
                    self.assertEqual(cad_res.status_code, 200)
                    cad_json = cad_res.json()
                    self.assertEqual(cad_json["status"], "VERIFIED_DIRECTORY_LINK")
                    self.assertEqual(cad_json["resolved_admin"]["state"], "Bihar")
                    self.assertIn("biharbhumi", cad_json["dilrmp_portal"]["ror_portal_url"].lower())

                    port_res = await client.get(f"/api/v1/agri/farms/{fid}/portfolio-summary")
                    self.assertEqual(port_res.status_code, 200)
                    port_json = port_res.json()
                    self.assertEqual(port_json["plot_count"], 1)
                    self.assertIsNone(port_json["area_weighted_cached_ndvi"])

                    agri_ctx = {
                        "schema": "bhu-loka-agri-context-v1",
                        "farm_id": fid,
                        "farm_name": "ASGI Wheat Field",
                        "crop_name": "Wheat",
                        "growth_stage": "Heading",
                        "location": {"state": "Bihar", "district": "Patna", "centroid_lat": 25.536, "centroid_lon": 84.851, "utm_epsg": "EPSG:32645"},
                        "geometry_metrics": {"area_hectares": created["area_hectares"], "area_acres": created["area_acres"]},
                        "satellite_status": "LIVE",
                        "latest_indices": {"ndvi": 0.62, "ndre": 0.38, "ndwi_gao": 0.19, "gndvi": 0.56, "bsi": -0.15},
                        "latest_zonal_dispersion": {"reference_band": "B08 (NIR 10m)", "nir_cv_pct": 10.2, "uniformity_class": "UNIFORM_CANOPY", "valid_pixels": 380},
                        "sar_wetness": {
                            "status": "LIVE",
                            "latest_sar": {
                                "acquired_utc": "2026-11-08T12:21:00Z",
                                "orbit_state": "ascending",
                                "vv_mean_db": -7.69,
                                "vh_mean_db": -12.69,
                                "vh_vv_ratio_db": -5.0,
                                "wetness_class": "DENSE_CANOPY_OR_HIGH_MOISTURE_VOLUME",
                            },
                        },
                        "water_soil": {
                            "agro_weather": {"status": "LIVE", "soil_moisture_7_to_28cm_m3_m3": 0.24, "et0_today_mm": 4.2, "water_balance_7d_mm": -6.5},
                            "fao56_etc": {"status": "LIVE", "crop_key": "wheat", "stage_key": "mid", "kc": 1.15, "etc_today_mm": 4.83, "etc_7d_mm": 32.0, "net_crop_water_deficit_7d_mm": -18.0, "gross_volume_m3_7d": 580.0},
                            "latest_soil_health": shc_saved,
                            "nasa_power": {"status": "LIVE", "solar_irradiance_mean_mj_m2_day": 16.5, "root_zone_wetness_gwetroot": 0.58},
                            "terrain_drainage": {"elevation_mean_masl_m": 51.2, "drainage_note": "Gentle agricultural grade."},
                            "advisories": ["Balanced short-term moisture profile based on ECMWF/Open-Meteo ET0 and root-zone soil moisture."],
                        },
                    }
                    q_res = await client.post(
                        "/api/v1/query",
                        json={"query": "What is the current NDVI and root-zone soil moisture for my farm?", "agri_context": agri_ctx},
                    )
                    self.assertEqual(q_res.status_code, 200)
                    q_json = q_res.json()
                    self.assertTrue(any(s.get("id") == "live_farm_agri_context" for s in q_json.get("retrieved_sources", [])))
                    self.assertGreaterEqual(q_json["eval_metrics"]["faithfulness"], 0.70)
                    self.assertTrue(q_json["guardrails"]["passed"])
                finally:
                    d_res = await client.delete(f"/api/v1/agri/farms/{fid}")
                    self.assertEqual(d_res.status_code, 200)

        asyncio.run(_run())

    def test_cadastral_advisory_and_multiplot_portfolio(self):
        root_farm = agri.create_farm(
            farm_name="Bihta Main Farm",
            geometry=_patna_box(0.0010),
            crop_name="Wheat",
            growth_stage="Mid",
            state_name="Maharashtra",  # intentional mismatch to verify mismatch warning
            district_name="Patna",
            db_path=self.test_db_path,
        )
        sub_farm = agri.create_farm(
            farm_name="Bihta East Subplot",
            geometry=_patna_box(0.0005),
            crop_name="Mustard",
            growth_stage="Vegetative",
            state_name="Bihar",
            district_name="Patna",
            parent_farm_id=root_farm["farm_id"],
            db_path=self.test_db_path,
        )
        foreign_farm = agri.create_farm(
            farm_name="Out of India Test Plot",
            geometry={
                "type": "Polygon",
                "coordinates": [[[2.350, 48.855], [2.352, 48.855], [2.352, 48.857], [2.350, 48.857], [2.350, 48.855]]],
            },
            crop_name="Wheat",
            db_path=self.test_db_path,
        )
        try:
            cad = agri.resolve_farm_cadastral_advisory(root_farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(cad["resolved_admin"]["state"], "Bihar")
            self.assertIsNotNone(cad["resolved_admin"]["state_mismatch_warning"])
            self.assertIn("Khata", cad["cadastral_disclaimer"])

            cad_out = agri.resolve_farm_cadastral_advisory(foreign_farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(cad_out["status"], "OUTSIDE_INDIA")
            self.assertIsNone(cad_out["dilrmp_portal"]["ror_portal_url"])

            # Empty cached portfolio -> never fabricates NDVI
            mp0 = agri.compute_multiplot_summary(sub_farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(mp0["cluster_root_id"], root_farm["farm_id"])
            self.assertEqual(mp0["plot_count"], 2)
            self.assertAlmostEqual(
                mp0["total_area_hectares"],
                round(root_farm["area_hectares"] + sub_farm["area_hectares"], 4),
                places=4,
            )
            self.assertIsNone(mp0["area_weighted_cached_ndvi"])
            self.assertEqual(len(mp0["crop_mix"]), 2)

            # Seed real cached optical stats via DB cache table for weighted mean test
            with agri._get_agri_conn(self.test_db_path) as conn:
                conn.execute(
                    "INSERT INTO agri_satellite_cache (cache_key, farm_id, payload_json, cached_at_epoch) VALUES (?, ?, ?, ?)",
                    ("sat_test_1", root_farm["farm_id"], json.dumps({"latest_indices": {"ndvi": 0.60, "gndvi": 0.55}, "scenes": [{"acquired_utc": "2026-11-05T05:00:00Z"}]}), 9999999999.0),
                )
                conn.execute(
                    "INSERT INTO agri_satellite_cache (cache_key, farm_id, payload_json, cached_at_epoch) VALUES (?, ?, ?, ?)",
                    ("sat_test_2", sub_farm["farm_id"], json.dumps({"latest_indices": {"ndvi": 0.40, "gndvi": 0.35}, "scenes": [{"acquired_utc": "2026-11-05T05:00:00Z"}]}), 9999999999.0),
                )
            expected_weighted = round(
                (0.60 * root_farm["area_hectares"] + 0.40 * sub_farm["area_hectares"])
                / (root_farm["area_hectares"] + sub_farm["area_hectares"]),
                4,
            )
            mp1 = agri.compute_multiplot_summary(root_farm["farm_id"], db_path=self.test_db_path)
            self.assertEqual(mp1["plots_with_cached_ndvi"], 2)
            self.assertAlmostEqual(mp1["area_weighted_cached_ndvi"], expected_weighted, places=4)
        finally:
            agri.delete_farm(sub_farm["farm_id"], db_path=self.test_db_path)
            agri.delete_farm(root_farm["farm_id"], db_path=self.test_db_path)
            agri.delete_farm(foreign_farm["farm_id"], db_path=self.test_db_path)


if __name__ == "__main__":
    unittest.main()
