const fs = require('fs');
const path = require('path');

const files = [
  path.join(__dirname, 'public', 'index.html'),
  path.join(__dirname, 'public', 'bhu_loka_cyber_dashboard.html')
];

files.forEach(filePath => {
  if (!fs.existsSync(filePath)) {
    console.log('Not found:', filePath);
    return;
  }
  let html = fs.readFileSync(filePath, 'utf8');

  // 1. RED: Remove WebGL2 badge chip
  html = html.replace(/<span[^>]*id="runtime-badge"[^>]*>[\s\S]*?<\/span>/gi, '');

  // 2. RED: Remove NASA PRESENTATION (7 SLIDES) from header
  html = html.replace(/<button[^>]*id="btn-open-presentation-header"[\s\S]*?<\/button>/gi, '');

  // 3. RED: Remove sovereign-quick-dock completely (COMMANDS ^ v floating bar with pills)
  html = html.replace(/<nav[^>]*id="sovereign-quick-dock"[\s\S]*?<\/nav>/gi, '');

  // 4. RED: Remove PASS: satellite observation strip from the bottom time machine
  html = html.replace(/<div[^>]*class="[^"]*hidden\s+xl:flex\s+items-center\s+gap-1\s+mr-3[^"]*"[\s\S]*?bhuSelectSatellitePass[\s\S]*?<\/div>/gi, '');

  // 5. RED: Remove Presentation button & Health/Worker button from Activity Bar if present
  html = html.replace(/<button[^>]*id="act-btn-presentation"[\s\S]*?<\/button>/gi, '');
  html = html.replace(/<button[^>]*id="act-btn-worker"[\s\S]*?<\/button>/gi, '');

  // 6. YELLOW/OVERLAP: Add explicit ✕ close button to holo-site-analysis-banner
  html = html.replace(
    /(<div id="holo-site-analysis-banner"[\s\S]*?RE-CROP<\/button>)([\s\S]*?)(<\/div>\s*<\/div>)/,
    (match, p1, p2, p3) => {
      return p1 + `<button type="button" onclick="document.getElementById('holo-site-analysis-banner').classList.add('hidden')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs ml-1" title="Close Site Analysis">✕</button>` + p3;
    }
  );

  // 7. YELLOW/OVERLAP: Fix holo-live-tracker-hud (Real-Time GPS Stream)
  // Ensure it has a prominent ✕ close button in its header
  if (!html.includes('id="btn-close-gps-hud"')) {
    html = html.replace(
      /(<div id="holo-live-tracker-hud"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>)/,
      `$1\n            <button type="button" id="btn-close-gps-hud" onclick="document.getElementById('holo-live-tracker-hud').classList.add('hidden')" class="text-slate-400 hover:text-white bg-slate-800 px-1.5 py-0.5 rounded font-bold text-xs" title="Close GPS HUD">✕</button>`
    );
  }

  // 8. YELLOW/OVERLAP: Fix holo-spectral-legend (3D Spectral & Color Guide)
  // Ensure it has a working close button
  html = html.replace(
    /(<div id="holo-spectral-legend"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>[\s\S]*?<button type="button" onclick="toggleHoloSpectralLegend\(\)")/,
    `$1 style="display:none"`
  );
  if (!html.includes('id="btn-close-spectral-legend"')) {
    html = html.replace(
      /(<div id="holo-spectral-legend"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>)/,
      `$1\n            <button type="button" id="btn-close-spectral-legend" onclick="document.getElementById('holo-spectral-legend').classList.add('hidden')" class="text-slate-400 hover:text-white bg-slate-800 px-1.5 py-0.5 rounded font-bold text-xs" title="Close Guide">✕</button>`
    );
  }

  // 9. GREEN: Left Panel Tabs - Ensure AI Assistant, Insights, and Vitals are properly styled and switchable
  if (!html.includes('/* ── COMPLETE TAB & OVERLAP FIX STYLES ── */')) {
    const customStyles = `
    /* ── COMPLETE TAB & OVERLAP FIX STYLES ── */
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

    /* Drawer Handle Enhancement */
    #bhu-drawer-handle {
      background: #0b1329 !important;
      border: 1px solid rgba(56, 189, 248, 0.4) !important;
      color: #38bdf8 !important;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }
    #bhu-drawer-handle:hover {
      background: #0f1c3d !important;
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.45);
    }

    /* HUD close buttons */
    #holo-live-tracker-hud, #bhu-color-decoder-card, #holo-spectral-legend, #holo-site-analysis-banner {
      box-shadow: 0 12px 36px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    `;
    html = html.replace('</style>', customStyles + '\n</style>');
  }

  // 10. Make sure the tab switcher script is available in both files
  if (!html.includes('/* ── COMPLETE TAB SWITCHER LOGIC ── */')) {
    const tabLogic = `
  <script>
  /* ── COMPLETE TAB SWITCHER LOGIC ── */
  window.switchLeftDockTab = function(tabName) {
    const aiView = document.getElementById('left-ai-view');
    const vitalsView = document.getElementById('left-health-vitals');
    const insightsView = document.getElementById('left-insights-view');

    // Deselect all tab buttons
    document.querySelectorAll('#left-dock-tabs [role="tab"]').forEach(btn => {
      btn.setAttribute('aria-selected', 'false');
      btn.classList.remove('active');
    });

    // Hide all views
    if (aiView) { aiView.style.display = 'none'; aiView.classList.add('hidden'); }
    if (vitalsView) { vitalsView.style.display = 'none'; vitalsView.classList.add('hidden'); }
    if (insightsView) { insightsView.style.display = 'none'; insightsView.classList.add('hidden'); }

    // Activate selected view
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

  // Ensure DOM is ready and wire click events
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

  fs.writeFileSync(filePath, html, 'utf8');
  console.log('Successfully updated:', path.basename(filePath));
});
