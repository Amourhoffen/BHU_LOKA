const fs = require('fs');
const path = require('path');

const targetFiles = [
  path.join(__dirname, 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'index.html'),
  path.join(__dirname, 'index.html')
];

targetFiles.forEach(file => {
  if (!fs.existsSync(file)) {
    console.log('Skipping missing file:', file);
    return;
  }

  let html = fs.readFileSync(file, 'utf8');

  // 1. FIX CURSOR: Remove "* { cursor: none !important; }" and restore OS mouse pointer everywhere
  html = html.replace(/\*\s*\{\s*cursor\s*:\s*none\s*!important;\s*\}/g, '* { cursor: auto; }');
  html = html.replace(/#bhu-cursor-dot\s*\{[^}]*\}/g, '#bhu-cursor-dot { display: none !important; }');
  html = html.replace(/#bhu-cursor-ring\s*\{[^}]*\}/g, '#bhu-cursor-ring { display: none !important; }');

  // Add explicit fullscreen cursor rules
  const cursorFixCSS = `
    /* ── RESTORE MOUSE CURSOR IN FULLSCREEN & NORMAL MODES ── */
    * { cursor: auto !important; }
    button, a, input, select, [role="button"], summary, .cursor-pointer { cursor: pointer !important; }
    #three-canvas-wrap, canvas { cursor: grab !important; }
    #three-canvas-wrap:active, canvas:active { cursor: grabbing !important; }
    #bhu-cursor-dot, #bhu-cursor-ring { display: none !important; pointer-events: none !important; }
    
    #viewport-panel:fullscreen,
    #viewport-panel:fullscreen *,
    #viewport-panel:-webkit-full-screen,
    #viewport-panel:-webkit-full-screen * {
      cursor: auto !important;
    }
    #viewport-panel:fullscreen button,
    #viewport-panel:fullscreen a,
    #viewport-panel:fullscreen input,
    #viewport-panel:fullscreen select,
    #viewport-panel:-webkit-full-screen button,
    #viewport-panel:-webkit-full-screen a,
    #viewport-panel:-webkit-full-screen input,
    #viewport-panel:-webkit-full-screen select {
      cursor: pointer !important;
    }
    #viewport-panel:fullscreen #three-canvas-wrap,
    #viewport-panel:fullscreen canvas,
    #viewport-panel:-webkit-full-screen #three-canvas-wrap,
    #viewport-panel:-webkit-full-screen canvas {
      cursor: grab !important;
    }
  `;
  if (!html.includes('RESTORE MOUSE CURSOR IN FULLSCREEN')) {
    html = html.replace('</style>', cursorFixCSS + '\n</style>');
  }

  // 2. RED: Remove WebGL2 badge chip
  html = html.replace(/\s*<span[^>]*id="runtime-badge"[^>]*>[\s\S]*?<\/span>/gi, '');

  // 3. RED: Remove NASA PRESENTATION (7 SLIDES) header button
  html = html.replace(/\s*<button[^>]*id="btn-open-presentation-header"[\s\S]*?<\/button>/gi, '');

  // 4. RED: Remove sovereign-quick-dock completely (COMMANDS ^ v bar that overlaps the bottom slider)
  html = html.replace(/\s*<nav[^>]*id="sovereign-quick-dock"[\s\S]*?<\/nav>/gi, '');

  // 5. RED: Remove PASS: satellite observation buttons strip from the bottom time machine
  html = html.replace(/\s*<div[^>]*class="[^"]*hidden\s+xl:flex\s+items-center\s+gap-1\s+mr-3[^"]*"[\s\S]*?bhuSelectSatellitePass[\s\S]*?<\/div>/gi, '');

  // 6. RED: Remove Presentation and extra buttons from Activity Bar
  html = html.replace(/\s*<button[^>]*id="act-btn-presentation"[\s\S]*?<\/button>/gi, '');
  html = html.replace(/\s*<button[^>]*id="act-btn-worker"[\s\S]*?<\/button>/gi, '');

  // 7. YELLOW/OVERLAP: Fix holo-site-analysis-banner - add prominent ✕ Close button
  html = html.replace(
    /(<div id="holo-site-analysis-banner"[\s\S]*?<div class="flex items-center gap-1.5 border-l border-slate-700 pl-2">[\s\S]*?<button type="button" onclick="open2DCropStudio\(\)"[^>]*>RE-CROP<\/button>)([\s\S]*?)(<\/div>\s*<\/div>)/,
    (match, p1, p2, p3) => {
      return p1 + `\n              <button type="button" onclick="document.getElementById('holo-site-analysis-banner').classList.add('hidden')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs ml-1.5 border border-slate-600" title="Close Site Analysis">✕</button>` + p3;
    }
  );

  // 8. YELLOW/OVERLAP: Fix holo-live-tracker-hud (Real-Time GPS Stream) - add prominent ✕ Close button
  if (!html.includes('id="btn-close-gps-stream"')) {
    html = html.replace(
      /(<div id="holo-live-tracker-hud"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>)/,
      `$1\n            <button type="button" id="btn-close-gps-stream" onclick="document.getElementById('holo-live-tracker-hud').classList.add('hidden')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs" title="Close GPS HUD">✕</button>`
    );
  }

  // 9. YELLOW/OVERLAP: Fix holo-spectral-legend (3D Spectral & Color Guide) - add prominent ✕ Close button
  if (!html.includes('id="btn-close-spectral-guide"')) {
    html = html.replace(
      /(<div id="holo-spectral-legend"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>)/,
      `$1\n            <button type="button" id="btn-close-spectral-guide" onclick="document.getElementById('holo-spectral-legend').classList.add('hidden')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs" title="Close Color Guide">✕</button>`
    );
  }

  // 10. YELLOW/OVERLAP: Fix bhu-color-decoder-card - make sure its close button is visible & works
  html = html.replace(
    /(<div id="bhu-color-decoder-card"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>[\s\S]*?<button type="button" onclick="toggleColorDecoderCard\(false\)")/,
    `$1 class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs"`
  );

  // 11. PREVENT AUTOMATIC OVERLAPPING: In switchMode, don't force holoLegend & holoHud open at the same time
  html = html.replace(
    /if\s*\(\s*holoLegend\s*\)\s*holoLegend\.classList\.toggle\('hidden',\s*mode\s*!==\s*'hologram'\s*\|\|\s*isMobile\);/g,
    `// Keep hidden by default to prevent overlapping, open only via user button
      if (holoLegend && !holoLegend.dataset.userOpened) holoLegend.classList.add('hidden');`
  );
  html = html.replace(
    /if\s*\(\s*holoHud\s*\)\s*holoHud\.classList\.toggle\('hidden',\s*mode\s*!==\s*'hologram'\s*\|\|\s*isMobile[^)]*\);/g,
    `// Keep hidden by default to prevent overlapping, open only via user button
      if (holoHud && !holoHud.dataset.userOpened) holoHud.classList.add('hidden');`
  );

  // 12. GREEN: Left Panel Tabs - Ensure AI Assistant, Insights, Vitals switch correctly
  const tabStyles = `
    /* ── LEFT DOCK TABS STYLING ── */
    #left-dock-tabs {
      background: rgba(8, 12, 22, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 4px 6px;
    }
    #left-dock-tabs [role="tab"] {
      font-size: 11px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 6px;
      color: #94a3b8;
      background: transparent;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    #left-dock-tabs [role="tab"]:hover {
      color: #f1f5f9;
      background: rgba(255, 255, 255, 0.06);
    }
    #left-dock-tabs [role="tab"][aria-selected="true"],
    #left-dock-tabs [role="tab"].active {
      color: #38bdf8 !important;
      background: rgba(56, 189, 248, 0.15) !important;
      border-color: rgba(56, 189, 248, 0.35) !important;
    }
  `;
  if (!html.includes('LEFT DOCK TABS STYLING')) {
    html = html.replace('</style>', tabStyles + '\n</style>');
  }

  // 13. GREEN: 3D Layers FAB Control Panel (if missing)
  if (!html.includes('id="bhu-3d-layer-panel"')) {
    const layerFabHTML = `
  <!-- ── BHU LOKA 3D LAYER CONTROL PANEL ── -->
  <button id="btn-3d-layer-toggle" type="button" title="Toggle 3D Hazard Layer Panel" aria-label="Toggle 3D hazard layer panel" onclick="toggleBhu3DLayerPanel()" style="position:fixed;bottom:20px;right:16px;width:42px;height:42px;border-radius:50%;background:rgba(8,12,22,0.92);backdrop-filter:blur(16px);border:1px solid rgba(45,156,219,0.4);color:#2d9cdb;font-size:15px;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2001;box-shadow:0 4px 20px rgba(45,156,219,0.25);">
    <i class="fa-solid fa-layer-group"></i>
  </button>

  <div id="bhu-3d-layer-panel" class="lp-hidden" role="dialog" aria-label="3D Layer Controls" style="position:fixed;bottom:70px;right:16px;width:240px;z-index:2000;background:rgba(8,12,22,0.95);backdrop-filter:blur(20px);border:1px solid rgba(45,156,219,0.3);border-radius:12px;box-shadow:0 16px 48px rgba(0,0,0,0.7);overflow:hidden;transition:transform 0.28s, opacity 0.22s;transform-origin:bottom right;">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px 8px;border-bottom:1px solid rgba(255,255,255,0.08);">
      <span style="font-size:11px;font-weight:600;letter-spacing:0.08em;color:#2d9cdb;text-transform:uppercase;"><i class="fa-solid fa-map-pin" style="margin-right:5px;"></i>3D Layers</span>
      <button onclick="toggleBhu3DLayerPanel()" style="background:none;border:none;color:#8fa3bd;cursor:pointer;padding:2px 4px;font-size:15px;line-height:1;">✕</button>
    </div>
    <div id="bhu-3d-layer-body" style="padding:8px 10px 10px;display:flex;flex-direction:column;gap:5px;max-height:320px;overflow-y:auto;">
    </div>
    <div style="padding:7px 10px 9px;border-top:1px solid rgba(255,255,255,0.08);display:flex;gap:6px;">
      <button onclick="setBhu3DLayerAll(true)" style="flex:1;font-size:10px;font-weight:600;padding:5px 0;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);color:#8fa3bd;cursor:pointer;">Enable All</button>
      <button onclick="setBhu3DLayerAll(false)" style="flex:1;font-size:10px;font-weight:600;padding:5px 0;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);color:#8fa3bd;cursor:pointer;">Clear All</button>
    </div>
  </div>

  <script>
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
        row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:7px;cursor:pointer;user-select:none;background:' + (layer.active ? 'rgba(45,156,219,0.12)' : 'transparent');
        row.innerHTML =
          '<span style="width:11px;height:11px;border-radius:50%;flex-shrink:0;background:' + layer.color + ';box-shadow:' + (layer.active ? '0 0 8px ' + layer.color : 'none') + '"></span>' +
          '<span style="font-size:11px;color:#c5d4e3;flex:1;">' + layer.label + '</span>' +
          '<span style="font-size:10px;font-weight:bold;color:' + (layer.active ? '#38bdf8' : '#64748b') + '">' + (layer.active ? 'ON' : 'OFF') + '</span>';
        row.addEventListener('click', function() {
          layer.active = !layer.active;
          renderLayerRows();
          if (typeof window.setBhuLayerVisibility === 'function') window.setBhuLayerVisibility(layer.id, layer.active);
          document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { id: layer.id, active: layer.active } }));
        });
        body.appendChild(row);
      });
    }

    window.setBhu3DLayerAll = function(state) {
      BHU_LAYERS.forEach(function(l) { l.active = state; });
      renderLayerRows();
      BHU_LAYERS.forEach(function(l) {
        if (typeof window.setBhuLayerVisibility === 'function') window.setBhuLayerVisibility(l.id, state);
        document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { id: l.id, active: state } }));
      });
    };

    var _lpOpen = false;
    window.toggleBhu3DLayerPanel = function() {
      _lpOpen = !_lpOpen;
      var panel = document.getElementById('bhu-3d-layer-panel');
      if (panel) {
        panel.style.display = _lpOpen ? 'block' : 'none';
      }
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderLayerRows);
    } else {
      renderLayerRows();
    }
  })();
  </script>
    `;
    html = html.replace('</body>', layerFabHTML + '\n</body>');
  }

  // 14. Add Master Tab Switcher Logic
  if (!html.includes('MASTER_TAB_SWITCHER_LOGIC')) {
    const tabLogic = `
  <script>
  /* MASTER_TAB_SWITCHER_LOGIC */
  window.switchLeftDockTab = function(tabName) {
    const aiView = document.getElementById('left-ai-view');
    const vitalsView = document.getElementById('left-health-vitals');
    const insightsView = document.getElementById('left-insights-view');

    document.querySelectorAll('#left-dock-tabs [role="tab"]').forEach(btn => {
      btn.setAttribute('aria-selected', 'false');
      btn.classList.remove('active');
    });

    if (aiView) { aiView.style.display = 'none'; aiView.classList.add('hidden'); }
    if (vitalsView) { vitalsView.style.display = 'none'; vitalsView.classList.add('hidden'); }
    if (insightsView) { insightsView.style.display = 'none'; insightsView.classList.add('hidden'); }

    if (tabName === 'ai') {
      const btn = document.getElementById('left-tab-btn-ai');
      if (btn) { btn.setAttribute('aria-selected', 'true'); btn.classList.add('active'); }
      if (aiView) { aiView.style.display = 'flex'; aiView.classList.remove('hidden'); }
    } else if (tabName === 'vitals') {
      const btn = document.getElementById('left-tab-btn-vitals');
      if (btn) { btn.setAttribute('aria-selected', 'true'); btn.classList.add('active'); }
      if (vitalsView) { vitalsView.style.display = 'flex'; vitalsView.classList.remove('hidden'); }
    } else if (tabName === 'insights') {
      const btn = document.getElementById('left-tab-btn-insights');
      if (btn) { btn.setAttribute('aria-selected', 'true'); btn.classList.add('active'); }
      if (insightsView) { insightsView.style.display = 'flex'; insightsView.classList.remove('hidden'); }
    }
  };

  document.addEventListener('DOMContentLoaded', function() {
    const tabAi = document.getElementById('left-tab-btn-ai');
    const tabVitals = document.getElementById('left-tab-btn-vitals');
    const tabInsights = document.getElementById('left-tab-btn-insights');
    if (tabAi) tabAi.onclick = function() { window.switchLeftDockTab('ai'); };
    if (tabVitals) tabVitals.onclick = function() { window.switchLeftDockTab('vitals'); };
    if (tabInsights) tabInsights.onclick = function() { window.switchLeftDockTab('insights'); };
  });
  </script>
    `;
    html = html.replace('</body>', tabLogic + '\n</body>');
  }

  fs.writeFileSync(file, html, 'utf8');
  console.log('Successfully updated:', path.basename(file), 'at', file);
});

console.log('ALL FILES UPDATED!');
