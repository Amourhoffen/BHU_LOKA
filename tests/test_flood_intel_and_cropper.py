"""
BHU LOKA — Scientific Flood Model Intelligence & Pan-India 3D Cropper Tests
============================================================================
Validates the scientific flood model presentation, empirical metrics from the
IIT Patna research paper, spatial cross-validation benchmarks, zero-hallucination
horizon constraints, and the pan-India 2D-to-3D terrain cropper.
"""

import json
import subprocess
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

BHU_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_HTML_PATH = BHU_ROOT / "bhu_loka_cyber_dashboard.html"
FLOOD_INTEL_JS_PATH = BHU_ROOT / "Assets" / "vendor" / "bhu_loka_flood_intel.js"


def test_flood_intel_js_exists_and_parses():
    """Verify that bhu_loka_flood_intel.js exists and has clean JS syntax."""
    assert FLOOD_INTEL_JS_PATH.exists(), f"Missing {FLOOD_INTEL_JS_PATH}"
    res = subprocess.run(["node", "-c", str(FLOOD_INTEL_JS_PATH)], capture_output=True, text=True)
    assert res.returncode == 0, f"Syntax error in bhu_loka_flood_intel.js: {res.stderr}"


def test_research_data_empirical_metrics():
    """Verify that BHU_FLOOD_RESEARCH_DATA has exact empirical research values."""
    node_eval_script = f"""
    const fs = require('fs');
    const vm = require('vm');
    const code = fs.readFileSync('{FLOOD_INTEL_JS_PATH.as_posix()}', 'utf-8');
    const sandbox = {{ window: {{ addEventListener: () => {{}} }}, document: {{ addEventListener: () => {{}} }} }};
    vm.createContext(sandbox);
    vm.runInContext(code, sandbox);
    const data = sandbox.window.BHU_FLOOD_RESEARCH_DATA;
    console.log(JSON.stringify(data));
    """
    res = subprocess.run(["node", "-e", node_eval_script], capture_output=True, text=True, check=True)
    data = json.loads(res.stdout.strip())

    # Metadata & Authors
    meta = data["metadata"]
    assert "Sequential Compound Hydro-Thermal Risk" in meta["title"]
    authors = [a["name"] for a in meta["authors"]]
    assert "Prince Kumar" in authors
    assert "Payal Priyadarshini" in authors
    assert meta["teamName"] == "Amour Hoffen"

    # Technical Performance (Track 1)
    perf = data["technicalPerformance"]
    assert perf["sampleCount"] == 60000
    assert abs(perf["f1Score"] - 0.6530) < 1e-4
    assert abs(perf["rocAuc"] - 0.7498) < 1e-4
    assert abs(perf["precision"] - 0.6842) < 1e-4
    assert abs(perf["recallPod"] - 0.6245) < 1e-4
    assert abs(perf["iouCsi"] - 0.4848) < 1e-4
    assert abs(perf["brierScore"] - 0.2003) < 1e-4
    cm = perf["confusionMatrix"]
    assert cm["truePositives"] == 18735
    assert cm["falseNegatives"] == 11265
    assert cm["trueNegatives"] == 22593
    assert cm["falsePositives"] == 7407

    # Spatial Cross-Validation (Track 2: N=3,200)
    leakage = data["spatialValidationLeakage"]
    assert abs(leakage["randomCv"]["meanR2"] - 0.9688) < 1e-4
    assert abs(leakage["spatialBlockCv"]["meanR2"] - 0.8258) < 1e-4
    assert abs(leakage["leakagePenalty"]["deltaR2"] - (-0.1430)) < 1e-4
    assert abs(leakage["leakagePenalty"]["deltaR2Pct"] - (-14.8)) < 0.1
    # Block 2 Central PMC drop
    b2 = next(b for b in leakage["spatialBlockCv"]["blocks"] if b["block"] == 2)
    assert abs(b2["r2"] - 0.5266) < 1e-4
    assert "Urban Core" in b2["label"]

    # Omission Discovery
    omission = data["patnaOmissionDiscovery"]
    assert omission["unSpiderSpecular"]["detectedFloodAreaKm2"] == 4.01
    assert omission["bhuLokaBimodal"]["totalInundatedAreaKm2"] == 99.60
    assert abs(omission["bhuLokaBimodal"]["omissionErrorPct"] - 95.98) < 1e-2

    # Exposure Intelligence
    exp = data["exposureIntelligence"]
    assert exp["modeledPmcPopulation2020"] == 214281
    assert exp["populationInFloodMask"] == 167246
    assert exp["populationInDepressionSinks"] == 60790
    assert exp["populationInJointFloodAndSink"] == 49380

    # Safe Shelters (Verified High Grounds)
    shelters = data["safeShelters"]
    assert len(shelters) >= 5
    shelter_names = [s["name"] for s in shelters]
    assert any("Danapur" in n for n in shelter_names)
    assert any("IIT Patna" in n for n in shelter_names)
    assert any("Bailey Road" in n for n in shelter_names)
    assert any("Gyan Bhawan" in n for n in shelter_names)
    assert any("AIIMS" in n for n in shelter_names)

    # Why Sinks Failed
    sinks = data["whyLowSinksFailed"]
    assert any("Rajendra Nagar" in s["locality"] for s in sinks)
    assert any("Kankarbagh" in s["locality"] for s in sinks)

    # Sensor Comparison
    sensors = data["sensorComparison"]
    assert sensors["sentinel1"]["frequencyGhz"] == 5.405
    assert "1.25 GHz" in sensors["nisarDualBand"]["frequencyGhz"]
    assert "3.2 GHz" in sensors["nisarDualBand"]["frequencyGhz"]


