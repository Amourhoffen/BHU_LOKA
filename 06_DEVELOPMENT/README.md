# BHU LOKA (भूलोक) — Development & Engineering Standards (R0 / R0.1)

**Project Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  

## Engineering Workflow Rules

1. **Software-Only Scope:** BHU LOKA delivers web apps, FastAPI/FastMCP services, GIS/Earth visualization, satellite processing pipelines, ML analytics, and Hybrid RAG reporting. Hardware devices, wearables, and firmware are out of current scope.
2. **Non-Destructive Extensions:** Additive modules attach via `FastAPI` `APIRouter` and shared vendor JS classes without breaking existing R0 HTTP routes (`35` custom routes total after `/api/v1/agri`) or `11` MCP tools.
3. **Windows Concurrency & SQLite Hygiene:** Always wrap `sqlite3.connect` calls in deterministic `try/finally` close (`@contextmanager def _get_conn()`) and never hold threading locks across blocking network I/O (`_wait_overpass_slot`).
4. **Zero Hardcoded Secrets:** Credentials (`NASA_EARTHDATA_USER`, `NASA_EARTHDATA_PASS`, `EE_PROJECT`, `COPERNICUS_*`) are read exclusively from environment variables or external user config.
5. **Gatekeeping Checks Before Sign-Off:**
   - Python tests (`test_india_location_street_intel.py`, `test_site_studio.py`, `test_rag.py`, `test_agri_engine.py`)
   - `node --check` on all `.js` bundles and HTML `<script>` blocks
   - `check_integrity.py --strict` across all touched code and SDLC documentation files
