# BHU LOKA (भूलोक) — High-Level Architecture Design (HLD, R0 / R0.1)

**Document ID:** `BHU-HLD-R0`  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope:** Software-Only Scientific Geospatial Platform  

---

## 1. System Topology

```mermaid
flowchart TD
    subgraph ClientTier ["Presentation Tier (Software-Only 2D / 3D / Desktop)"]
        D3["bhu_loka_cyber_dashboard.html (Three.js r128)"]
        D2["bhu_loka_leafmap_interactive.html (Leaflet 1.9.4 + NASA GIBS WMTS)"]
        EL["BhuLoka_Chromium_App/main.js (Electron 33 Shell)"]
        JS1["bhu_loka_location_engine.js (LocationContext + Site Studio)"]
        JS2["bhu_loka_india_intel.js (Modules A-F + 12 GIS Layers)"]
        JS3["bhu_loka_agri.js (Precision Agriculture + NASA EO Panel)"]
        IDX["bhu_loka_india_admin_index.js (Offline 36-State Index)"]
        D3 --> JS1
        D2 --> JS1
        D3 --> JS2
        D2 --> JS2
        D2 --> JS3
        JS2 --> IDX
        EL --> D3
    end

    subgraph ApiTier ["Application & AI Tier (Python 3.13.7)"]
        FA["FastAPI Server (main.py - 39 ASGI / 35 Custom HTTP Routes)"]
        MCP["FastMCP Server (bhu_loka_mcp_server.py - 11 Tools)"]
        RAG["Enterprise Hybrid RAG (BM25 + FAISS RRF + RAGAS Guardrails)"]
        LOC["bhu_loka_location_engine.py (15-Module Telemetry Engine)"]
        IND["bhu_loka_india_intel.py (Admin, RoR, 12 GIS Layers, RSS)"]
        STU["bhu_loka_site_studio.py (Solar/UTCI + CAD/3D Export)"]
        AGR["bhu_loka_agri_engine.py (Farms, NASA CMR/POWER, S2 STAC)"]
        FA --> RAG
        FA --> LOC
        FA --> IND
        FA --> STU
        FA --> AGR
        MCP --> RAG
        MCP --> LOC
        MCP --> STU
        AGR --> RAG
    end

    subgraph DataTier ["Local Storage & External Open EO APIs"]
        SQL[("bhu_loka_india_intel.sqlite (Admin, Parcels, Farms, Cache)")]
        EO[("Empirical Experiments & Rasters (MOD11A1.061, S1 SAR, GLO-30, WorldPop)")]
        EXT["Open APIs (NASA CMR, NASA GIBS, NASA POWER, USGS Landsat / S2 STAC, Open-Meteo, Overpass, RSS)"]
        IND --> SQL
        AGR --> SQL
        AGR --> EXT
        LOC --> EXT
        RAG --> EO
    end

    JS1 -->|HTTP JSON 127.0.0.1:8000| FA
    JS2 -->|HTTP JSON 127.0.0.1:8000| FA
    JS3 -->|HTTP JSON 127.0.0.1:8000| FA
```

---

## 2. Software-Only Runtime Boundaries

- **Web & API Execution:** `uvicorn main:app` serves `35` custom HTTP routes on `127.0.0.1:8000` (all R0 routes plus `/api/v1/agri/*`).
- **Desktop & MCP Execution:** `BhuLoka_Chromium_App/main.js` wraps the 3D HUD; `bhu_loka_mcp_server.py` exposes `11` FastMCP tools.
- **No Hardware/IoT Tier:** Physical IoT sensors, wearables, and hardware firmware are explicitly out of current scope.