def test_dashboard_html_model_intel_integration():
    """Verify dashboard HTML includes script tag, navigation buttons, and modal structure."""
    with open(DASHBOARD_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Script tag inclusion
    scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    assert any("bhu_loka_flood_intel.js" in s for s in scripts), "bhu_loka_flood_intel.js script tag missing"

    # Top Command Bar Buttons
    sar_btn = soup.find(id="link-open-sar-hero")
    assert sar_btn is not None, "Top nav link-open-sar-hero missing"
    assert "openModelIntelModal" in sar_btn.get("onclick", "")

    eval_btn = soup.find(id="btn-open-model-eval")
    assert eval_btn is not None, "Top nav btn-open-model-eval missing"
    assert "performance" in eval_btn.get("onclick", "")

    # Subheader 3D Mode Button
    mode_btn = soup.find(id="btn-model-intel-nav")
    assert mode_btn is not None, "Subheader btn-model-intel-nav missing"

    # Modal Structure
    modal = soup.find(id="bhu-model-intel-modal")
    assert modal is not None, "Modal #bhu-model-intel-modal missing"
    content_pane = soup.find(id="model-intel-content-pane")
    assert content_pane is not None, "Modal #model-intel-content-pane missing"

    # Modal Tabs
    tabs = ["overview", "performance", "horizon", "omission", "exposure", "shelters", "nisar", "report"]
    for t in tabs:
        tab_btn = soup.find(id=f"tab-btn-{t}")
        assert tab_btn is not None, f"Modal tab button #tab-btn-{t} missing"


def test_dashboard_html_pan_india_cropper_features():
    """Verify pan-India location search and calibrated DEM synthesis."""
    with open(DASHBOARD_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Crop studio search input
    search_input = soup.find(id="crop-location-search")
    assert search_input is not None, "Crop location search input missing"

    # Crop modal existence
    crop_modal = soup.find(id="bhu-crop-3d-modal")
    assert crop_modal is not None, "Crop modal missing"

    # Check that calibrated DEM synthesizer is defined in JS
    assert "function synthesizeCalibratedDemGrid" in html, "synthesizeCalibratedDemGrid function missing"
    assert "window.cropStudioGoTo" in html, "cropStudioGoTo missing"
    assert "window.cropStudioSearchLocation" in html, "cropStudioSearchLocation missing"


def test_calibrated_dem_synthesizer_output():
    """Evaluate synthesizeCalibratedDemGrid for multiple Indian geographical zones."""
    node_script = """
    // Extract synthesizeCalibratedDemGrid from dashboard html
    const fs = require('fs');
    const html = fs.readFileSync('bhu_loka_cyber_dashboard.html', 'utf-8');
    const startIdx = html.indexOf('function synthesizeCalibratedDemGrid');
    const endIdx = html.indexOf('const _hitPlaneMat', startIdx);
    const fnCode = html.slice(startIdx, endIdx);

    eval(fnCode);

    const zones = [
      { name: 'Patna', lat: 25.594, lon: 85.138, expMin: 45, expMax: 65 },
      { name: 'Bengaluru', lat: 12.971, lon: 77.594, expMin: 500, expMax: 800 },
      { name: 'Ladakh', lat: 34.152, lon: 77.577, expMin: 2500, expMax: 4000 },
      { name: 'Mumbai', lat: 19.076, lon: 72.877, expMin: 5, expMax: 40 }
    ];

    const results = zones.map(z => {
      const res = synthesizeCalibratedDemGrid(z.lat, z.lon, z.name, 'India', 0.04, 10);
      return {
        name: z.name,
        matrixRows: res.elev_matrix.length,
        matrixCols: res.elev_matrix[0].length,
        meanM: res.metrics.mean_m,
        terrainClass: res.metrics.terrain_class,
        inRange: (res.metrics.mean_m >= z.expMin && res.metrics.mean_m <= z.expMax)
      };
    });

    console.log(JSON.stringify(results));
    """
    res = subprocess.run(["node", "-e", node_script], cwd=BHU_ROOT, capture_output=True, text=True, check=True)
    results = json.loads(res.stdout.strip())
    assert len(results) == 4
    for r in results:
        assert r["matrixRows"] == 10
        assert r["matrixCols"] == 10
        assert r["inRange"] is True, f"Elevation out of range for {r['name']}: {r['meanM']}m"


def test_sovereign_command_dock_spectral_legend_and_presentation():
    """Verify the omnipresent Sovereign Command Dock, Hologram Spectral Legend, Live GPS HUD, and Presentation Modal."""
    with open(DASHBOARD_HTML_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # 1. Sovereign Command Dock
    dock = soup.find("nav", id="sovereign-quick-dock")
    assert dock is not None, "Missing #sovereign-quick-dock"
    dock_btns = dock.find_all("button")
    assert len(dock_btns) >= 7, f"Expected at least 7 workspace quick-switch buttons, found {len(dock_btns)}"

    # 2. Hologram Spectral & Color Legend HUD
    spectral_legend = soup.find("div", id="holo-spectral-legend")
    assert spectral_legend is not None, "Missing #holo-spectral-legend HUD"
    assert "Pink / Magenta" in spectral_legend.text
    assert "Blue Dot / Pin" in spectral_legend.text
    assert "Dhamani Pokhar" in spectral_legend.text

    # 3. Real-Time Tactical GPS Telemetry HUD
    live_hud = soup.find("div", id="holo-live-tracker-hud")
    assert live_hud is not None, "Missing #holo-live-tracker-hud"
    assert "Real-Time GPS Stream" in live_hud.text
    assert "45.5m MASL" in live_hud.text

    # 4. NASA Presentation Deck Modal
    pres_modal = soup.find("div", id="bhu-presentation-modal")
    assert pres_modal is not None, "Missing #bhu-presentation-modal"
    iframe = pres_modal.find("iframe", id="bhu-presentation-iframe")
    assert iframe is not None, "Missing iframe inside presentation modal"

    # 5. Top Header Badges
    assert soup.find("button", id="btn-open-cropper-header") is not None
    assert soup.find("button", id="btn-open-presentation-header") is not None

    # 6. AI Assistant Spectral Color Reasoning Check
    ai_script_path = BHU_ROOT / "Assets" / "vendor" / "bhu_loka_ai.js"
    assert ai_script_path.exists()
    node_test = """
    const fs = require('fs');
    global.window = {};
    global.document = { getElementById: () => null, querySelector: () => null, querySelectorAll: () => [], addEventListener: () => {} };
    eval(fs.readFileSync('Assets/vendor/bhu_loka_ai.js', 'utf8'));
    const res = window.BhuLokaAI.generateSovereignResponse('Map par pink aur blue color ka kya matlab hai', 'farmer', 'hi');
    console.log(JSON.stringify({ ok: !!res.answer && res.answer.includes('PINK') && res.answer.includes('BLUE') }));
    """
    res = subprocess.run(["node", "-e", node_test], cwd=BHU_ROOT, capture_output=True, text=True, check=True)
    out = json.loads(res.stdout.strip())
    assert out["ok"] is True
