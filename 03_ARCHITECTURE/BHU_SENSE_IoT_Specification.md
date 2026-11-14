# BHU LOKA (भूलोक) — Future Telemetry Concept (`BHU SENSE`, Out of Current Scope)

**Document ID:** `BHU-SPEC-IOT-01`  
**Status:** `NOT IMPLEMENTED` (`EXPLICITLY OUT OF CURRENT SCOPE` — Future Roadmap Concept Only)  
**Project Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  

---

## 1. Critical Scope Clarification (Software-Only Platform)

BHU LOKA is currently a **SOFTWARE-ONLY** scientific research and geospatial decision intelligence platform covering web applications, Python/FastAPI backends, 2D/3D GIS visualization, satellite data processing, scientific analytics, AI agents, MCP tools, and research reporting workflows.

**EXPLICITLY OUT OF CURRENT SCOPE:**
- IoT hardware engineering or procurement
- Wearable devices
- Physical sensor manufacturing
- Physical monitoring devices
- Embedded hardware firmware (e.g., ESP32, LoRaWAN boards)

No IoT device, wearable, firmware binary, or live physical telemetry broker is developed, purchased, simulated, or deployed in the current release (`R0` / `R0.1`). Soil moisture, evapotranspiration (`ET0`), solar radiation, and root-zone wetness in R0.1 come exclusively from verified remote-sensing and reanalysis software services (**NASA LaRC POWER**, **NASA EOSDIS CMR / GIBS**, **USGS/NASA Landsat**, **Copernicus Sentinel-2**, and **Open-Meteo ECMWF/GLO-90**).

---

## 2. Optional Future Software Ingestion Draft (Deferred Beyond Current Release)

If institutional hardware partners supply pre-calibrated sensor gateways in a future multi-year phase (`R3+`), BHU LOKA's software API tier defines the following conceptual JSON ingestion boundaries:
- Mandatory hardware device identity and `farm_id` foreign key linking to `agri_farms`
- ISO-8601 UTC timestamp (`timestamp_utc`) with strict heartbeat staleness gates (`OFFLINE` / `UNAVAILABLE` UI rendering after $3\times$ missed intervals)
- Physical range quarantine flags (`VALID`, `OUT_OF_RANGE`, `STALE_HEARTBEAT`) so uncalibrated readings never contaminate satellite or hydrological analytics.
