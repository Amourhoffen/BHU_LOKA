#!/usr/bin/env python3
"""
BHU LOKA – Comprehensive Professional UI/UX Enhancement
========================================================
Targets:
  1. Top header bar – cleaner, tighter, Apple-class typography
  2. Left chevron strip – hide completely
  3. 3D Layer panel – fix color dots (make them actual glowing circles)
  4. Left AI panel – professional card layout
  5. Scientific Modal (Model Intel) – clean glassmorphic 
  6. Flood Prediction Modal – cleaner inputs/outputs
  7. Bottom time machine – polished minimal bar
  8. All badge-chips, buttons – consistent hover states
  9. Global typography consistency
  10. Remove any stale "Skip" button remnants
"""

import re, os, shutil

BASE = r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"
FILES = [
    os.path.join(BASE, "public", "index.html"),
    os.path.join(BASE, "bhu_loka_cyber_dashboard.html"),
]

# ─────────────────────────────────────────────────────────────────
# GLOBAL PROFESSIONAL DESIGN OVERRIDES CSS
# ─────────────────────────────────────────────────────────────────
PRO_CSS = r"""
  <!-- ═══ BHU LOKA – Professional UI/UX Design System v2 ═══ -->
  <style id="bhu-pro-ui-v2">

    /* ── Global Resets & Typography ── */
    *, *::before, *::after { box-sizing: border-box; }

    body {
      font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: optimizeLegibility;
    }

    /* ── Hide ALL stale chevron/nav elements ── */
    .bhu-nav-chevron,
    [class*="bhu-nav-chevron"],
    #bhu-side-chevrons,
    .side-chevron-btn {
      display: none !important;
      pointer-events: none !important;
      visibility: hidden !important;
    }

    /* ── Hide the stale "Skip >" button on intro ── */
    #bhu-skip-btn,
    button[onclick*="skipBhuIntro"]:not(#bhu-dismiss-intro) {
      display: none !important;
    }

    /* ═══ TOP HEADER PROFESSIONAL REDESIGN ═══ */
    header, #bhu-topbar, [id*="topbar"], [id*="header"]:not([id*="modal"]) {
      border-bottom: 1px solid rgba(255,255,255,0.055) !important;
      background: rgba(4,7,16,0.96) !important;
      backdrop-filter: blur(20px) saturate(160%) !important;
      -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
    }

    /* BHU LOKA wordmark – crisp */
    .bhu-wordmark, #bhu-logo-text {
      font-weight: 800;
      letter-spacing: -0.02em;
      font-size: 15px;
    }

    /* ── BADGE CHIPS – unified pro style ── */
    .badge-chip {
      background: rgba(255,255,255,0.045) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      color: rgba(200,215,235,0.85) !important;
      font-size: 10px !important;
      font-weight: 600 !important;
      letter-spacing: 0.05em !important;
      padding: 3px 10px !important;
      border-radius: 6px !important;
      transition: all 0.14s ease !important;
      white-space: nowrap !important;
    }
    .badge-chip:hover {
      background: rgba(255,255,255,0.09) !important;
      border-color: rgba(255,255,255,0.18) !important;
      color: #fff !important;
    }

    /* Accent chips (DANCING WITH SARs / CROP TO 3D / PREDICT AREA) */
    .badge-chip[style*="accent-primary"],
    #link-open-sar-hero,
    #btn-open-model-eval,
    #btn-open-cropper-header {
      font-size: 10px !important;
      font-weight: 700 !important;
      letter-spacing: 0.06em !important;
    }

    /* ═══ LEFT RAIL (VS Code Activity Bar) – cleaner ═══ */
    #vscode-activity-bar,
    [id="vscode-activity-bar"] {
      background: rgba(3,5,12,0.98) !important;
      border-right: 1px solid rgba(255,255,255,0.05) !important;
      width: 48px !important;
    }
    #vscode-activity-bar button,
    #vscode-activity-bar a {
      width: 36px !important;
      height: 36px !important;
      border-radius: 10px !important;
      transition: background 0.14s ease, transform 0.1s ease !important;
    }
    #vscode-activity-bar button:hover,
    #vscode-activity-bar a:hover {
      background: rgba(255,255,255,0.08) !important;
      transform: scale(1.05) !important;
    }

    /* ═══ LEFT RAIL PANEL (AI Assistant etc.) – pro card design ═══ */
    #left-rail, [id="left-rail"] {
      background: rgba(4,7,18,0.97) !important;
      border-right: 1px solid rgba(255,255,255,0.055) !important;
      backdrop-filter: blur(20px) !important;
      -webkit-backdrop-filter: blur(20px) !important;
    }

    /* Tab bar in left panel */
    #left-rail .flex.border-b,
    #left-rail [role="tablist"] {
      background: rgba(3,5,12,0.9) !important;
      border-bottom: 1px solid rgba(255,255,255,0.07) !important;
      padding: 0 8px !important;
      gap: 2px !important;
    }
    #left-rail button[role="tab"],
    #left-rail .tab-btn {
      font-size: 10.5px !important;
      font-weight: 600 !important;
      letter-spacing: 0.03em !important;
      border-radius: 6px !important;
      padding: 6px 10px !important;
      transition: all 0.14s ease !important;
      border: none !important;
      background: transparent !important;
      color: rgba(148,163,184,0.75) !important;
    }
    #left-rail button[role="tab"]:hover {
      background: rgba(255,255,255,0.06) !important;
      color: rgba(226,232,240,0.9) !important;
    }
    #left-rail button[role="tab"].active,
    #left-rail button[role="tab"][aria-selected="true"],
    #left-rail button.active-tab {
      background: rgba(45,156,219,0.15) !important;
      color: rgb(125,211,252) !important;
      border-bottom: 2px solid rgb(45,156,219) !important;
    }

    /* ═══ 3D LAYER PANEL – enhanced color dots and toggles ═══ */
    #bhu-3d-panel .lp-dot {
      width: 11px !important;
      height: 11px !important;
      border-radius: 50% !important;
      flex-shrink: 0 !important;
      border: 1.5px solid rgba(255,255,255,0.3) !important;
    }

    /* ═══ MODALS – unified glassmorphic professional style ═══ */
    .bhu-modal-overlay,
    [id*="modal"][class*="fixed"],
    [id*="modal-overlay"],
    [class*="modal"][class*="fixed inset"] {
      background: rgba(0,0,0,0.85) !important;
      backdrop-filter: blur(16px) !important;
      -webkit-backdrop-filter: blur(16px) !important;
    }

    .bhu-modal-container,
    [id*="modal"] > div:first-child,
    [id*="-modal"] .modal-body {
      border: 1px solid rgba(255,255,255,0.1) !important;
      border-radius: 16px !important;
      box-shadow: 0 32px 80px rgba(0,0,0,0.9), 0 0 0 1px rgba(255,255,255,0.05), inset 0 1px 0 rgba(255,255,255,0.07) !important;
    }

    /* ═══ BUTTONS – consistent professional style ═══ */
    button {
      font-family: 'Space Grotesk', system-ui, sans-serif !important;
      -webkit-font-smoothing: antialiased !important;
    }

    /* Primary action buttons */
    button[class*="bg-cyan"],
    button[class*="bg-sky"],
    button[class*="bg-blue"],
    button[id*="run-model"],
    button[id*="btn-run"],
    .btn-primary-action {
      transition: all 0.16s cubic-bezier(0.34,1.56,0.64,1) !important;
    }
    button[class*="bg-cyan"]:hover,
    button[class*="bg-sky"]:hover,
    button[class*="bg-blue"]:hover {
      transform: translateY(-1px) scale(1.01) !important;
      filter: brightness(1.1) !important;
    }
    button[class*="bg-cyan"]:active,
    button[class*="bg-sky"]:active {
      transform: scale(0.98) !important;
    }

    /* ═══ CLOSE BUTTONS – uniform ═══ */
    button[onclick*="close"],
    button[onclick*="Close"],
    button[aria-label*="close"],
    button[aria-label*="Close"] {
      width: 28px !important;
      height: 28px !important;
      border-radius: 8px !important;
      background: rgba(255,255,255,0.06) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      color: rgba(148,163,184,0.8) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: background 0.14s, color 0.14s !important;
      flex-shrink: 0 !important;
    }
    button[onclick*="close"]:hover,
    button[onclick*="Close"]:hover,
    button[aria-label*="close"]:hover,
    button[aria-label*="Close"]:hover {
      background: rgba(239,68,68,0.2) !important;
      color: rgb(248,113,113) !important;
      border-color: rgba(239,68,68,0.3) !important;
    }

    /* ═══ INPUT FIELDS – unified ═══ */
    input[type="text"],
    input[type="number"],
    select,
    textarea {
      font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace !important;
      font-size: 12px !important;
      background: rgba(0,0,0,0.4) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      border-radius: 8px !important;
      color: rgba(226,232,240,0.95) !important;
      transition: border-color 0.14s ease, box-shadow 0.14s ease !important;
      outline: none !important;
    }
    input[type="text"]:focus,
    input[type="number"]:focus,
    select:focus,
    textarea:focus {
      border-color: rgba(45,156,219,0.5) !important;
      box-shadow: 0 0 0 3px rgba(45,156,219,0.12) !important;
    }

    /* ═══ BOTTOM TIME MACHINE BAR – professional minimal ═══ */
    #bhu-time-machine {
      background: rgba(3,5,12,0.97) !important;
      border-top: 1px solid rgba(255,255,255,0.07) !important;
      height: 46px !important;
      padding: 0 16px !important;
    }
    #bhu-time-machine button {
      border-radius: 6px !important;
      transition: color 0.12s, background 0.12s !important;
    }
    #bhu-time-machine button:hover {
      background: rgba(255,255,255,0.07) !important;
      color: #f1f5f9 !important;
    }

    /* ═══ SECTION HEADERS – clean caps ═══ */
    .section-header,
    [class*="section-header"] {
      font-size: 9.5px !important;
      font-weight: 700 !important;
      letter-spacing: 0.1em !important;
      text-transform: uppercase !important;
      color: rgba(100,116,139,0.9) !important;
    }

    /* ═══ SCROLLBARS – minimal ═══ */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }

    /* ═══ TOAST NOTIFICATION – professional ═══ */
    #sovereign-toast-container .sovereign-toast {
      border-radius: 10px !important;
      backdrop-filter: blur(16px) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
      font-size: 12px !important;
      font-family: 'Space Grotesk', system-ui, sans-serif !important;
    }

    /* ═══ 3D LAYER FAB – final polish ═══ */
    #bhu-3d-fab {
      bottom: 60px !important;
      right: 16px !important;
    }

    /* ═══ RIGHT RAIL PANEL – pro card ═══ */
    #right-rail, [id="right-rail"] {
      background: rgba(4,7,18,0.97) !important;
      border-left: 1px solid rgba(255,255,255,0.055) !important;
    }

    /* ═══ GRID INFO CARDS in modals ═══ */
    .panel-inset,
    [class*="panel-inset"] {
      background: rgba(0,0,0,0.3) !important;
      border: 1px solid rgba(255,255,255,0.07) !important;
      border-radius: 10px !important;
      transition: border-color 0.14s !important;
    }
    .panel-inset:hover { border-color: rgba(255,255,255,0.12) !important; }

    /* ═══ PROBABILITY DISPLAYS – big numbers ═══ */
    [class*="text-5xl"],
    [class*="text-4xl"],
    .big-stat {
      font-family: 'Space Grotesk', system-ui, sans-serif !important;
      font-weight: 800 !important;
      letter-spacing: -0.02em !important;
    }

    /* ═══ RANGE SLIDERS ═══ */
    input[type="range"] {
      accent-color: #2d9cdb !important;
      cursor: pointer !important;
    }

    /* ═══ HORIZONTAL RULE / DIVIDER ═══ */
    hr { border-color: rgba(255,255,255,0.07) !important; }

    /* ═══ TAB NAVIGATION (view tabs – World / India 36 etc.) ═══ */
    #bhu-view-tabs button,
    #bhu-nav-tabs button,
    [id*="view-tabs"] button,
    #bhu-tabs button {
      font-size: 10.5px !important;
      font-weight: 600 !important;
      letter-spacing: 0.04em !important;
      border-radius: 6px !important;
      padding: 4px 10px !important;
      transition: all 0.14s !important;
    }

    /* ═══ Left rail small vertical dot indicators ═══ */
    #left-rail .h-1\.5,
    #left-rail [class*="h-1.5 w-1.5"] {
      display: none !important;
    }

    /* ═══ Animate panel opens ═══ */
    @keyframes bhu-panel-in {
      from { opacity: 0; transform: translateY(6px) scale(0.98); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    .panel { animation: bhu-panel-in 0.22s ease forwards; }

    /* ═══ Cursor always visible ═══ */
    *, *::before, *::after {
      cursor: auto !important;
    }
    button, a, [role="button"], input, select, textarea, label {
      cursor: pointer !important;
    }
    input[type="text"], input[type="number"], textarea {
      cursor: text !important;
    }
    input[type="range"] { cursor: grab !important; }

    /* ═══ Hide old "left side chevron strip" container ═══ */
    #bhu-left-chevron-strip,
    .bhu-chevron-strip,
    [id*="chevron-strip"],
    [class*="chevron-strip"] {
      display: none !important;
    }

    /* Small vertical 3-dot / chevron left-of-map area */
    [style*="position:absolute"][style*="left:0"][style*="top:50%"] > button,
    [style*="position: absolute"][style*="left: 0"][style*="top: 50%"] > button {
      display: none !important;
    }

  </style>
"""

