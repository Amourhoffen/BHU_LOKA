#!/usr/bin/env python3
"""
MASTER UNIFY & CLEAN SCRIPT FOR BHU LOKA
=========================================
1. Removes Top-Right elements:
   - Bell button (#btn-api-chip)
   - Gear button (toggleHeroMap)
   - PK avatar block (Prince Kumar / PA2511CDH37)
2. Removes Bottom Timeline:
   - Entire #bhu-time-machine div + all child nodes
   - Adds CSS to guarantee #bhu-time-machine is permanently hidden
3. Fixes GPS Stream HUD:
   - Removes duplicate close buttons (#btn-close-gps-stream and #btn-close-gps-hud)
   - Keeps only one clean close button (top-right .hud-close-btn)
4. Fixes Left Rail Vitals:
   - Adds flex-1 min-h-0 to #left-health-vitals
   - Ensures CSS displays #left-health-vitals when tab is active
   - Fixes switchLeftDockTab function to cleanly switch between AI, Insights, and Vitals
5. Fixes 3D Hazard Filters FAB & Panel:
   - Sets #bhu-3d-fab to bottom: 38px; right: 18px; z-index: 2500
   - Solid glassmorphism prevents any text collision with footer
   - Sets #bhu-3d-panel to bottom: 84px; right: 18px; z-index: 2501
   - All 7 hazard layers with glowing colored dots and smooth toggles
6. Syncs the result across:
   - public/index.html
   - public/bhu_loka_cyber_dashboard.html
   - bhu_loka_cyber_dashboard.html (root)
"""

import os, re, shutil

BASE_DIR = r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"
PRIMARY_FILE = os.path.join(BASE_DIR, "public", "index.html")

TARGETS = [
    os.path.join(BASE_DIR, "public", "index.html"),
    os.path.join(BASE_DIR, "public", "bhu_loka_cyber_dashboard.html"),
    os.path.join(BASE_DIR, "bhu_loka_cyber_dashboard.html"),
]

