/**
 * BHU LOKA Site Enhancer
 * Applies targeted UI/UX improvements to public/index.html before deployment
 */

const fs = require('fs');
const path = require('path');

const HTML_FILE = path.join(__dirname, 'public', 'index.html');
const DASHBOARD_FILE = path.join(__dirname, 'public', 'bhu_loka_cyber_dashboard.html');

function enhance(filePath) {
  if (!fs.existsSync(filePath)) {
    console.log(`Skipping (not found): ${filePath}`);
    return;
  }

  let html = fs.readFileSync(filePath, 'utf8');
  const original = html;

  // ─────────────────────────────────────────────────────────────────────
  // 1. Inject enhanced 3D Layer Viewer CSS + 3D Layer Panel HTML + JS
  //    if not already present
  // ─────────────────────────────────────────────────────────────────────
  if (!html.includes('id="bhu-3d-layer-panel"')) {

    // A. Inject CSS for the new 3D Layer Panel (before </style> first occurrence)
    const layerPanelCSS = `
    /* ── BHU LOKA 3D LAYER CONTROL PANEL ── */
    #bhu-3d-layer-panel {
      position: fixed;
      bottom: 70px;
      right: 16px;
      width: 240px;
      z-index: 2000;
      background: rgba(8,12,22,0.92);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(45,156,219,0.25);
      border-radius: 12px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06);
      overflow: hidden;
      transition: transform 0.28s cubic-bezier(0.4,0,0.2,1), opacity 0.22s ease;
      transform-origin: bottom right;
    }
    #bhu-3d-layer-panel.lp-hidden {
      transform: scale(0.88) translateY(12px);
      opacity: 0;
      pointer-events: none;
    }
    #bhu-3d-layer-panel .lp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px 8px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    #bhu-3d-layer-panel .lp-title {
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      color: #2d9cdb;
      text-transform: uppercase;
    }
    #bhu-3d-layer-panel .lp-close {
      background: none;
      border: none;
      color: #8fa3bd;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 4px;
      font-size: 14px;
      line-height: 1;
      transition: color 0.15s;
    }
    #bhu-3d-layer-panel .lp-close:hover { color: #f0f4f8; }
    #bhu-3d-layer-panel .lp-body {
      padding: 8px 10px 10px;
      display: flex;
      flex-direction: column;
      gap: 5px;
      max-height: 320px;
      overflow-y: auto;
    }
    #bhu-3d-layer-panel .lp-layer-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 7px;
      cursor: pointer;
      transition: background 0.14s;
      user-select: none;
    }
    #bhu-3d-layer-panel .lp-layer-row:hover { background: rgba(255,255,255,0.055); }
    #bhu-3d-layer-panel .lp-layer-row.active { background: rgba(45,156,219,0.08); }
    #bhu-3d-layer-panel .lp-dot {
      width: 11px; height: 11px;
      border-radius: 50%;
      flex-shrink: 0;
      border: 2px solid rgba(255,255,255,0.18);
      transition: box-shadow 0.2s;
    }
    #bhu-3d-layer-panel .lp-layer-row.active .lp-dot {
      box-shadow: 0 0 7px 2px currentColor;
    }
    #bhu-3d-layer-panel .lp-layer-name {
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 11px;
      color: #c5d4e3;
      flex: 1;
    }
    #bhu-3d-layer-panel .lp-toggle {
      width: 28px; height: 15px;
      border-radius: 8px;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.12);
      position: relative;
      flex-shrink: 0;
      transition: background 0.2s;
    }
    #bhu-3d-layer-panel .lp-toggle::after {
      content: '';
      position: absolute;
      top: 1px; left: 1px;
      width: 11px; height: 11px;
      border-radius: 50%;
      background: #8fa3bd;
      transition: transform 0.2s, background 0.2s;
    }
    #bhu-3d-layer-panel .lp-layer-row.active .lp-toggle {
      background: rgba(45,156,219,0.4);
    }
    #bhu-3d-layer-panel .lp-layer-row.active .lp-toggle::after {
      transform: translateX(13px);
      background: #2d9cdb;
    }
    #bhu-3d-layer-panel .lp-footer {
      padding: 7px 10px 9px;
      border-top: 1px solid rgba(255,255,255,0.07);
      display: flex;
      gap: 6px;
    }
    #bhu-3d-layer-panel .lp-footer button {
      flex: 1;
      font-family: 'Space Grotesk', system-ui, sans-serif;
      font-size: 10px;
      font-weight: 500;
      padding: 5px 0;
      border-radius: 6px;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.05);
      color: #8fa3bd;
      cursor: pointer;
      transition: background 0.14s, color 0.14s;
    }
    #bhu-3d-layer-panel .lp-footer button:hover { background: rgba(45,156,219,0.18); color: #2d9cdb; }

    /* ── 3D LAYER TOGGLE BUTTON (FAB) ── */
    #btn-3d-layer-toggle {
      position: fixed;
      bottom: 20px;
      right: 16px;
      width: 42px; height: 42px;
      border-radius: 50%;
      background: rgba(8,12,22,0.92);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(45,156,219,0.4);
      color: #2d9cdb;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 2001;
      box-shadow: 0 4px 20px rgba(45,156,219,0.25);
      transition: transform 0.18s, box-shadow 0.18s, background 0.15s;
    }
    #btn-3d-layer-toggle:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(45,156,219,0.4);
      background: rgba(45,156,219,0.15);
    }

    /* ── MOBILE BOTTOM NAV ENHANCEMENTS ── */
    @media (max-width: 767px) {
      #bhu-3d-layer-panel {
        bottom: 80px;
        right: 10px;
        left: 10px;
        width: auto;
      }
      #btn-3d-layer-toggle {
        bottom: 72px;
        right: 10px;
      }
    }
    `;

    html = html.replace('</style>', layerPanelCSS + '\n  </style>');

    // B. Inject 3D Layer Panel HTML (before </body>)
    const layerPanelHTML = `
  <!-- ── BHU LOKA 3D LAYER CONTROL PANEL ── -->
  <button id="btn-3d-layer-toggle" type="button" title="Toggle 3D Hazard Layer Panel" aria-label="Toggle 3D hazard layer panel" onclick="toggleBhu3DLayerPanel()">
    <i class="fa-solid fa-layer-group"></i>
  </button>

  <div id="bhu-3d-layer-panel" class="lp-hidden" role="dialog" aria-label="3D Layer Controls">
    <div class="lp-header">
      <span class="lp-title"><i class="fa-solid fa-map-pin" style="margin-right:5px;"></i>3D Layers</span>
      <button class="lp-close" onclick="toggleBhu3DLayerPanel()" aria-label="Close layer panel">&times;</button>
    </div>
    <div class="lp-body" id="bhu-3d-layer-body">
      <!-- Layer rows injected by JS -->
    </div>
    <div class="lp-footer">
      <button onclick="setBhu3DLayerAll(true)">Enable All</button>
      <button onclick="setBhu3DLayerAll(false)">Clear All</button>
    </div>
  </div>

  <script>
  /* ── BHU LOKA 3D LAYER MANAGER ── */
  (function() {
    var BHU_LAYERS = [
      { id: 'heat',       label: 'Heat Area',        color: '#ef4444', active: false },
      { id: 'flood',      label: 'Flood Zone',        color: '#3b82f6', active: false },
      { id: 'multihazard',label: 'Multi-Hazard Zone', color: '#f97316', active: false },
      { id: 'safe',       label: 'Safe Zone',         color: '#10b981', active: false },
      { id: 'crime',      label: 'High-Crime Zone',   color: '#a855f7', active: false },
      { id: 'sar',        label: 'SAR / Flood SAR',   color: '#06b6d4', active: false },
      { id: 'dem',        label: 'DEM / Elevation',   color: '#d97706', active: false },
    ];

    function renderLayerRows() {
      var body = document.getElementById('bhu-3d-layer-body');
      if (!body) return;
      body.innerHTML = '';
      BHU_LAYERS.forEach(function(layer) {
        var row = document.createElement('div');
        row.className = 'lp-layer-row' + (layer.active ? ' active' : '');
        row.setAttribute('role', 'button');
        row.setAttribute('tabindex', '0');
        row.setAttribute('aria-label', layer.label + (layer.active ? ' (on)' : ' (off)'));
        row.setAttribute('data-layer-id', layer.id);
        row.innerHTML =
          '<span class="lp-dot" style="background:' + layer.color + ';border-color:' + layer.color + '20"></span>' +
          '<span class="lp-layer-name">' + layer.label + '</span>' +
          '<span class="lp-toggle" aria-hidden="true"></span>';
        row.addEventListener('click', function() { toggleBhu3DLayer(layer.id); });
        row.addEventListener('keydown', function(e) { if (e.key === 'Enter' || e.key === ' ') toggleBhu3DLayer(layer.id); });
        body.appendChild(row);
      });
    }

    window.toggleBhu3DLayer = function(layerId) {
      var layer = BHU_LAYERS.find(function(l) { return l.id === layerId; });
      if (!layer) return;
      layer.active = !layer.active;
      renderLayerRows();
      // Notify the main engine if present
      if (typeof window.setBhuLayerVisibility === 'function') {
        window.setBhuLayerVisibility(layerId, layer.active);
      }
      // Dispatch custom event for other modules to listen
      document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { id: layerId, active: layer.active } }));
    };

    window.setBhu3DLayerAll = function(state) {
      BHU_LAYERS.forEach(function(l) { l.active = state; });
      renderLayerRows();
      BHU_LAYERS.forEach(function(l) {
        if (typeof window.setBhuLayerVisibility === 'function') window.setBhuLayerVisibility(l.id, state);
        document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { id: l.id, active: state } }));
      });
    };

    var _layerPanelOpen = false;
    window.toggleBhu3DLayerPanel = function() {
      _layerPanelOpen = !_layerPanelOpen;
      var panel = document.getElementById('bhu-3d-layer-panel');
      if (panel) panel.classList.toggle('lp-hidden', !_layerPanelOpen);
      var btn = document.getElementById('btn-3d-layer-toggle');
      if (btn) {
        btn.style.background = _layerPanelOpen ? 'rgba(45,156,219,0.22)' : '';
        btn.setAttribute('aria-expanded', _layerPanelOpen ? 'true' : 'false');
      }
    };

    // Render on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderLayerRows);
    } else {
      renderLayerRows();
    }
  })();
  </script>
`;

    html = html.replace('</body>', layerPanelHTML + '\n</body>');
  }

  // ─────────────────────────────────────────────────────────────────────
  // 2. Enhance mobile bottom nav — add Labels to icons
  // ─────────────────────────────────────────────────────────────────────
  // Find the mobile-bottomnav section and ensure labels are visible
  if (html.includes('id="mobile-bottom-nav"') && !html.includes('mobile-nav-label-patch')) {
    const mobileNavCSS = `
    /* ── MOBILE BOTTOM NAV LABEL PATCH ── mobile-nav-label-patch */
    @media (max-width: 767px) {
      #mobile-bottom-nav {
        padding-bottom: env(safe-area-inset-bottom, 4px);
        height: 56px;
      }
      #mobile-bottom-nav button {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        font-size: 9px;
        font-weight: 500;
        color: #8fa3bd;
        min-width: 0;
        flex: 1;
        padding: 4px 2px 2px;
        border: none;
        background: none;
        transition: color 0.15s;
      }
      #mobile-bottom-nav button.active,
      #mobile-bottom-nav button[aria-selected="true"] {
        color: #2d9cdb;
      }
      #mobile-bottom-nav button i {
        font-size: 18px;
      }
      #mobile-bottom-nav button span.nav-lbl {
        display: block;
        font-size: 9px;
        line-height: 1;
      }
    }
    `;
    html = html.replace('</style>', mobileNavCSS + '\n  </style>');
  }

  // ─────────────────────────────────────────────────────────────────────
  // 3. Improve page <title> and meta description for better presence
  // ─────────────────────────────────────────────────────────────────────
  html = html.replace(
    /<title>BHU LOKA.*?<\/title>/,
    '<title>BHU LOKA (भूलोक) · Sovereign AI Geospatial Intelligence Platform</title>'
  );

  if (!html.includes('<meta name="description"')) {
    html = html.replace(
      '<meta name="viewport"',
      '<meta name="description" content="BHU LOKA — India\'s first sovereign dual-agent AI geospatial workstation. Flood SAR, 3D terrain, satellite orbit tracking, precision agriculture, and multi-hazard mapping for India.">\n  <meta name="viewport"'
    );
  }

  // Open Graph tags
  if (!html.includes('og:title')) {
    html = html.replace(
      '</head>',
      `  <!-- Open Graph -->
  <meta property="og:title" content="BHU LOKA (भूलोक) · Sovereign AI Geospatial Platform" />
  <meta property="og:description" content="India's first sovereign dual-agent AI geospatial workstation. Flood SAR, 3D terrain, satellite orbit tracking and multi-hazard mapping." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bhu-loka.web.app/" />
  <meta name="theme-color" content="#040710" />
</head>`
    );
  }

  // ─────────────────────────────────────────────────────────────────────
  // 4. Add skip-to-content link for accessibility
  // ─────────────────────────────────────────────────────────────────────
  if (!html.includes('id="skip-to-main"')) {
    const skipLink = `<a id="skip-to-main" href="#workstation-main" class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[99999] focus:px-3 focus:py-1.5 focus:bg-sky-600 focus:text-white focus:rounded focus:text-sm">Skip to main content</a>\n`;
    html = html.replace('<body', skipLink + '<body');
  }

  // ─────────────────────────────────────────────────────────────────────
  // 5. Remove any remaining stray emojis from text nodes
  // ─────────────────────────────────────────────────────────────────────
  html = html.replace(/[\u{1F300}-\u{1FAFF}]/gu, '');
  html = html.replace(/[\u{2600}-\u{27BF}]/gu, '');

  // ─────────────────────────────────────────────────────────────────────
  // 6. Write back only if changed
  // ─────────────────────────────────────────────────────────────────────
  if (html !== original) {
    fs.writeFileSync(filePath, html, 'utf8');
    console.log(`Enhanced: ${path.basename(filePath)}`);
  } else {
    console.log(`No changes needed: ${path.basename(filePath)}`);
  }
}

enhance(HTML_FILE);
enhance(DASHBOARD_FILE);
console.log('Done.');