# ─────────────────────────────────────────────────────────────────
# JS INJECTION – Extra runtime polish
# ─────────────────────────────────────────────────────────────────
PRO_JS = r"""
  <!-- ═══ BHU LOKA – Runtime UI Polish ═══ -->
  <script id="bhu-pro-ui-runtime">
  (function() {
    'use strict';

    // ── Ensure cursor always visible ──
    var styleEl = document.createElement('style');
    styleEl.textContent = '* { cursor: auto !important; } button,a,[role="button"],input,select,label { cursor: pointer !important; } input[type="text"],input[type="number"],textarea { cursor: text !important; }';
    document.head.appendChild(styleEl);

    // ── Hide all stale chevron/nav buttons at runtime ──
    function hideChevrons() {
      document.querySelectorAll('.bhu-nav-chevron, [class*="bhu-nav-chevron"]').forEach(function(el) {
        el.style.display = 'none';
        el.style.visibility = 'hidden';
        el.style.pointerEvents = 'none';
      });
      // Also hide the small dot-indicator vertical strip (3 dots on left of 3D viewport)
      document.querySelectorAll('[class*="rounded-full"][style*="cursor:pointer"]').forEach(function(el) {
        if (el.parentElement && el.parentElement.querySelectorAll('[class*="rounded-full"]').length >= 3) {
          var parent = el.parentElement;
          if (parent.style && (parent.style.position === 'absolute' || window.getComputedStyle(parent).position === 'absolute')) {
            parent.style.display = 'none';
          }
        }
      });
    }

    // ── Auto-dismiss intro overlay after 2s ──
    function autoDismissIntro() {
      var overlay = document.getElementById('bhu-intro-overlay');
      if (overlay) {
        overlay.style.transition = 'opacity 0.4s ease';
        overlay.style.opacity = '0';
        setTimeout(function() { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 420);
      }
    }

    // ── 3D Layer panel: fix toggle thumb position ──
    function fixLayerToggles() {
      document.querySelectorAll('.lp-toggle input').forEach(function(cb) {
        cb.addEventListener('change', function() {
          var thumb = cb.parentElement.querySelector('.lp-toggle-thumb');
          if (thumb) thumb.style.left = cb.checked ? '18px' : '2px';
        });
      });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        hideChevrons();
        setTimeout(autoDismissIntro, 3000);
        fixLayerToggles();
      });
    } else {
      hideChevrons();
      setTimeout(autoDismissIntro, 3000);
      fixLayerToggles();
    }

    // Run again after page settles (some elements are injected late)
    setTimeout(function() {
      hideChevrons();
      fixLayerToggles();
    }, 1500);
    setTimeout(hideChevrons, 4000);

  })();
  </script>
"""

def process_file(path):
    if not os.path.exists(path):
        print(f"  SKIP: {path}")
        return

    shutil.copy2(path, path + ".bak2")

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    orig_len = len(html)

    # Remove any existing pro-ui-v2 or runtime injection to avoid duplicates
    html = re.sub(r'<style id=["\']bhu-pro-ui-v2["\']>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script id=["\']bhu-pro-ui-runtime["\']>.*?</script>', '', html, flags=re.DOTALL)

    # Inject CSS before </head>
    if '</head>' in html:
        html = html.replace('</head>', PRO_CSS + '\n</head>', 1)
        print("  PRO CSS injected")

    # Inject JS before </body>
    if '</body>' in html:
        html = html.replace('</body>', PRO_JS + '\n</body>', 1)
        print("  PRO JS injected")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Size: {orig_len:,} → {len(html):,} bytes")
    print(f"  DONE: {os.path.basename(path)}\n")

if __name__ == '__main__':
    for fp in FILES:
        print(f"\nProcessing: {fp}")
        process_file(fp)
    print("All done.")
