"""
FastAPI Entry Point for BHU LOKA Enterprise Hybrid RAG & Live Geospatial API
Connects:
- Hybrid BM25 + FAISS RRF RAG Pipeline
- Live Zero-Key Open-Meteo Weather + GloFAS River Flood Discharge Proxy
- Verified Sovereign India 36-State Hubs & Patna Ward ULSI Audits
- Google Earth Engine SDK + API Credential Diagnostics

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

import os
import sys
import time
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Optional, Tuple
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

# Ensure path resolution
APP_DIR = Path(__file__).resolve().parent
PIPELINES_DIR = APP_DIR.parent.parent.parent / "Pipelines"
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
from bhu_loka_guardrails import BhuLokaGuardrails
from bhu_loka_eval_harness import RagasEvaluator
from bhu_loka_llmops import BhuLokaLLMOps

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return get_health_status(len(pipeline.documents))


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
    res = pipeline.run(req.query, top_k=req.top_k, language_override=req.language)
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


if __name__ == "__main__":
    print("=================================================================")
    print(" BHU LOKA DUAL-AGENT HYBRID RAG + LIVE ORBITAL & DEM API v3.0")
    print("=================================================================")
    print("Endpoints:")
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