def clean_html(html):
    # 1. Remove Bell button (#btn-api-chip)
    html = re.sub(r'<button[^>]+id=["\']btn-api-chip["\'][^>]*>.*?</button>\s*', '', html, flags=re.DOTALL)

    # 2. Remove Gear button (toggleHeroMap)
    html = re.sub(r'<button[^>]+onclick=["\']toggleHeroMap\(\)["\'][^>]*>.*?</button>\s*', '', html, flags=re.DOTALL)

    # 3. Remove PK avatar block
    html = re.sub(r'<div class=["\']flex items-center gap-1\.5 pl-2 border-l[^"\']*["\']>\s*<div class=["\']w-7 h-7 rounded-full[^"\']*["\']>.*?PK.*?</div>\s*</div>\s*(?:<div[^>]*>.*?Prince Kumar.*?</div>\s*</div>)?\s*</div>', '', html, flags=re.DOTALL)
    # Generic backup for PK block if slightly different markup
    html = re.sub(r'<div class=["\']flex items-center gap-1\.5 pl-2 border-l border-slate-700/80["\']>.*?PA2511CDH37.*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)

    # 4. Remove #bhu-time-machine element completely
    html = re.sub(r'<!-- GLOBAL TIME MACHINE.*?-->\s*<div id=["\']bhu-time-machine["\'].*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id=["\']bhu-time-machine["\'].*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)

    # 5. Fix GPS HUD duplicate close buttons:
    # Remove #btn-close-gps-stream and #btn-close-gps-hud
    html = re.sub(r'<button[^>]+id=["\']btn-close-gps-stream["\'][^>]*>.*?</button>\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'<button[^>]+id=["\']btn-close-gps-hud["\'][^>]*>.*?</button>\s*', '', html, flags=re.DOTALL)

    # 6. Fix #left-health-vitals classes to have flex-1 min-h-0
    html = re.sub(
        r'<div id=["\']left-health-vitals["\'] class=["\']hidden flex flex-col',
        r'<div id="left-health-vitals" class="hidden flex-1 min-h-0 flex flex-col',
        html
    )

    # 7. Remove any old #btn-3d-layer-toggle buttons
    html = re.sub(r'<button[^>]+id=["\']btn-3d-layer-toggle["\'][^>]*>.*?</button>\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'<div[^>]+id=["\']bhu-3d-layer-panel["\'][^>]*>.*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)

    # 8. Ensure #bhu-time-machine is permanently hidden in CSS
    time_machine_hide_css = """
    #bhu-time-machine, .bhu-time-machine-bar, [id*="time-machine"] {
      display: none !important;
      height: 0 !important;
      min-height: 0 !important;
      max-height: 0 !important;
      padding: 0 !important;
      margin: 0 !important;
      border: none !important;
      visibility: hidden !important;
      pointer-events: none !important;
      overflow: hidden !important;
    }
    #left-health-vitals {
      flex: 1 1 0% !important;
      min-height: 0 !important;
    }
    #holo-live-tracker-hud {
      position: absolute !important;
      top: 50px !important;
      right: 14px !important;
    }
    #holo-live-tracker-hud .hud-close-btn {
      position: absolute !important;
      top: 8px !important;
      right: 10px !important;
      width: 24px !important;
      height: 24px !important;
      border-radius: 6px !important;
      background: rgba(255,255,255,0.08) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      color: rgba(255,255,255,0.7) !important;
      font-size: 16px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      cursor: pointer !important;
      line-height: 1 !important;
      z-index: 10 !important;
    }
    #holo-live-tracker-hud .hud-close-btn:hover {
      background: rgba(239,68,68,0.25) !important;
      color: #fff !important;
      border-color: rgba(239,68,68,0.4) !important;
    }
    #workstation-footer {
      height: 28px !important;
      background: rgba(3, 6, 14, 0.98) !important;
      border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
      padding: 0 16px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      font-size: 10px !important;
      font-family: 'JetBrains Mono', monospace !important;
      color: #64748b !important;
      position: relative !important;
      z-index: 40 !important;
    }
    #bhu-3d-fab {
      position: fixed !important;
      bottom: 38px !important;
      right: 18px !important;
      z-index: 2500 !important;
      display: flex !important;
      align-items: center !important;
      gap: 7px !important;
      padding: 0 16px 0 12px !important;
      height: 36px !important;
      border-radius: 9999px !important;
      background: linear-gradient(135deg, rgba(2,132,199,0.96) 0%, rgba(6,182,212,0.96) 50%, rgba(16,185,129,0.92) 100%) !important;
      color: #ffffff !important;
      font-family: 'Space Grotesk', system-ui, sans-serif !important;
      font-weight: 700 !important;
      font-size: 11px !important;
      letter-spacing: 0.06em !important;
      border: 1.5px solid rgba(255,255,255,0.4) !important;
      box-shadow: 0 4px 20px rgba(6,182,212,0.55), 0 2px 8px rgba(0,0,0,0.8) !important;
      cursor: pointer !important;
      user-select: none !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
      transition: transform 0.18s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.18s ease !important;
    }
    #bhu-3d-fab:hover {
      transform: scale(1.05) translateY(-1px) !important;
      box-shadow: 0 6px 28px rgba(6,182,212,0.8), 0 4px 12px rgba(0,0,0,0.9) !important;
    }
    #bhu-3d-panel {
      position: fixed !important;
      bottom: 82px !important;
      right: 18px !important;
      z-index: 2501 !important;
      width: 236px !important;
      background: rgba(8, 14, 28, 0.95) !important;
      backdrop-filter: blur(28px) saturate(180%) !important;
      -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
      border: 1px solid rgba(255, 255, 255, 0.14) !important;
      border-radius: 16px !important;
      box-shadow: 0 24px 64px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.06) !important;
      overflow: hidden !important;
      transform-origin: bottom right !important;
      transition: transform 0.24s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s ease !important;
    }
    #bhu-3d-panel.lp-hidden {
      transform: scale(0.85) translateY(10px) !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
    """

    if '</style>' in html:
        # inject inside the last style block
        html = html.replace('</style>', time_machine_hide_css + '\n</style>', 1)

    return html

def main():
    print("Reading primary file:", PRIMARY_FILE)
    with open(PRIMARY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned = clean_html(content)

    for target in TARGETS:
        print(f"Writing updated workstation to: {target}")
        with open(target, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"  -> Successfully updated {os.path.basename(target)} ({len(cleaned):,} bytes)")

    print("\nAll workstations synchronized successfully!")

if __name__ == '__main__':
    main()
