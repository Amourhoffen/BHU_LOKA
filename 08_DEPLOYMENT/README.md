# BHU LOKA (भूलोक) — Deployment & Runtime Runbook (R0 / R0.1)

**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  

## Local Sovereign Startup (Software-Only Platform)

1. **Backend API (`127.0.0.1:8000`):**
   ```powershell
   python -m uvicorn main:app --app-dir "Bhu Loka - भूलोक/Models/04_Hybrid_RAG/enterprise_rag_app" --host 127.0.0.1 --port 8000
   ```
   Or launch `Launch_BhuLoka_FullStack.bat`.
2. **Static Web Serving (`127.0.0.1:8080`):**
   ```powershell
   python -m http.server 8080 --bind 127.0.0.1 --directory "Bhu Loka - भूलोक"
   ```
3. **MCP Server (`127.0.0.1:8001` or stdio):**
   ```powershell
   python "Bhu Loka - भूलोक/Pipelines/bhu_loka_mcp_server.py"
   ```

## Environment Requirements

- **Python:** `3.13.7` (`fastapi`, `uvicorn`, `httpx`, `scikit-learn`, `torch`, `faiss-cpu`, `sentence-transformers`, `mcp`, `beautifulsoup4`).
- **Node.js / Browser:** Host `chrome.exe` supports headless rendering & screenshot verification; `chrome-devtools-mcp@1.13.0` automation specifically requires host Node `>=22.12.0` (`v22.11.0` currently installed).
- **Optional Credentials:** NASA CMR, NASA GIBS WMTS, and NASA LaRC POWER require zero credentials. Set `NASA_EARTHDATA_USER` / `NASA_EARTHDATA_PASS` in process environment only if downloading raw MODIS/HLS HDF files via `Data/06_LST_Thermal/download_modis_auto.py`.
