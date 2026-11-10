"""
BHU LOKA (भूलोक) - Sovereign Geospatial Model Context Protocol (MCP) Server
Provides 8 real MCP Tools & 2 Resources for AI coding agents and desktop assistants:
  - query_bhu_loka_rag            : Dual-Agent Transformer + BM25 + FAISS + Cross Re-Ranker QA
  - get_patna_ward_ulsi           : Calibrated DEM, Sentinel-1 SAR, NCRB/Q390 & ULSI metrics
  - get_india_sovereign_hubs      : All-India 36-State sovereign bounds (6.75N-37.10N) + 12 hubs
  - fetch_live_hydromet_and_flood : Live Open-Meteo Weather + GloFAS River Discharge (m3/s)
  - fetch_live_satellites         : Live NORAD CelesTrak GP active/Starlink/ISRO/EO/ISS telemetry
  - build_3d_location_hologram    : Live Open-Meteo Copernicus/SRTM 90m DEM 8x8 grid for any city
  - get_google_earth_gee_workflow : GEE (`Repos/earthengine-api`) SDK status + India gl=IN tiles + code
  - get_system_api_health         : Zero-key vs optional credential status diagnostics

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PIPELINES_DIR = Path(__file__).resolve().parent
if str(PIPELINES_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINES_DIR))

from mcp.server.fastmcp import FastMCP  # type: ignore

from bhu_loka_live_api import (
    fetch_live_hydromet,
    fetch_live_satellites as fetch_live_satellites_api,
    fetch_location_3d_dem,
    get_api_and_gee_status,
    get_india_hubs,
    get_patna_wards,
    load_bhu_loka_env,
    query_hybrid_rag,
    warmup_rag_pipeline,
)
from google_earth_engine_connector import BhuLokaGoogleEarthConnector


load_bhu_loka_env()


def create_mcp_server(host: str = "127.0.0.1", port: int = 8001) -> FastMCP:
    mcp = FastMCP(
        name="bhu-loka-geospatial",
        instructions=(
            "BHU LOKA (भूलोक) Sovereign Geospatial Decision Support Server built at IIT Patna "
            "by Prince Kumar (PA2511CDH37) under Pallav Rustogi. Strictly NEVER refer to this project "
            "as PRITHVI. Use these tools for calibrated Patna ULSI/SAR/DEM audits, complete "
            "6.75N-37.10N 36-State India hazard hubs, live Open-Meteo weather & GloFAS river flood "
            "discharge, and Repos/earthengine-api Google Earth workflows."
        ),
        host=host,
        port=port,
        log_level="ERROR",
    )

    @mcp.tool()
    def query_bhu_loka_rag(query: str, top_k: int = 3) -> Dict[str, Any]:
        """Query BHU LOKA's local Hybrid BM25 + FAISS RRF RAG knowledge engine."""
        if not query or not query.strip():
            return {"error": "Query cannot be empty."}
        bounded_k = max(1, min(10, int(top_k)))
        return query_hybrid_rag(query.strip(), top_k=bounded_k)

    @mcp.tool()
    def get_patna_ward_ulsi(ward_name: str = "") -> Dict[str, Any]:
        """Get calibrated Copernicus 30m DEM, Sentinel-1 SAR inundation, NCRB/Q390 safety, and ULSI score for Patna wards."""
        return get_patna_wards(ward_filter=ward_name)

    @mcp.tool()
    def get_india_sovereign_hubs(state_filter: str = "") -> Dict[str, Any]:
        """Get All-India 36-State sovereign extent (6.75N-37.10N including Ladakh, J&K, Arunachal) and 12 hazard hubs."""
        return get_india_hubs(state_filter=state_filter)

    @mcp.tool()
    def fetch_live_hydromet_and_flood(
        location_name: str = "Patna",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Fetch real live Open-Meteo weather, soil moisture, and GloFAS river flood discharge (m3/s) with zero API keys."""
        return fetch_live_hydromet(location=location_name, lat=lat, lon=lon)

    @mcp.tool()
    def get_google_earth_gee_workflow(
        bbox_west: float = 84.95,
        bbox_south: float = 25.52,
        bbox_east: float = 85.28,
        bbox_north: float = 25.66,
        start_date: str = "2019-09-20",
        end_date: str = "2019-10-05",
    ) -> Dict[str, Any]:
        """Inspect Google Earth Engine SDK (`Repos/earthengine-api`) status, India gl=IN tiles, and return a reproducible ee workflow."""
        conn = BhuLokaGoogleEarthConnector()
        init_res = conn.initialize()
        return {
            "sdk_summary": conn.summary(),
            "initialize_check": init_res,
            "tile_endpoints": conn.get_tile_endpoints(),
            "ee_python_workflow": conn.generate_gee_patna_workflow(
                bbox=[bbox_west, bbox_south, bbox_east, bbox_north],
                start_date=start_date,
                end_date=end_date,
            ),
        }

    @mcp.tool()
    def get_system_api_health() -> Dict[str, Any]:
        """Audit connected zero-key engines vs optional API credentials in the active environment."""
        return get_api_and_gee_status()

    @mcp.tool()
    def fetch_live_satellites(constellation: str = "all") -> Dict[str, Any]:
        """Fetch real active NORAD CelesTrak satellites (Starlink, ISS, ISRO, Sentinel/MODIS EO, Weather) with live positions."""
        return fetch_live_satellites_api(constellation=constellation)

    @mcp.tool()
    def build_3d_location_hologram(
        location_name: str = "Bihta",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        span_deg: float = 0.08,
    ) -> Dict[str, Any]:
        """Dynamically fetch a Copernicus/SRTM 90m DEM elevation grid via Open-Meteo for Agent-2 3D terrain hologram synthesis."""
        return fetch_location_3d_dem(location_name=location_name, lat=lat, lon=lon, span_deg=span_deg)

    @mcp.resource("bhu-loka://sovereign/metadata")
    def sovereign_metadata() -> str:
        """Read-only BHU LOKA identity, sovereign extent, and API configuration manifest."""
        payload = {
            "status": get_api_and_gee_status(),
            "hubs": get_india_hubs(),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @mcp.resource("bhu-loka://wards/patna")
    def patna_wards_resource() -> str:
        """Read-only Patna multi-hazard ward audit matrix (DEM + S1 SAR + NCRB + ULSI)."""
        return json.dumps(get_patna_wards(), indent=2, ensure_ascii=False)

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="BHU LOKA Sovereign Geospatial MCP Server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    # Pre-warm Hybrid RAG & numpy/faiss on the main thread before stdio threads start
    warmup_rag_pipeline()
    mcp_server = create_mcp_server(host=args.host, port=args.port)
    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()
