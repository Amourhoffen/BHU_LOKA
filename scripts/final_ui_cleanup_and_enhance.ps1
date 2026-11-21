
# ═══════════════════════════════════════════════════════════════════
# BHU LOKA – Final UI Cleanup & 3D Layer Enhancement Script
# ═══════════════════════════════════════════════════════════════════
# Actions:
#   1. Remove bell/gear/PK avatar buttons from top-right header
#   2. Remove left-side chevron overlay buttons (any remaining HTML)
#   3. Remove old COMMANDS floating dock (if present)
#   4. Enhance 3D Layers panel with Apple/ISO glassmorphic design
#   5. Apply to both public/index.html and bhu_loka_cyber_dashboard.html
# ═══════════════════════════════════════════════════════════════════

$files = @(
    "public\index.html",
    "bhu_loka_cyber_dashboard.html"
)

foreach ($file in $files) {
    if (-not (Test-Path $file)) { Write-Host "SKIP (not found): $file"; continue }

    $content = Get-Content $file -Raw -Encoding UTF8

    # ── 1. REMOVE BELL/GEAR/PK AVATAR SECTION ──────────────────────
    # Remove the entire right controls block: from btn-api-chip through the PK div closing </div></div>
    # Pattern: button#btn-api-chip ... through closing div of the user section
    $content = $content -replace '(?s)<button[^>]+id="btn-api-chip"[^>]*>.*?</button>\s*', ''
    # Remove the gear/settings button (toggleHeroMap)
    $content = $content -replace '(?s)<button[^>]+onclick="toggleHeroMap\(\)"[^>]*>.*?</button>\s*', ''
    # Remove PK avatar section (the div with gradient ring + initials PK)
    $content = $content -replace '(?s)<div class="flex items-center gap-1\.5 pl-2 border-l[^"]*">\s*<div class="w-7 h-7 rounded-full[^"]*">[^<]*<div[^>]*>[^<]*PK[^<]*</div>\s*</div>\s*<div[^>]*>[^<]*Prince Kumar[^<]*(?:\n.*?)*?</div>\s*</div>\s*</div>', ''

    # ── 2. REMOVE any remaining bhu-nav-chevron HTML elements ───────
    $content = $content -replace '(?s)<button[^>]+class="[^"]*bhu-nav-chevron[^"]*"[^>]*>.*?</button>', ''

    # ── 3. REMOVE old COMMANDS floating dock (if present) ───────────
    $content = $content -replace '(?s)<!-- SOVEREIGN FLOATING WORKSPACE COMMAND DOCK.*?-->\s*\n\s*\n', ''

    # ── 4. REPLACE 3D LAYER PANEL with enhanced Apple/ISO design ────
    # First remove old panel + button if present
    $content = $content -replace '(?s)<!-- ── BHU LOKA 3D LAYER CONTROL PANEL ── -->.*?<!-- ── ENHANCED HIGH-VISIBILITY 3D HAZARD FILTERS BUTTON ── -->\s*<button[^>]+id="btn-3d-layer-toggle"[^>]*>.*?</button>\s*\n\s*<div[^>]+id="bhu-3d-layer-panel"[^>]*>.*?</div>\s*\n', '<!-- 3D_LAYERS_PLACEHOLDER -->'

    # Also try simpler pattern if the above didn't match
    if ($content -notmatch '3D_LAYERS_PLACEHOLDER') {
        $content = $content -replace '(?s)<button[^>]+id="btn-3d-layer-toggle"[^>]*>.*?</button>', '<!-- 3D_BTN_PLACEHOLDER -->'
        $content = $content -replace '(?s)<div[^>]+id="bhu-3d-layer-panel"[^>]*>.*?(?=\n\s*<!--|\n\s*<script|\n\s*<div id="bhu-presentation)', '<!-- 3D_PANEL_PLACEHOLDER -->'
    }

    # ── 5. INJECT enhanced Apple/ISO 3D LAYER SYSTEM CSS ─────────────
    $enhancedCSS = @'
  <!-- ═══ BHU LOKA 3D HAZARD LAYER SYSTEM – Apple/ISO Design ═══ -->
  <style>
    /* ── Layer FAB Button ── */
    #bhu-3d-fab {
      position: fixed;
      bottom: 68px;
      right: 20px;
      z-index: 2200;
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 0 18px 0 14px;
      height: 40px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(2,132,199,0.95) 0%, rgba(6,182,212,0.95) 50%, rgba(16,185,129,0.9) 100%);
      color: #fff;
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-weight: 700;
      font-size: 11.5px;
      letter-spacing: 0.06em;
      border: 1.5px solid rgba(255,255,255,0.35);
      box-shadow: 0 0 24px rgba(6,182,212,0.55), 0 4px 16px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.3);
      cursor: pointer;
      transition: transform 0.18s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.18s ease, opacity 0.18s ease;
      user-select: none;
      -webkit-user-select: none;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }
    #bhu-3d-fab:hover {
      transform: scale(1.06) translateY(-1px);
      box-shadow: 0 0 32px rgba(6,182,212,0.8), 0 8px 24px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.3);
    }
    #bhu-3d-fab:active {
      transform: scale(0.97);
    }
    #bhu-3d-fab .fab-icon {
      width: 18px;
      height: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255,255,255,0.18);
      border-radius: 6px;
      flex-shrink: 0;
    }
    #bhu-3d-fab .fab-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 0 8px rgba(255,255,255,0.9);
      flex-shrink: 0;
      animation: fab-pulse 2.4s ease-in-out infinite;
    }
    @keyframes fab-pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.65; transform: scale(0.85); }
    }

    /* ── Layer Panel ── */
    #bhu-3d-panel {
      position: fixed;
      bottom: 118px;
      right: 20px;
      z-index: 2199;
      width: 230px;
      background: rgba(6, 10, 22, 0.88);
      backdrop-filter: blur(28px) saturate(180%);
      -webkit-backdrop-filter: blur(28px) saturate(180%);
      border: 1px solid rgba(255,255,255,0.13);
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.75), 0 0 0 0.5px rgba(255,255,255,0.06), inset 0 1px 0 rgba(255,255,255,0.08);
      overflow: hidden;
      transform-origin: bottom right;
      transition: transform 0.28s cubic-bezier(0.34,1.56,0.64,1), opacity 0.22s ease;
    }
    #bhu-3d-panel.lp-hidden {
      transform: scale(0.85) translateY(10px);
      opacity: 0;
      pointer-events: none;
    }
    .lp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 14px 8px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .lp-title {
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: rgba(255,255,255,0.9);
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .lp-title-icon {
      width: 20px;
      height: 20px;
      border-radius: 6px;
      background: linear-gradient(135deg, rgba(6,182,212,0.4), rgba(16,185,129,0.3));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
    }
    .lp-close {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      color: rgba(255,255,255,0.6);
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      line-height: 1;
    }
    .lp-close:hover {
      background: rgba(239,68,68,0.3);
      color: #fff;
      border-color: rgba(239,68,68,0.5);
    }
    .lp-body {
      padding: 10px 12px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .lp-row {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 7px 10px;
      border-radius: 10px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.055);
      cursor: pointer;
      transition: background 0.14s ease, border-color 0.14s ease, transform 0.1s ease;
      user-select: none;
    }
    .lp-row:hover {
      background: rgba(255,255,255,0.07);
      border-color: rgba(255,255,255,0.12);
      transform: translateX(2px);
    }
    .lp-row.active-layer {
      background: rgba(255,255,255,0.06);
      border-color: rgba(255,255,255,0.14);
    }
    .lp-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
      box-shadow: 0 0 8px currentColor;
    }
    .lp-name {
      flex: 1;
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 11.5px;
      font-weight: 500;
      color: rgba(255,255,255,0.82);
      letter-spacing: 0.01em;
    }
    /* iOS-style toggle */
    .lp-toggle {
      position: relative;
      width: 34px;
      height: 20px;
      flex-shrink: 0;
    }
    .lp-toggle input {
      opacity: 0;
      width: 0;
      height: 0;
      position: absolute;
    }
    .lp-toggle-track {
      position: absolute;
      inset: 0;
      border-radius: 10px;
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.1);
      transition: background 0.22s ease, border-color 0.22s ease;
      cursor: pointer;
    }
    .lp-toggle input:checked + .lp-toggle-track {
      background: rgba(16,185,129,0.85);
      border-color: rgba(16,185,129,0.6);
      box-shadow: 0 0 10px rgba(16,185,129,0.4);
    }
    .lp-toggle-thumb {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      transition: left 0.22s cubic-bezier(0.34,1.56,0.64,1);
      pointer-events: none;
      box-shadow: 0 1px 4px rgba(0,0,0,0.5);
    }
    .lp-toggle input:checked ~ .lp-toggle-thumb {
      left: 16px;
    }
    .lp-footer {
      display: flex;
      gap: 8px;
      padding: 0 12px 12px;
    }
    .lp-btn {
      flex: 1;
      height: 30px;
      border-radius: 8px;
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 10.5px;
      font-weight: 700;
      letter-spacing: 0.06em;
      cursor: pointer;
      border: none;
      transition: opacity 0.15s, transform 0.12s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
    }
    .lp-btn:hover { opacity: 0.85; transform: scale(1.02); }
    .lp-btn:active { transform: scale(0.97); }
    .lp-btn-enable {
      background: linear-gradient(135deg, rgba(2,132,199,0.9), rgba(16,185,129,0.85));
      color: #fff;
    }
    .lp-btn-clear {
      background: rgba(255,255,255,0.08);
      color: rgba(255,255,255,0.65);
      border: 1px solid rgba(255,255,255,0.1);
    }
  </style>
