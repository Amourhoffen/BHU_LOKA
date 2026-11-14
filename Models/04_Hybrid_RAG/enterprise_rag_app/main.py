"""
FastAPI Entry Point for BHU LOKA Enterprise Hybrid RAG & Live Geospatial API
Connects:
- Hybrid BM25 + FAISS RRF RAG Pipeline
- Live Zero-Key Open-Meteo Weather + GloFAS River Flood Discharge Proxy
- Verified Sovereign India 36-State Hubs & Patna Ward ULSI Audits
- Google Earth Engine SDK + API Credential Diagnostics

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

import json
import os
import sys
import threading
import time
import urllib.request
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure path resolution
APP_DIR = Path(__file__).resolve().parent
BHU_LOKA_ROOT = APP_DIR.parent.parent.parent
PIPELINES_DIR = BHU_LOKA_ROOT / "Pipelines"
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))
if str(PIPELINES_DIR) not in sys.path:
    sys.path.append(str(PIPELINES_DIR))

from config.settings import settings
from rag.pipeline import RAGPipeline
from api.health import get_health_status, HealthResponse
from api.rag import QueryRequest, QueryResponse
from bhu_loka_live_api import (
    fetch_live_hydromet,
    fetch_live_satellites,
    fetch_location_3d_dem,
    get_api_and_gee_status,
    get_india_hubs,
    get_patna_wards,
    load_bhu_loka_env,
    start_background_live_warmup,
)
from bhu_loka_location_engine import fetch_universal_location_intelligence
from bhu_loka_site_studio import export_site_package, run_site_analysis
from bhu_loka_agri_engine import router as agri_router
from bhu_loka_india_intel import (
    get_admin_children,
    get_gis_layer,
    get_india_states,
    get_land_record_portals,
    get_layers_catalog,
    get_villages_wards,
    refresh_official_news_feeds,
    resolve_admin_context,
    search_admin_locations,
    search_land_parcel,
)
from bhu_loka_guardrails import BhuLokaGuardrails
from bhu_loka_eval_harness import RagasEvaluator
from bhu_loka_llmops import BhuLokaLLMOps
from bhu_loka_worker_health import worker_router
from bhu_loka_urban_business import urban_router

load_bhu_loka_env()

# Initialize RAG Pipeline at startup (uses instant SVD + precomputed 384-d MiniLM .npz cache)
pipeline = RAGPipeline()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Non-blocking background Transformer model + CelesTrak/DEM cache warmup once FastAPI starts
    pipeline.start_background_transformer_warmup()
    start_background_live_warmup()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Dual-Agent Enterprise Hybrid RAG, Live Orbital Satellite & Copernicus DEM API for BHU LOKA",
    lifespan=lifespan,
)
app.include_router(agri_router)
app.include_router(worker_router)
app.include_router(urban_router)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$",
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Bhu-Loka-Attribution", "X-Bhu-Role"],
)

_ALLOWED_ROLES = {"viewer", "analyst", "admin"}
_VIEWER_BLOCKED_POST_PREFIXES = ("/api/v1/india/news/refresh", "/api/v1/agri/")
_AUDIT_LOCK = threading.Lock()
_SECURITY_AUDIT_LOG: Deque[Dict[str, Any]] = deque(maxlen=250)
_AUDIT_JSONL_PATH = BHU_LOKA_ROOT / "Data" / "08_Processed_Outputs" / "api_audit.jsonl"


def _record_audit_event(entry: Dict[str, Any]) -> None:
    with _AUDIT_LOCK:
        _SECURITY_AUDIT_LOG.append(entry)
    try:
        _AUDIT_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_JSONL_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


@app.middleware("http")
async def bhu_loka_security_and_audit_middleware(request: Request, call_next):
    t_start = time.perf_counter()
    raw_role = str(request.headers.get("X-Bhu-Role") or "analyst").strip().lower()
    role = raw_role if raw_role in _ALLOWED_ROLES else "viewer"
    path = request.url.path
    method = request.method.upper()

    if role == "viewer" and method in ("POST", "PUT", "PATCH", "DELETE"):
        if any(path.startswith(pfx) for pfx in _VIEWER_BLOCKED_POST_PREFIXES):
            resp = JSONResponse(
                status_code=403,
                content={
                    "detail": "Read-only role 'viewer' is not permitted to trigger write/refresh mutations. Use X-Bhu-Role: analyst or admin.",
                    "role": role,
                    "path": path,
                },
            )
            resp.headers["X-Content-Type-Options"] = "nosniff"
            resp.headers["X-Frame-Options"] = "SAMEORIGIN"
            resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            _record_audit_event(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "method": method,
                    "path": path,
                    "role": role,
                    "status_code": 403,
                    "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                }
            )
            return resp

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
    if path.startswith("/api/"):
        _record_audit_event(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "path": path,
                "role": role,
                "status_code": getattr(response, "status_code", 200),
                "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
            }
        )
    return response


@app.get("/health", response_model=HealthResponse)
async def health():
    return get_health_status(len(pipeline.documents))


@app.get("/api/v1/system/security-audit")
def system_security_audit():
    """Return Phase-1 security controls, RBAC matrix, and recent non-secret API audit log."""
    with _AUDIT_LOCK:
        recent = list(_SECURITY_AUDIT_LOG)[-25:]
        total = len(_SECURITY_AUDIT_LOG)
    return {
        "status": "ACTIVE",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "security_headers": [
            "X-Content-Type-Options: nosniff",
            "X-Frame-Options: SAMEORIGIN",
            "Referrer-Policy: strict-origin-when-cross-origin",
            "Permissions-Policy: camera=(), microphone=(), geolocation=(self)",
        ],
        "rbac_roles": {
            "viewer": "Read-only GIS/EO access + RAG queries; write/refresh mutations blocked (403).",
            "analyst": "Default scientific workstation role: GIS queries, RAG evaluation, news refresh, exports.",
            "admin": "Full audit diagnostics & governance configuration.",
        },
        "ai_guardrails": {
            "input_prompt_injection_filter": "BhuLokaGuardrails.evaluate_input ACTIVE",
            "output_grounding_verifier": "BhuLokaGuardrails.evaluate_output + RagasEvaluator ACTIVE",
        },
        "audit_buffer_count": total,
        "recent_events": recent,
    }


@app.get("/api/v1/sources/provenance")
def sources_provenance_registry():
    """Authoritative data-source registry distinguishing EO imagery, orbital ephemeris, weather, hydrology, CCTV, and alerts."""
    return {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cloud_infrastructure_exclusion": "Cloud hosting (e.g., AWS/GCP infrastructure) is never represented as Earth observation satellite telemetry.",
        "categories": [
            {
                "domain": "Earth Observation & Satellite Imagery",
                "sources": [
                    {"name": "NASA EOSDIS GIBS (MODIS Terra)", "products": "TrueColor, NDVI 8-Day, MOD11A1 Daytime LST", "status": "CATALOG_AND_TILES", "limitation": "Composite tiles; not raw Level-1B radiance."},
                    {"name": "Google Earth High-Res (gl=IN)", "products": "Hybrid / Optical Terrain Tiles (0.5m)", "status": "LIVE_TILES", "limitation": "Multi-temporal optical composite; cloud/revisit dependent."},
                    {"name": "Copernicus Sentinel-1 / Sentinel-2 & ISRO Bhoonidhi Ref", "products": "10m SAR Flood Calibration & MSI Reference", "status": "REFERENCE_AND_PATNA_SAR", "limitation": "Live programmatic L2A downloads require Earthdata / Bhoonidhi credentials."},
                ],
            },
            {
                "domain": "Orbital Tracking (Ephemeris Only)",
                "sources": [
                    {"name": "CelesTrak NORAD GP/TLE Catalog", "products": "ISS/CSS, ISRO, NASA/ESA EO, NOAA Weather, Starlink orbital propagation", "status": "LIVE_OR_CACHED", "limitation": "Keplerian orbital ephemeris only; NOT live onboard spacecraft or payload telemetry."},
                    {"name": "WhereTheISS / Open-Notify", "products": "ISS ZARYA (25544) lat/lon/alt tracker", "status": "LIVE", "limitation": "Public position feed only."},
                ],
            },
            {
                "domain": "Weather, Climate, Hydrology & Air Quality",
                "sources": [
                    {"name": "Open-Meteo DWD ICON / ECMWF HRES", "products": "Temperature, RH, Wind, Precipitation, Soil Moisture 0-7cm", "status": "LIVE_OR_UNAVAILABLE", "limitation": "1-11 km NWP grid interpolation; offline fails closed."},
                    {"name": "Copernicus GloFAS v4", "products": "River Discharge & Flood Awareness", "status": "LIVE_OR_UNAVAILABLE", "limitation": "0.05 deg hydrological model."},
                    {"name": "Copernicus CAMS & CPCB NAQI", "products": "PM2.5, PM10, US AQI", "status": "LIVE_OR_UNAVAILABLE", "limitation": "11 km atmospheric grid."},
                ],
            },
            {
                "domain": "Public Infra, Alerts & Authorized CCTV",
                "sources": [
                    {"name": "OpenStreetMap Overpass (ODbL)", "products": "Roads, Closures, Traffic Controls, Hospitals", "status": "LIVE_CACHED_OR_UNAVAILABLE", "limitation": "Community/mapped vector completeness varies; zero fabricated nodes."},
                    {"name": "State Police & Smart City Municipal Portals", "products": "Authorized Public Camera Nodes", "status": "VERIFIED_PUBLIC_REGISTRY", "limitation": "Public status/portal links only; private feeds excluded."},
                    {"name": "PIB India & NDMA Sachet", "products": "Official Government News & CAP Emergency Alerts", "status": "LIVE_RSS_OR_EMPTY", "limitation": "Only verified official RSS/CAP entries displayed."},
                ],
            },
        ],
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    t0 = time.perf_counter()

    # 1. Input Guardrail Inspection
    in_guard = BhuLokaGuardrails.evaluate_input(req.query)
    if not in_guard.passed and in_guard.risk_level == "CRITICAL":
        latency = round((time.perf_counter() - t0) * 1000.0, 2)
        refusal_msg = (
            f"[BHU LOKA SECURITY GUARDRAIL TRIGGERED: {in_guard.violation_type}]\n"
            f"Adversarial request blocked: {in_guard.details}\n"
            "BHU LOKA strictly enforces sovereign scientific integrity and rejects jailbreak attempts."
        )
        BhuLokaLLMOps.log_evaluation_trace(
            query=req.query,
            answer=refusal_msg,
            retrieved_sources=[],
            faithfulness=1.0,
            answer_relevance=1.0,
            context_precision=1.0,
            guardrail_passed=False,
            latency_ms=latency,
            user_language="en",
            encoder_backend="GuardrailEnforcer"
        )
        return {
            "query": req.query,
            "answer": refusal_msg,
            "retrieved_sources": [],
            "language": "en",
            "encoder_backend": "GuardrailEnforcer",
            "latency_ms": latency,
            "eval_metrics": {
                "faithfulness": 1.0,
                "answer_relevance": 1.0,
                "context_precision": 1.0,
                "llm_judge_verdict": "ADVERSARIAL_BLOCKED"
            },
            "guardrails": {
                "passed": False,
                "violation": in_guard.violation_type,
                "risk_level": in_guard.risk_level
            }
        }

    # 2. Dual-Agent RAG Synthesis
    res = pipeline.run(
        req.query,
        top_k=req.top_k,
        language_override=req.language,
        agri_context=req.agri_context,
        geo_context=req.geo_context,
        historical_epoch=req.historical_epoch,
        active_layers=req.active_layers,
    )
    latency = round((time.perf_counter() - t0) * 1000.0, 2)
    res["latency_ms"] = latency

    # 3. Ragas Metrics & LLM-as-a-Judge Evaluation
    retrieved_docs = res.get("retrieved_sources", [])
    eval_res = RagasEvaluator.compute_all_metrics(
        query=req.query,
        answer=res["answer"],
        retrieved_docs=retrieved_docs
    )

    # 4. Output Guardrail (Context Grounding vs AI Agent Hallucination check)
    out_guard = BhuLokaGuardrails.evaluate_output(
        query=req.query,
        answer=res["answer"],
        retrieved_docs=retrieved_docs
    )

    res["eval_metrics"] = {
        "faithfulness": eval_res.faithfulness,
        "answer_relevance": eval_res.answer_relevance,
        "context_precision": eval_res.context_precision,
        "context_recall": eval_res.context_recall,
        "context_groundedness_pct": eval_res.context_groundedness_pct,
        "agent_self_ratio_pct": eval_res.agent_self_ratio_pct,
        "llm_judge_verdict": eval_res.llm_judge_verdict,
        "llm_judge_reasoning": eval_res.llm_judge_reasoning,
        "grounded_claims_count": len(eval_res.grounded_claims),
        "ungrounded_claims_count": len(eval_res.ungrounded_claims)
    }

    res["guardrails"] = {
        "passed": out_guard.passed,
        "decision": out_guard.decision,
        "context_groundedness_pct": out_guard.context_groundedness_pct,
        "agent_self_ratio_pct": out_guard.agent_self_ratio_pct
    }

    # 5. LLMOps & LangSmith Logging
    BhuLokaLLMOps.log_evaluation_trace(
        query=req.query,
        answer=res["answer"],
        retrieved_sources=retrieved_docs,
        faithfulness=eval_res.faithfulness,
        answer_relevance=eval_res.answer_relevance,
        context_precision=eval_res.context_precision,
        guardrail_passed=out_guard.passed,
        latency_ms=latency,
        user_language=res.get("language", "en"),
        encoder_backend=res.get("encoder_backend", "MiniLM-384d")
    )

    res["grounding_payload"] = req.geo_context
    return res


@app.get("/api/v1/eval/metrics")
def eval_metrics():
    """
    Cumulative LLMOps evaluation telemetry and RAGAS metrics across all queries.
    """
    return BhuLokaLLMOps.get_cumulative_metrics()


@app.get("/api/v1/documents")
def list_documents():
    return [
        {
            "id": d["id"],
            "title": d["title"],
            "category": d["category"],
        }
        for d in pipeline.documents
    ]


@app.get("/api/v1/wards")
def list_wards(q: str = Query(default="", description="Optional locality filter")):
    return get_patna_wards(ward_filter=q)


@app.get("/api/v1/hubs")
def list_india_hubs(state: str = Query(default="", description="Optional state/UT filter")):
    return get_india_hubs(state_filter=state)


@app.get("/api/v1/live-telemetry")
def live_telemetry(
    location: str = Query(default="Patna", description="City or hub preset name"),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
):
    return fetch_live_hydromet(location=location, lat=lat, lon=lon)


@app.get("/api/v1/gee-status")
def gee_and_api_status():
    return get_api_and_gee_status()


@app.get("/api/v1/satellites")
def live_satellites(
    constellation: str = Query(default="all", description="Filter: all | starlink | eo | weather | isro | station"),
):
    return fetch_live_satellites(constellation=constellation)


@app.get("/api/v1/dem-hologram")
def location_3d_dem(
    location: str = Query(default="Bihta", description="Any city, ward, address, Bihar district, or heritage site"),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
    span_deg: float = Query(default=0.08, ge=0.02, le=0.4),
    grid_n: int = Query(default=8, ge=4, le=10),
):
    return fetch_location_3d_dem(location_name=location, lat=lat, lon=lon, span_deg=span_deg, grid_n=grid_n)


@app.get("/api/v1/location-intelligence")
def universal_location_intelligence(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (EPSG:4326)"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (EPSG:4326)"),
    place_name: Optional[str] = Query(default=None, description="Optional place or locality name"),
    radius_km: float = Query(default=10.0, ge=1.0, le=100.0, description="Analysis radius in km"),
):
    """
    BHU LOKA Universal Location Intelligence:
    Returns complete 15-module multi-hazard, hydrology, weather, terrain, and satellite intelligence
    for ANY clicked or queried coordinates in India with full data provenance.
    """
    try:
        return fetch_universal_location_intelligence(lat=lat, lon=lon, place_name=place_name, radius_km=radius_km)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/site-analysis")
def site_studio_analysis(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (EPSG:4326)"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (EPSG:4326)"),
    place_name: Optional[str] = Query(default=None),
    radius_m: float = Query(default=350.0, ge=100.0, le=1000.0, description="Site analysis ring radius in meters"),
    date_iso: Optional[str] = Query(default=None, description="Optional YYYY-MM-DD date for solar curve"),
    building_height_m: float = Query(default=10.0, ge=2.0, le=300.0, description="Reference height (m) for shadow lengths"),
    include_osm: bool = Query(default=True),
    include_utci: bool = Query(default=True),
    include_dem: bool = Query(default=True),
    span_deg: float = Query(default=0.04, ge=0.02, le=0.25),
):
    """
    BHU LOKA Site Studio v3.2:
    Returns UTM projection, deterministic NOAA solar/shadow/solstice curves, Bröde UTCI thermal comfort
    + Open-Meteo wind rose, live OSM Overpass site ring, and Marching-Squares DEM contours & transects.
    """
    try:
        return run_site_analysis(
            lat=lat,
            lon=lon,
            place_name=place_name,
            radius_m=radius_m,
            date_iso=date_iso,
            building_height_m=building_height_m,
            include_osm=include_osm,
            include_utci=include_utci,
            include_dem=include_dem,
            span_deg=span_deg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/export-site")
def export_site_bundle(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    format: str = Query(default="geojson", description="geojson | dxf | svg | profile_svg | glb | obj"),
    place_name: Optional[str] = Query(default=None),
    radius_m: float = Query(default=350.0, ge=100.0, le=1000.0),
    span_deg: float = Query(default=0.04, ge=0.02, le=0.25),
):
    """Stream true-scale metric DXF, layered SVG, elevation transect SVG, glTF 2.0 GLB, OBJ, or GeoJSON."""
    try:
        pkg = export_site_package(
            lat=lat,
            lon=lon,
            fmt=format,
            place_name=place_name,
            radius_m=radius_m,
            span_deg=span_deg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=pkg["bytes"],
        media_type=pkg["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{pkg["filename"]}"',
            "X-Bhu-Loka-Attribution": "OpenStreetMap ODbL | Copernicus GLO-90 DEM | NOAA Solar | Brode UTCI",
        },
    )


class LandParcelSearchRequest(BaseModel):
    state_or_code: str = Field(..., min_length=1, description="Indian State/UT name or 2-digit Census/LGD code")
    district: Optional[str] = None
    subdivision: Optional[str] = None
    circle: Optional[str] = None
    block: Optional[str] = None
    village_mauza: Optional[str] = None
    khata_no: Optional[str] = None
    khesra_no: Optional[str] = None
    plot_no: Optional[str] = None
    ulpin: Optional[str] = None
    check_portal: bool = False


@app.get("/api/v1/india/states")
def india_states_list():
    """Return all 28 Indian States and 8 Union Territories (36) with state-specific hierarchy schemas."""
    return get_india_states()


@app.get("/api/v1/india/admin/children")
def india_admin_children(
    parent_id: Optional[str] = Query(default=None),
    state_code: Optional[str] = Query(default=None),
    level_depth: Optional[int] = Query(default=None, ge=0, le=7),
):
    """Return verified child administrative units under a parent unit or state_code."""
    return get_admin_children(parent_id=parent_id, state_code=state_code, level_depth=level_depth)


@app.get("/api/v1/india/admin/search")
def india_admin_search(
    q: str = Query(..., min_length=1, description="English, alternate, or local-language query"),
    limit: int = Query(default=25, ge=1, le=100),
):
    """Search States/UTs, Districts, Subdivisions/Tehsils/Anchals, Capitals, Rural Villages, and Remote Sectors."""
    return search_admin_locations(q=q, limit=limit)


@app.get("/api/v1/india/admin/resolve")
def india_admin_resolve(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
):
    """Resolve authoritative Indian State/UT, District, Level-3 Subdivision, and breadcrumb for coordinates."""
    try:
        return resolve_admin_context(lat=lat, lon=lon)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/india/admin/villages-wards")
def india_villages_wards(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(default=10.0, ge=1.0, le=50.0),
    refresh_live: bool = Query(default=False),
):
    """Return rural villages, Gram Panchayats, and ULB wards inside radius."""
    try:
        return get_villages_wards(lat=lat, lon=lon, radius_km=radius_km, refresh_live=refresh_live)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/india/land-records/portals")
def india_land_portals(state: Optional[str] = Query(default=None)):
    """Return DILRMP state-wise official land record portal directory (or single State/UT entry)."""
    try:
        return get_land_record_portals(state_or_code=state)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/india/land-records/search")
def india_land_parcel_search(req: LandParcelSearchRequest):
    """Composite-scoped Land Parcel & Plot search (Bihar Pilot + 36-State DILRMP Handoff)."""
    try:
        return search_land_parcel(req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/india/layers/catalog")
def india_layers_catalog():
    """Return documented 10-point GIS layer catalog across Administrative, Police, CCTV, News, Traffic & Emergency."""
    return get_layers_catalog()


@app.get("/api/v1/india/layers/{layer_id}")
def india_gis_layer(
    layer_id: str,
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(default=10.0, ge=1.0, le=100.0),
    refresh_live: bool = Query(default=False),
    category: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
):
    """Fetch GeoJSON FeatureCollection and 10-point GIS layer metadata filtered to LocationContext."""
    try:
        return get_gis_layer(
            layer_id=layer_id,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            refresh_live=refresh_live,
            category=category,
            language=language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/india/news/refresh")
def india_news_refresh():
    """Refresh official PIB EN/HI RSS and NDMA Sachet CAP alerts into SQLite store."""
    return refresh_official_news_feeds()


_SAT_TILE_CACHE: Dict[str, Tuple[bytes, str]] = {}


@app.get("/api/v1/sat-tile/{z}/{x}/{y}")
def proxy_satellite_tile(
    z: int,
    x: int,
    y: int,
    layer: str = Query(default="hybrid", description="hybrid | sat | maps | terrain"),
):
    """CORS-safe satellite & Google Earth India (gl=IN) tile proxy for Three.js WebGL terrain draping."""
    if not (0 <= z <= 20):
        raise HTTPException(status_code=400, detail="Zoom out of range")
    cache_key = f"{layer}:{z}:{x}:{y}"
    cached = _SAT_TILE_CACHE.get(cache_key)
    if cached:
        return Response(
            content=cached[0],
            media_type=cached[1],
            headers={"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"},
        )

    lyrs_code = {"hybrid": "y", "sat": "s", "maps": "m", "terrain": "p"}.get(layer, "y")
    srv = (x + y) % 4
    urls = [
        f"https://mt{srv}.google.com/vt/lyrs={lyrs_code}&gl=IN&x={x}&y={y}&z={z}",
        f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    ]
    for u in urls:
        try:
            req = urllib.request.Request(
                u,
                headers={"User-Agent": "Mozilla/5.0 (BHU-LOKA Geospatial Workbench/3.0)"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
                if len(data) > 100:
                    if len(_SAT_TILE_CACHE) >= 400:
                        _SAT_TILE_CACHE.pop(next(iter(_SAT_TILE_CACHE)))
                    _SAT_TILE_CACHE[cache_key] = (data, ctype)
                    return Response(
                        content=data,
                        media_type=ctype,
                        headers={"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"},
                    )
        except Exception:
            continue
    raise HTTPException(status_code=502, detail="Satellite tile unavailable")


def _serve_dashboard_html(filename: str) -> FileResponse:
    target = BHU_LOKA_ROOT / filename
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f"Dashboard file not found: {filename}")
    return FileResponse(path=str(target), media_type="text/html; charset=utf-8")


@app.get("/", include_in_schema=False)
def serve_root_dashboard():
    """Serve the primary BHU LOKA 3D Sovereign Geospatial Workstation."""
    return _serve_dashboard_html("bhu_loka_cyber_dashboard.html")


@app.get("/bhu_loka_cyber_dashboard.html", include_in_schema=False)
def serve_3d_dashboard():
    return _serve_dashboard_html("bhu_loka_cyber_dashboard.html")


@app.get("/bhu_loka_leafmap_interactive.html", include_in_schema=False)
def serve_2d_explorer():
    return _serve_dashboard_html("bhu_loka_leafmap_interactive.html")


_ASSETS_DIR = BHU_LOKA_ROOT / "Assets"
if _ASSETS_DIR.is_dir():
    app.mount("/Assets", StaticFiles(directory=str(_ASSETS_DIR)), name="bhu_loka_assets")

_PROCESSED_OUTPUTS_DIR = BHU_LOKA_ROOT / "Data" / "08_Processed_Outputs"
if _PROCESSED_OUTPUTS_DIR.is_dir():
    app.mount(
        "/Data/08_Processed_Outputs",
        StaticFiles(directory=str(_PROCESSED_OUTPUTS_DIR)),
        name="bhu_loka_processed_outputs",
    )


if __name__ == "__main__":
    print("=================================================================")
    print(" BHU LOKA DUAL-AGENT HYBRID RAG + LIVE ORBITAL & DEM API v3.0")
    print("=================================================================")
    print("Dashboards & Endpoints:")
    print("  GET  http://127.0.0.1:8000/  (3D Sovereign Workstation)")
    print("  GET  http://127.0.0.1:8000/bhu_loka_leafmap_interactive.html  (2D GIS Explorer)")
    print("  GET  http://127.0.0.1:8000/health")
    print("  POST http://127.0.0.1:8000/api/v1/query")
    print("  GET  http://127.0.0.1:8000/api/v1/wards")
    print("  GET  http://127.0.0.1:8000/api/v1/hubs")
    print("  GET  http://127.0.0.1:8000/api/v1/live-telemetry?location=Patna")
    print("  GET  http://127.0.0.1:8000/api/v1/satellites")
    print("  GET  http://127.0.0.1:8000/api/v1/dem-hologram?location=Ayodhya")
    print("  GET  http://127.0.0.1:8000/api/v1/gee-status")
    print("=================================================================")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
