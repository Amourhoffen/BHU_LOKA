#!/usr/bin/env python3
"""
BHU LOKA (भूलोक) CI/CD Automated Frontend & Scenegraph Verifier
Runs headless Chromium against bhu_loka_cyber_dashboard.html?autoTest=1,
extracts and asserts scientific parentage, axial tilt, ephemeris and UI integrity.
"""

import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path

def find_chrome():
    if os.environ.get("CHROME_BIN"):
        return os.environ.get("CHROME_BIN")
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        p = shutil.which(name)
        if p:
            return p
    win_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p
    return None

def main():
    chrome = find_chrome()
    if not chrome:
        print("[CI ERROR] Chromium or Google Chrome binary not found.")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent.parent
    dashboard_path = repo_root / "bhu_loka_cyber_dashboard.html"
    if not dashboard_path.exists():
        print(f"[CI ERROR] Dashboard file not found at: {dashboard_path}")
        sys.exit(1)

    url = f"{dashboard_path.as_uri()}?autoTest=1"
    print(f"[CI] Running headless verification on: {url}")
    print(f"[CI] Chrome binary: {chrome}")

    cmd = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--virtual-time-budget=6000",
        "--dump-dom",
        url
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[CI ERROR] Headless browser execution failed with returncode {res.returncode}")
        print("Stderr:", res.stderr)
        sys.exit(res.returncode)

    match = re.search(r'<div id="step1-test-results-json"[^>]*>(.*?)</div>', res.stdout, re.DOTALL)
    if not match:
        print("[CI ERROR] #step1-test-results-json element not found in dumped DOM.")
        print(f"Dumped DOM length: {len(res.stdout)}")
        sys.exit(1)

    try:
        results = json.loads(match.group(1).strip())
    except Exception as e:
        print(f"[CI ERROR] Failed to parse JSON test results: {e}")
        print("Raw payload:", match.group(1)[:500])
        sys.exit(1)

    print("\n" + "=" * 60)
    print("      BHU LOKA FRONTEND & SCENEGRAPH CI TEST REPORT      ")
    print("=" * 60)
    print(json.dumps(results, indent=2))

    all_passed = results.get("allPassed", False)
    world = results.get("worldView", {})
    solar = results.get("solarView", {})
    ui = results.get("uiDeck", {})

    print("\n[CRITICAL SCIENTIFIC ASSERTIONS]")
    print(f"  - Earth Axial Obliquity 23.44 deg : {'PASS' if world.get('axialTiltMatches23_44') else 'FAIL'}")
    print(f"  - Moon Parentage is Earth only   : {'PASS' if world.get('moonParentIsEarth') else 'FAIL'}")
    print(f"  - Zero Planets Orbiting Earth    : {'PASS' if world.get('hasZeroPlanetsInWorld') else 'FAIL'}")
    print(f"  - Sun Origin (0,0,0) PointLight  : {'PASS' if solar.get('sunLightAtOrigin') and solar.get('sunLightIsPointLight') else 'FAIL'}")
    print(f"  - 8 Heliocentric Planets         : {'PASS' if solar.get('has8Planets') else 'FAIL'}")
    print(f"  - Moon Parentage in Solar View   : {'PASS' if solar.get('moonParentIsEarthNotSun') else 'FAIL'}")
    print(f"  - Astronomical Scale Toggle      : {'PASS' if solar.get('scaleToggleWorks') else 'FAIL'}")
    print(f"  - 5-Hub Workstation Navigation   : {'PASS' if ui.get('has5MainTabs') else 'FAIL'}")
    print(f"  - Zero Mock 5300 / 7550 Sum      : {'PASS' if ui.get('zeroMock5300Satellites') else 'FAIL'}")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("# 🛰️ BHU LOKA Frontend & Ephemeris Verification\n\n")
            f.write(f"**Overall Status:** {'✅ PASSED' if all_passed else '❌ FAILED'}\n\n")
            f.write("| Verification Test | Required Scientific Invariant | Result |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| **Earth Obliquity** | Axial Tilt $= 23.44^\\circ$ | `{'PASS' if world.get('axialTiltMatches23_44') else 'FAIL'}` ({world.get('axialTiltDeg')}°) |\n")
            f.write(f"| **Lunar Hierarchy** | Moon orbits Earth only | `{'PASS' if world.get('moonParentIsEarth') else 'FAIL'}` (Parent: EarthSystem) |\n")
            f.write(f"| **Planetary Exclusion** | Zero planet spheres in WorldGroup | `{'PASS' if world.get('hasZeroPlanetsInWorld') else 'FAIL'}` ({world.get('planetsInWorldCount')} planets) |\n")
            f.write(f"| **Solar Heliocentrism** | Sun at $(0,0,0)$ with PointLight | `{'PASS' if solar.get('sunLightAtOrigin') else 'FAIL'}` |\n")
            f.write(f"| **Planetary Ephemeris** | 8 Keplerian Planets (Mercury..Neptune) | `{'PASS' if solar.get('has8Planets') else 'FAIL'}` (Count: {solar.get('planetCount')}) |\n")
            f.write(f"| **Solar Lunar Orbit** | Moon orbits Earth Pivot in Solar view | `{'PASS' if solar.get('moonParentIsEarthNotSun') else 'FAIL'}` |\n")
            f.write(f"| **Scale Toggle** | Visual Schematic vs Distance-True AU | `{'PASS' if solar.get('scaleToggleWorks') else 'FAIL'}` |\n")
            f.write(f"| **Navigation Reset** | Exactly 5 Top Hubs | `{'PASS' if ui.get('has5MainTabs') else 'FAIL'}` |\n")
            f.write(f"| **Zero Fabricated Stats** | Live ephemeris or honest UNAVAILABLE | `{'PASS' if ui.get('zeroMock5300Satellites') else 'FAIL'}` |\n")

    if not all_passed:
        print("\n[CI GATE FAILED] Not all scientific and structural assertions passed.")
        sys.exit(1)

    print("\n[CI GATE PASSED] All 12 scientific and frontend invariants verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