'@

    # ── 6. INJECT enhanced 3D LAYER HTML + JS ────────────────────────
    $enhancedHTML = @'
  <!-- ═══ BHU LOKA 3D HAZARD LAYER FAB + PANEL ═══ -->
  <button id="bhu-3d-fab" aria-label="Toggle 3D Hazard Layers" onclick="toggleBhu3DPanel()" title="3D Hazard Filters">
    <span class="fab-icon"><i class="fa-solid fa-layer-group" style="font-size:11px;"></i></span>
    <span>3D LAYERS</span>
    <span class="fab-dot"></span>
  </button>

  <div id="bhu-3d-panel" class="lp-hidden" role="dialog" aria-label="3D Hazard Layer Controls" aria-modal="false">
    <div class="lp-header">
      <span class="lp-title">
        <span class="lp-title-icon"><i class="fa-solid fa-map" style="color:rgba(6,182,212,0.9);font-size:9px;"></i></span>
        3D LAYERS
      </span>
      <button class="lp-close" onclick="toggleBhu3DPanel()" aria-label="Close">&times;</button>
    </div>
    <div class="lp-body" id="bhu-3d-layer-body">
      <!-- Layer rows injected by JS -->
    </div>
    <div class="lp-footer">
      <button class="lp-btn lp-btn-enable" onclick="bhuEnableAllLayers()" aria-label="Enable all layers">
        <i class="fa-solid fa-eye" style="font-size:10px;"></i> ALL ON
      </button>
      <button class="lp-btn lp-btn-clear" onclick="bhuClearAllLayers()" aria-label="Clear all layers">
        <i class="fa-solid fa-eye-slash" style="font-size:10px;"></i> CLEAR
      </button>
    </div>
  </div>

  <script>
    (function () {
      'use strict';

      var BHU_LAYERS = [
        { id: 'heat',       label: 'Heat Area',       color: '#f97316', key: 'heatMesh'          },
        { id: 'flood',      label: 'Flood Zone',      color: '#38bdf8', key: 'terrainFloodMesh'   },
        { id: 'multihazard',label: 'Multi-Hazard',    color: '#a855f7', key: 'multiHazardGroup'   },
        { id: 'safezone',   label: 'Safe Zone',       color: '#10b981', key: 'safeZoneGroup'      },
        { id: 'crime',      label: 'High Crime Zone', color: '#ef4444', key: 'crimeZoneGroup'      },
        { id: 'sar',        label: 'SAR / Flood SAR', color: '#facc15', key: 'indiaLstGroup'       },
        { id: 'dem',        label: 'DEM / Elevation', color: '#94a3b8', key: 'demGroup'            }
      ];

      var _panelOpen = false;

      window.toggleBhu3DPanel = function () {
        var panel = document.getElementById('bhu-3d-panel');
        if (!panel) return;
        _panelOpen = !_panelOpen;
        if (_panelOpen) {
          panel.classList.remove('lp-hidden');
          _buildLayerRows();
        } else {
          panel.classList.add('lp-hidden');
        }
      };

      function _buildLayerRows() {
        var body = document.getElementById('bhu-3d-layer-body');
        if (!body || body.dataset.built === '1') return;
        body.dataset.built = '1';
        body.innerHTML = '';
        BHU_LAYERS.forEach(function (layer) {
          var row = document.createElement('div');
          row.className = 'lp-row';
          row.setAttribute('role', 'button');
          row.setAttribute('tabindex', '0');
          row.setAttribute('aria-label', 'Toggle ' + layer.label);
          row.innerHTML = '<span class="lp-dot" style="background:' + layer.color + ';box-shadow:0 0 8px ' + layer.color + ';"></span>' +
            '<span class="lp-name">' + layer.label + '</span>' +
            '<label class="lp-toggle" onclick="event.stopPropagation()" aria-label="Toggle ' + layer.label + '">' +
            '  <input type="checkbox" id="lt-' + layer.id + '" onchange="bhuSetLayer(\'' + layer.id + '\',this.checked)">' +
            '  <span class="lp-toggle-track"></span>' +
            '  <span class="lp-toggle-thumb"></span>' +
            '</label>';
          row.addEventListener('click', function () {
            var cb = document.getElementById('lt-' + layer.id);
            if (cb) { cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); }
          });
          row.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); row.click(); }
          });
          body.appendChild(row);
        });
      }

      window.bhuSetLayer = function (id, visible) {
        var layer = BHU_LAYERS.find(function (l) { return l.id === id; });
        if (!layer) return;
        // Toggle Three.js object if present
        try {
          var obj = window[layer.key] || (window.scene && window.scene.getObjectByName(layer.key));
          if (obj) obj.visible = visible;
        } catch (e) {}
        // Toggle via existing setBhuLayerVisibility if available
        if (typeof window.setBhuLayerVisibility === 'function') {
          window.setBhuLayerVisibility(id, visible);
        }
        // Fire event for map engine
        document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { layer: id, visible: visible } }));
        // Toast
        if (typeof window.showSovereignToast === 'function') {
          window.showSovereignToast((visible ? '🟢 ' : '⚫ ') + layer.label + ' ' + (visible ? 'ON' : 'OFF'), 'info', 1800);
        }
        // Row visual feedback
        var row = document.querySelector('[aria-label="Toggle ' + layer.label + '"]');
        if (row) row.classList.toggle('active-layer', visible);
      };

      window.bhuEnableAllLayers = function () {
        BHU_LAYERS.forEach(function (l) {
          var cb = document.getElementById('lt-' + l.id);
          if (cb) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
        });
      };

      window.bhuClearAllLayers = function () {
        BHU_LAYERS.forEach(function (l) {
          var cb = document.getElementById('lt-' + l.id);
          if (cb) { cb.checked = false; cb.dispatchEvent(new Event('change')); }
        });
      };

      // Keyboard close on Escape
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && _panelOpen) window.toggleBhu3DPanel();
      });
    })();
  </script>
'@

    # Inject CSS before </head>
    if ($content -match '</head>') {
        $content = $content -replace '</head>', "$enhancedCSS`n</head>"
    }

    # Inject HTML before </body>
    if ($content -match '</body>') {
        # Remove old placeholders
        $content = $content -replace '<!-- 3D_LAYERS_PLACEHOLDER -->', ''
        $content = $content -replace '<!-- 3D_BTN_PLACEHOLDER -->', ''
        $content = $content -replace '<!-- 3D_PANEL_PLACEHOLDER -->', ''
        $content = $content -replace '</body>', "$enhancedHTML`n</body>"
    }

    Set-Content -Path $file -Value $content -Encoding UTF8 -NoNewline
    Write-Host "DONE: $file"
}

Write-Host "`nAll files updated. Ready for deploy."
