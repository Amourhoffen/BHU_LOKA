from typing import Optional
from config.settings import settings
from ingestion.loader import KnowledgeLoader
from embeddings.embedder import SovereignDenseEmbedder
from vectorstore.vector_db import SovereignVectorDB
from rag.retriever import HybridRetriever
from rag.prompt_builder import PromptBuilder
from rag.generator import LocalSovereignGenerator
from rag.reranker import plan_agent2_map_actions


class RAGPipeline:
    """
    End-to-End Dual-Agent Enterprise RAG Pipeline orchestrating:
      Agent 1: Ingestion -> BM25 + Transformer Vector Search (FAISS) -> RRF -> Cross Re-Ranker -> Multilingual Grounded Synthesis
      Agent 2: Autonomous Cartographic Director returning synchronized 3D/2D Map & Auto-Hologram Actions
    """

    def __init__(self, preload_transformer: Optional[bool] = None, enable_transformer: Optional[bool] = None):
        self.loader = KnowledgeLoader(settings.crime_data_path)
        use_trans = settings.enable_transformer if enable_transformer is None else enable_transformer
        do_preload = settings.preload_transformer if preload_transformer is None else preload_transformer

        self.embedder = SovereignDenseEmbedder(
            n_components=24,
            model_name=settings.transformer_model,
            cache_path=settings.embedding_cache_path,
            enable_transformer=use_trans,
        )
        self.vector_db = SovereignVectorDB(dim=settings.embedding_dim)
        self.generator = LocalSovereignGenerator()
        self.documents: list[dict] = []
        self._doc_texts: list[str] = []
        self.retriever: HybridRetriever = self._initialize(preload_transformer=do_preload)

    def _initialize(self, preload_transformer: bool = False) -> HybridRetriever:
        self.documents = self.loader.load_all_documents()
        self._doc_texts = [
            f"{doc.get('title', '')} {doc.get('keywords', '')} {doc.get('content', '')}"
            for doc in self.documents
        ]
        svd_embs = self.embedder.fit_transform(self._doc_texts)
        self.vector_db.build_index(svd_embs, self.documents)

        if self.embedder.transformer_doc_vecs is not None:
            self.vector_db.build_transformer_index(self.embedder.transformer_doc_vecs)

        if preload_transformer and self.embedder.enable_transformer:
            self.ensure_transformer_ready()

        return HybridRetriever(
            embedder=self.embedder,
            vector_db=self.vector_db,
            documents=self.documents,
            rrf_k=settings.rrf_k,
        )

    def ensure_transformer_ready(self) -> bool:
        """Load local SentenceTransformer (`all-MiniLM-L6-v2`) synchronously & activate 384-d FAISS index."""
        ok = self.embedder.load_transformer_sync(texts=self._doc_texts)
        if ok and self.embedder.transformer_doc_vecs is not None:
            self.vector_db.build_transformer_index(self.embedder.transformer_doc_vecs)
        return ok

    def start_background_transformer_warmup(self) -> None:
        """Non-blocking background Transformer warmup for FastAPI daemon runtime."""
        self.embedder.start_background_warmup(
            texts=self._doc_texts,
            on_ready=lambda vecs: self.vector_db.build_transformer_index(vecs),
        )

    @staticmethod
    def _build_agri_context_entry(agri_context: dict) -> dict:
        farm_name = agri_context.get("farm_name") or agri_context.get("farm_id") or "Selected Farm"
        crop = agri_context.get("crop_name") or "Unspecified"
        stage = agri_context.get("growth_stage") or "Unspecified"
        gm = agri_context.get("geometry_metrics") or {}
        loc = agri_context.get("location") or {}
        sat_status = agri_context.get("satellite_status") or "NOT_QUERIED"
        idx = agri_context.get("latest_indices") or {}
        zonal = agri_context.get("latest_zonal_dispersion") or {}
        sar = agri_context.get("sar_wetness") or {}
        scene = agri_context.get("latest_scene") or {}
        ws = (agri_context.get("water_soil") or {}).get("agro_weather") or {}
        npow = (agri_context.get("water_soil") or {}).get("nasa_power") or {}
        neo = agri_context.get("nasa_eo") or {}
        td = (agri_context.get("water_soil") or {}).get("terrain_drainage") or {}
        fao = agri_context.get("fao56_etc") or (agri_context.get("water_soil") or {}).get("fao56_etc") or {}
        shc = agri_context.get("latest_soil_health") or (agri_context.get("water_soil") or {}).get("latest_soil_health") or {}
        advisories = (agri_context.get("water_soil") or {}).get("advisories") or []
        cad = agri_context.get("cadastral_advisory") or {}
        mp = agri_context.get("multiplot_summary") or {}

        parts = [
            f"Active Farm Context: {farm_name} (Crop: {crop}, Stage: {stage}).",
            f"Area: {gm.get('area_hectares', 'N/A')} ha ({gm.get('area_acres', 'N/A')} acres), Perimeter: {gm.get('perimeter_m', 'N/A')} m.",
            f"Location: {loc.get('centroid_lat', 'N/A')} N, {loc.get('centroid_lon', 'N/A')} E ({loc.get('crs', 'EPSG:4326')}, {loc.get('utm_epsg', 'N/A')}).",
            f"Sentinel-2 L2A Status: {sat_status}.",
        ]
        if sat_status == "LIVE" and idx:
            parts.append(
                f"Latest Scene {scene.get('scene_id', '')} ({scene.get('acquired_utc', '')}, cloud {scene.get('cloud_cover_pct', '--')}%): "
                f"NDVI={idx.get('ndvi')}, NDRE={idx.get('ndre')}, EVI={idx.get('evi')}, SAVI={idx.get('savi')}, "
                f"NDWI_Gao={idx.get('ndwi_gao')}, NDWI_McFeeters={idx.get('ndwi_mcfeeters')}, GNDVI={idx.get('gndvi')}, BSI={idx.get('bsi')}."
            )
        if zonal and zonal.get("nir_cv_pct") is not None:
            parts.append(
                f"Zonal Canopy Uniformity ({zonal.get('reference_band', 'B08')}): CV={zonal.get('nir_cv_pct')}%, "
                f"Class={zonal.get('uniformity_class')}, Valid Pixels={zonal.get('valid_pixels')}."
            )
        if sar and sar.get("status"):
            lsar = sar.get("latest_sar") or {}
            if sar.get("status") == "LIVE" and lsar:
                parts.append(
                    f"Sentinel-1 C-SAR RTC ({lsar.get('acquired_utc', '')}, {lsar.get('orbit_state', '')}): "
                    f"VV={lsar.get('vv_mean_db')} dB, VH={lsar.get('vh_mean_db')} dB, "
                    f"VH/VV={lsar.get('vh_vv_ratio_db')} dB, Class={lsar.get('wetness_class')}."
                )
            else:
                parts.append(f"Sentinel-1 C-SAR Status: {sar.get('status')}.")
        if npow:
            parts.append(
                f"NASA LaRC POWER Agro-Climatology ({npow.get('status', 'UNAVAILABLE')}): "
                f"Solar Radiation={npow.get('solar_irradiance_mean_mj_m2_day')} MJ/m2/day, "
                f"Root-Zone Wetness (GWETROOT)={npow.get('root_zone_wetness_gwetroot')}, "
                f"Tmax={npow.get('t2m_max_mean_c')} C."
            )
        if neo and neo.get("datasets"):
            ds_summary = ", ".join(
                f"{d.get('short_name')}:{d.get('status')}" for d in neo["datasets"][:4]
            )
            parts.append(f"NASA CMR / USGS Landsat Discovery ({neo.get('status', 'UNAVAILABLE')}): {ds_summary}.")
        if ws:
            parts.append(
                f"Open-Meteo Agro-Weather ({ws.get('status', 'UNAVAILABLE')}): "
                f"Surface Soil Moisture 0-7cm={ws.get('soil_moisture_0_to_7cm_m3_m3')} m3/m3, "
                f"Root Moisture 7-28cm={ws.get('soil_moisture_7_to_28cm_m3_m3')} m3/m3, "
                f"ET0 7-day={ws.get('et0_7d_mm')} mm, Precip 7-day={ws.get('precip_7d_mm')} mm, "
                f"Water Balance={ws.get('water_balance_7d_mm')} mm, VPD={ws.get('vapour_pressure_deficit_kpa')} kPa."
            )
        if td:
            parts.append(
                f"Terrain ({td.get('status', 'UNAVAILABLE')}): Elevation={td.get('elevation_mean_masl_m')} m, "
                f"Estimated Slope={td.get('estimated_slope_deg')} deg ({td.get('drainage_note', '')})."
            )
        if fao and fao.get("status") == "LIVE":
            parts.append(
                f"FAO-56 Crop Evapotranspiration ({fao.get('crop_key')}/{fao.get('stage_key')}, Kc={fao.get('kc')}): "
                f"ETc today={fao.get('etc_today_mm')} mm, 7d ETc={fao.get('etc_7d_mm')} mm, "
                f"Net 7d Crop Deficit={fao.get('net_crop_water_deficit_7d_mm')} mm ({fao.get('gross_volume_m3_7d')} m3)."
            )
        if shc and shc.get("metrics"):
            sm = shc["metrics"]
            sr = (shc.get("classification") or {}).get("ratings") or {}
            parts.append(
                f"India Soil Health Card Lab Report ({shc.get('report_id', '')}): "
                f"pH={sm.get('ph')} ({sr.get('ph', '--')}), EC={sm.get('ec_ds_m')} dS/m, "
                f"OC={sm.get('organic_carbon_pct')}%, N={sm.get('nitrogen_kg_ha')} kg/ha ({sr.get('nitrogen_kg_ha', '--')}), "
                f"P={sm.get('phosphorus_kg_ha')} kg/ha ({sr.get('phosphorus_kg_ha', '--')}), "
                f"K={sm.get('potassium_kg_ha')} kg/ha ({sr.get('potassium_kg_ha', '--')})."
            )
        if mp and mp.get("plot_count"):
            crops_txt = ", ".join(
                f"{c.get('crop_name')} ({c.get('area_hectares')} ha / {c.get('area_share_pct')}%)"
                for c in (mp.get("crop_mix") or [])[:4]
            )
            parts.append(
                f"Multi-Plot Holding Cluster ({mp.get('plot_count')} plot(s), Root={mp.get('cluster_root_id')}): "
                f"Total={mp.get('total_area_hectares')} ha ({mp.get('total_area_acres')} ac), "
                f"Area-Weighted Cached NDVI={mp.get('area_weighted_cached_ndvi') if mp.get('area_weighted_cached_ndvi') is not None else 'Not yet queried'}, "
                f"Crops=[{crops_txt}]."
            )
        if cad and cad.get("resolved_admin"):
            radm = cad["resolved_admin"]
            port = cad.get("dilrmp_portal") or {}
            parts.append(
                f"DILRMP / Cadastral Advisory ({cad.get('status')}): Resolved State={radm.get('state')}, "
                f"District={radm.get('district')}, Unit Level={radm.get('subdivision_label') or 'District'}, "
                f"Official RoR Portal={port.get('ror_portal_url') or port.get('directory_url')}."
            )
        if advisories:
            parts.append("Verified Water & Stress Advisories: " + " | ".join(str(a) for a in advisories))
        parts.append("Legal ownership is not verified from user-drawn boundaries.")

        content = " ".join(parts)
        return {
            "document": {
                "id": "live_farm_agri_context",
                "title": f"Precision Agriculture Field Telemetry: {farm_name}",
                "category": "Precision Agriculture Live Context",
                "content": content,
                "source_provenance": "BHU LOKA Farm Polygon + Sentinel-2 L2A STAC + Open-Meteo ET0/Soil + Copernicus GLO-90 DEM",
            },
            "rrf_score": 1.0,
            "vector_score": 1.0,
            "bm25_score": 1.0,
            "rerank_score": 1.0,
        }

    def _build_earth_intelligence_context_entry(
        self,
        geo_context: Optional[dict] = None,
        historical_epoch: Optional[dict] = None,
        active_layers: Optional[list] = None,
    ) -> dict:
        parts = ["BHU LOKA Earth Intelligence Grounding Context:"]
        if geo_context:
            level = geo_context.get("level", "earth")
            name = geo_context.get("name", "Earth System")
            code = geo_context.get("code", "EARTH")
            stack = " > ".join(geo_context.get("stack", [name]))
            parts.append(f"Geographic Region: {name} (Hierarchy: {stack}, Level: {str(level).upper()}, Code: {code}).")
            if "current_lat" in geo_context and "current_lon" in geo_context:
                lat = float(geo_context["current_lat"])
                lon = float(geo_context["current_lon"])
                loc_name = geo_context.get("current_location_name", "Target")
                parts.append(f"Locked Target Location: {loc_name} ({lat:.4f}°N, {lon:.4f}°E).")
            if "active_mode" in geo_context:
                parts.append(f"Active 3D Viewport Scale: {str(geo_context['active_mode']).upper()}.")
            if "visible_satellites_count" in geo_context:
                parts.append(f"Tracked Orbital Assets: {geo_context['visible_satellites_count']} payloads in catalog.")
            if "active_hazard_hubs" in geo_context:
                parts.append(f"Active Multi-Hazard Monitoring Hubs: {geo_context['active_hazard_hubs']} sovereign nodes.")
            if "active_hazard_alerts" in geo_context and isinstance(geo_context["active_hazard_alerts"], list):
                alerts = []
                for a in geo_context["active_hazard_alerts"]:
                    if isinstance(a, dict):
                        alerts.append(f"{a.get('hazard', 'Hazard')} [{a.get('severity', 'ALERT')}]: {a.get('details', '')}")
                    elif isinstance(a, str):
                        alerts.append(a)
                if alerts:
                    parts.append(f"Active Multi-Hazard Viewport Alerts: {'; '.join(alerts)}.")
            if "active_layers_with_opacity" in geo_context and isinstance(geo_context["active_layers_with_opacity"], dict):
                layers_str = ", ".join(f"{k} (opacity {int(v*100)}%)" for k, v in geo_context["active_layers_with_opacity"].items())
                parts.append(f"Rendered Scientific Observation Overlays: {layers_str}.")
        if historical_epoch:
            year = historical_epoch.get("year", 2026)
            formatted = historical_epoch.get("formatted", "2026 CE")
            parts.append(f"Temporal Epoch: {formatted} (Year {year}). Satellite and hydromet observations correspond to this timeline.")
        if active_layers and not (geo_context and "active_layers_with_opacity" in geo_context):
            parts.append(f"Active Scientific Layers: {', '.join(str(layer) for layer in active_layers)}.")
        parts.append("Strict scientific provenance: Data grounded in verified orbital ephemeris, NWP grids, and SOI administrative vectors. Missing observations fail closed.")

        content = " ".join(parts)
        doc_title = f"Earth Intelligence Context: {geo_context.get('name', 'Earth') if geo_context else 'Active Region'}"
        return {
            "document": {
                "id": "earth_intel_active_context",
                "title": doc_title,
                "category": "Geospatial Earth Intelligence Live Context",
                "content": content,
                "source_provenance": "BHU LOKA Sovereign GIS + CelesTrak + Copernicus GLO-30 + Open-Meteo",
            },
            "rrf_score": 1.0,
            "vector_score": 1.0,
            "bm25_score": 1.0,
            "rerank_score": 1.0,
        }

    def run(
        self,
        query: str,
        top_k: int = 3,
        language_override: Optional[str] = None,
        agri_context: Optional[dict] = None,
        geo_context: Optional[dict] = None,
        historical_epoch: Optional[dict] = None,
        active_layers: Optional[list] = None,
    ):
        retrieved = self.retriever.retrieve(query, top_k=top_k)
        if agri_context:
            farm_entry = self._build_agri_context_entry(agri_context)
            retrieved = [farm_entry] + retrieved[: max(0, top_k - 1)]
        elif geo_context or historical_epoch or active_layers:
            geo_entry = self._build_earth_intelligence_context_entry(
                geo_context=geo_context,
                historical_epoch=historical_epoch,
                active_layers=active_layers,
            )
            retrieved = [geo_entry] + retrieved[: max(0, top_k - 1)]
        encoder_label = self.embedder.active_backend_label()
        PromptBuilder.build_rag_prompt(query, retrieved)
        norm_lang = language_override if language_override in {"en", "hi", "hinglish"} else None
        answer, lang = self.generator.generate(
            query,
            retrieved,
            encoder_label=encoder_label,
            language_override=norm_lang,
        )
        agent2_actions = plan_agent2_map_actions(query, retrieved)

        provenance_list = list(
            dict.fromkeys(
                r["document"].get("source_provenance", r["document"].get("category", "Verified Local Archive"))
                for r in retrieved
            )
        )

        return {
            "query": query,
            "language": lang,
            "encoder_backend": encoder_label,
            "reranker": "BhuLokaCrossReranker (Stage-2 Lexical + Dense + Entity)",
            "source_provenance": provenance_list,
            "answer": answer,
            "agent2_map_actions": agent2_actions,
            "retrieved_sources": [
                {
                    "id": r["document"].get("id"),
                    "title": r["document"]["title"],
                    "category": r["document"]["category"],
                    "content": r["document"].get("content", ""),
                    "source_provenance": r["document"].get("source_provenance", r["document"]["category"]),
                    "rrf_score": round(r["rrf_score"], 5),
                    "vector_score": r.get("vector_score", 0.0),
                    "bm25_score": r.get("bm25_score", 0.0),
                    "rerank_score": r.get("rerank_score", round(r["rrf_score"], 5)),
                }
                for r in retrieved
            ],
        }
