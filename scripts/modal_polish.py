#!/usr/bin/env python3
"""
BHU LOKA – Modal & Specific Element Polish
===========================================
Targeted fixes for:
  1. Scientific Flood Model modal – header, tabs, cards
  2. Area Flood Prediction modal – header, inputs, results
  3. Bottom-left vertical chevron dot strip – hide
  4. AI Assistant left panel – role tabs, agent cards
  5. Top nav second-row (World / India 36 tabs) – tighter
"""

import re, os, shutil

BASE = r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"
FILES = [
    os.path.join(BASE, "public", "index.html"),
    os.path.join(BASE, "bhu_loka_cyber_dashboard.html"),
]

MODAL_CSS = r"""
  <!-- ═══ BHU LOKA – Modal & Panel Targeted Polish ═══ -->
  <style id="bhu-modal-polish">

    /* ══ Scientific Flood Model Modal ══ */
    #bhu-model-intel-modal > div {
      border-color: rgba(6,182,212,0.25) !important;
      border-radius: 18px !important;
      box-shadow: 0 40px 100px rgba(0,0,0,0.9), 0 0 0 1px rgba(6,182,212,0.08), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    }
    #bhu-model-intel-modal .px-4.py-2\.5.bg-\[#090e18\] {
      background: rgba(5,8,18,0.98) !important;
      border-bottom: 1px solid rgba(255,255,255,0.07) !important;
      padding: 14px 20px !important;
    }

    /* Modal tab bar */
    #bhu-model-intel-modal [role="tablist"],
    #bhu-model-intel-modal .flex.border-b {
      background: rgba(3,5,12,0.9) !important;
      border-bottom: 1px solid rgba(255,255,255,0.06) !important;
      padding: 0 16px !important;
      gap: 2px !important;
      flex-wrap: nowrap !important;
      overflow-x: auto !important;
    }
    #bhu-model-intel-modal [role="tab"],
    #bhu-model-intel-modal .tab-btn {
      font-size: 10px !important;
      font-weight: 600 !important;
      letter-spacing: 0.04em !important;
      padding: 8px 12px !important;
      border-radius: 0 !important;
      border-bottom: 2px solid transparent !important;
      white-space: nowrap !important;
      transition: all 0.14s !important;
      color: rgba(100,116,139,0.9) !important;
      background: transparent !important;
    }
    #bhu-model-intel-modal [role="tab"]:hover {
      color: rgba(226,232,240,0.85) !important;
      background: rgba(255,255,255,0.03) !important;
    }
    #bhu-model-intel-modal [role="tab"].active,
    #bhu-model-intel-modal [role="tab"][aria-selected="true"] {
      color: rgb(103,232,249) !important;
      border-bottom-color: rgb(6,182,212) !important;
    }

    /* Modal body content area */
    #bhu-model-intel-modal .flex-1 {
      background: rgba(4,7,16,0.6) !important;
    }

    /* ══ Area Flood Prediction Modal ══ */
    #bhu-area-predict-modal > div {
      border-color: rgba(251,191,36,0.2) !important;
      border-radius: 18px !important;
      box-shadow: 0 40px 100px rgba(0,0,0,0.9), 0 0 0 1px rgba(251,191,36,0.06), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    }
    #bhu-area-predict-modal .px-4.py-2\.5 {
      padding: 14px 20px !important;
      background: rgba(5,8,18,0.98) !important;
      border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    }

    /* Preset locality chips in area flood modal */
    #bhu-area-predict-modal button[onclick*="preset"],
    #bhu-area-predict-modal button[onclick*="Preset"],
    #bhu-area-predict-modal .preset-btn {
      font-size: 10px !important;
      font-weight: 600 !important;
      letter-spacing: 0.03em !important;
      border-radius: 7px !important;
      padding: 5px 10px !important;
      transition: all 0.14s !important;
    }

    /* Result big numbers in flood modal */
    #bhu-area-predict-modal [id*="result"],
    #bhu-area-predict-modal [id*="prob"],
    #bhu-area-predict-modal [class*="text-5xl"],
    #bhu-area-predict-modal [class*="text-4xl"] {
      font-family: 'Space Grotesk', system-ui, sans-serif !important;
      font-weight: 800 !important;
      letter-spacing: -0.03em !important;
    }

    /* "RUN SPATIAL RANDOM FOREST" button */
    #bhu-area-predict-modal button[onclick*="runAreaFlood"],
    #bhu-area-predict-modal button[onclick*="runModel"],
    #bhu-area-predict-modal #btn-run-sbcv,
    #bhu-area-predict-modal button[class*="bg-amber"],
    #bhu-area-predict-modal button[class*="from-amber"] {
      height: 44px !important;
      border-radius: 10px !important;
      font-size: 11.5px !important;
      font-weight: 800 !important;
      letter-spacing: 0.08em !important;
      transition: all 0.18s cubic-bezier(0.34,1.56,0.64,1) !important;
    }
    #bhu-area-predict-modal button[onclick*="runAreaFlood"]:hover,
    #bhu-area-predict-modal button[onclick*="runModel"]:hover {
      transform: translateY(-2px) scale(1.01) !important;
      filter: brightness(1.08) !important;
    }

    /* "RUN MODEL INFERENCE" in scientific modal */
    #bhu-model-intel-modal button[onclick*="runInference"],
    #bhu-model-intel-modal button[onclick*="runModel"],
    #bhu-model-intel-modal #btn-run-inference {
      height: 42px !important;
      border-radius: 10px !important;
      font-size: 11px !important;
      font-weight: 800 !important;
      letter-spacing: 0.07em !important;
    }

    /* ══ Left AI Panel ══ */
    /* Role selector tabs (Farmer / Business / Student / Work) */
    #left-rail button[onclick*="setRole"],
    #left-rail button[onclick*="switchRole"],
    .role-btn, [class*="role-tab"] {
      font-size: 10.5px !important;
      font-weight: 700 !important;
      letter-spacing: 0.04em !important;
      border-radius: 7px !important;
      padding: 5px 12px !important;
      transition: all 0.14s !important;
    }

    /* AI input area */
    #left-rail textarea,
    #left-rail input[type="text"] {
      background: rgba(0,0,0,0.5) !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      border-radius: 10px !important;
      font-size: 12px !important;
      resize: none !important;
      transition: border-color 0.14s, box-shadow 0.14s !important;
    }
    #left-rail textarea:focus,
    #left-rail input[type="text"]:focus {
      border-color: rgba(6,182,212,0.4) !important;
      box-shadow: 0 0 0 3px rgba(6,182,212,0.1) !important;
    }

    /* RUN button in AI panel */
    #left-rail button[id*="run"],
    #left-rail button[onclick*="run"],
    #left-rail .btn-run {
      font-size: 11px !important;
      font-weight: 800 !important;
      letter-spacing: 0.08em !important;
      border-radius: 8px !important;
      transition: all 0.16s cubic-bezier(0.34,1.56,0.64,1) !important;
    }
    #left-rail button[id*="run"]:hover {
      transform: scale(1.03) !important;
      filter: brightness(1.1) !important;
    }

    /* ══ Second row nav tabs (World / India 36 / Bihar 38 / etc.) ══ */
    #bhu-view-tabs,
    [id*="view-tabs"],
    .bhu-tabs-row {
      gap: 1px !important;
      padding: 2px 8px !important;
    }
    #bhu-view-tabs button,
    [id*="view-tabs"] button {
      font-size: 10px !important;
      font-weight: 600 !important;
      letter-spacing: 0.04em !important;
      padding: 3px 9px !important;
      border-radius: 5px !important;
      height: 24px !important;
      white-space: nowrap !important;
      transition: all 0.12s !important;
    }

    /* ══ Left vertical dot-menu strip (3 dots on 3D map left edge) ══ */
    /* This appears as a small absolute-positioned div with 3 vertical dots */
    div[style*="position:absolute"][style*="left:0"],
    div[style*="position: absolute"][style*="left: 0"] {
      /* Only hide if it's the dot strip, not content panels */
    }

    /* Directly target the grey vertical dot strip */
    .bhu-left-dot-strip,
    #bhu-left-dot-strip,
    [id*="dot-strip"],
    [class*="dot-strip"] {
      display: none !important;
    }

    /* ══ Intro Overlay – professional ══ */
    #bhu-intro-overlay {
      background: radial-gradient(ellipse at center, rgba(4,8,22,0.98) 0%, rgba(2,4,12,1) 100%) !important;
    }

    /* ══ Exponent/feature importance values in modal ══ */
    #bhu-model-intel-modal .text-cyan-400,
    #bhu-model-intel-modal [class*="text-cyan"] {
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 11.5px !important;
    }

    /* ══ SHAP/XAI contribution bar in flood modal ══ */
    #bhu-area-predict-modal [class*="bg-cyan"],
    #bhu-area-predict-modal [class*="bg-emerald"] {
      border-radius: 3px !important;
    }

    /* ══ General modal section dividers ══ */
    #bhu-model-intel-modal hr,
    #bhu-area-predict-modal hr {
      border-color: rgba(255,255,255,0.06) !important;
      margin: 10px 0 !important;
    }

    /* ══ Scientific modal performance cards ══ */
    #bhu-model-intel-modal [class*="bg-\[#"], 
    #bhu-model-intel-modal [class*="bg-slate"] {
      border-radius: 10px !important;
    }

    /* ══ Tooltip / hover-cards ══ */
    [class*="tooltip"],
    [data-tooltip] {
      border-radius: 8px !important;
      font-size: 11px !important;
      backdrop-filter: blur(12px) !important;
    }

    /* ══ View-on-3D-terrain / export buttons in modals ══ */
    #bhu-area-predict-modal button[onclick*="viewOn3D"],
    #bhu-area-predict-modal button[onclick*="export"],
    #bhu-area-predict-modal button[onclick*="Export"] {
      border-radius: 9px !important;
      font-size: 10.5px !important;
      font-weight: 700 !important;
      letter-spacing: 0.05em !important;
      transition: all 0.14s !important;
    }

  </style>
"""

def process_file(path):
    if not os.path.exists(path):
        print(f"  SKIP: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    orig_len = len(html)

    # Remove existing to avoid duplicates
    html = re.sub(r'<style id=["\']bhu-modal-polish["\']>.*?</style>', '', html, flags=re.DOTALL)

    if '</head>' in html:
        html = html.replace('</head>', MODAL_CSS + '\n</head>', 1)
        print("  Modal polish CSS injected")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Size: {orig_len:,} → {len(html):,} bytes  |  DONE: {os.path.basename(path)}\n")

if __name__ == '__main__':
    for fp in FILES:
        print(f"Processing: {fp}")
        process_file(fp)
    print("All done.")
