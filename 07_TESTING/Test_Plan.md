# BHU LOKA (भूलोक) — Master Test Plan (R0 / R0.1)

**Document ID:** `BHU-TP-R0`  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  

---

## 1. Verification Strategy and Runtime Constraints

On Windows sandboxed shells, Python's `ProactorEventLoop._make_self_pipe()` calls loopback `socketpair`, causing `asyncio.run(...)` inside ASGI/MCP tests to block unless executed outside sandbox socket restrictions. Therefore, BHU LOKA divides automated verification into:

1. **Full Pytest Suite (`43` tests across 4 files):** Covers Spatial DB setup, India Admin Explorer, Land Scoping, 12 GIS layers + 429 retry, News RSS, Site Studio CAD/3D exports, Hybrid RAG + RAGAS guardrails, UTM farm polygon math, NASA CMR (`MOD13Q1`, `MOD11A2`, `HLSL30`), USGS Landsat C2 L2, NASA LaRC POWER, Sentinel-2 L2A STAC, and FastAPI ASGI / FastMCP endpoints.
2. **Live Daemon HTTP & Live NASA API Probing:** Real `uvicorn` + `http.server` smoke requests against core endpoints + `/api/v1/agri/*` and zero-key NASA CMR/GIBS/POWER probes.
3. **JavaScript Syntax, CDP Layout & Runtime Rendering:** `node --check` on all `.js` bundles + inline `<script>` blocks, plus Chrome DevTools Protocol (CDP) layout checks (`1422x748`, `1200x760`, Theater Mode, Browser Fullscreen + `ESC` restore, `390x844` mobile drawers, zero document vertical overflow / zero WebGL canvas stretch, zero console errors).
4. **Scientific Integrity Audit:** Strict scan via `.agents/skills/scientific-integrity-guard/scripts/check_integrity.py --strict` ensuring zero `S0`/`S1`/`S2` findings.

---

## 2. Test Suites & Entry Commands

| Suite File | Count | Scope | Execution Requirement |
| :--- | :---: | :--- | :--- |
| `Models/04_Hybrid_RAG/enterprise_rag_app/tests/test_india_location_street_intel.py` | 10 | 36 States/UTs, Patna GADM L3=3, Ladakh `38`, 12 layers + 429 retry, land scoping, 8 RSS categories, offline Phase-7 modules 10–13, ASGI endpoints | Sync (`9`) sandbox/host; Async ASGI (`1`) host |
| `Models/04_Hybrid_RAG/enterprise_rag_app/tests/test_site_studio.py` | 7 | UTM zones, solar ephemeris, UTCI heat stress, contour/DXF/SVG/GLB/OBJ/GeoJSON exports, ASGI + 11 MCP tools | Sync (`6`) sandbox/host; Async (`1`) host |
| `Models/04_Hybrid_RAG/enterprise_rag_app/tests/test_rag.py` | 20 | BM25/FAISS retrieval, RAGAS evaluator, guardrails, LLMOps, hubs, wards, 15 modules, ASGI + MCP registration | Sync (`18`) sandbox/host; Async (`2`) host |
| `Models/04_Hybrid_RAG/enterprise_rag_app/tests/test_agri_engine.py` | 6 | UTM farm polygon area & validation, CRUD/multi-plot/GeoJSON export, Sentinel-2 L2A indices + 2-date delta, NASA CMR & Landsat discovery, NASA POWER `-999` fill filtering & Open-Meteo ET0, farm-aware RAG (`faithfulness >= 0.70`) & ASGI endpoints | Sync (`5`) sandbox/host; Async ASGI (`1`) host |

---

## 3. Release Sign-Off Criteria

A module is marked `IMPLEMENTED AND VERIFIED` only when associated tests pass (`0` failures), static syntax checks pass, fail-closed `UNAVAILABLE` states and NASA/Copernicus attributions are verified under mocked offline failures, and `check_integrity.py --strict` reports `S0=0, S1=0`.
