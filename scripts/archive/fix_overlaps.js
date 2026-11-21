/**
 * BHU LOKA Overlap & UI Fix Script
 * Based on user annotations (Red = remove, Yellow = relocate/fix, Green = enhance)
 */
const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, 'public', 'index.html');
let html = fs.readFileSync(FILE, 'utf8');
const original = html;

// ─────────────────────────────────────────────────────────────────────────────
// 🔴 RED — COMPLETELY REMOVE
// ─────────────────────────────────────────────────────────────────────────────

// 1. Remove WebGL2 badge chip from header
html = html.replace(
  /\s*<span[^>]*id="runtime-badge"[^>]*>WebGL2<\/span>/g,
  ''
);

// 2. Remove "NASA PRESENTATION (7 SLIDES)" header button
html = html.replace(
  /\s*<button[^>]*id="btn-open-presentation-header"[\s\S]*?NASA PRESENTATION \(7 SLIDES\)\s*<\/button>/,
  ''
);

// 3. Remove the PASS: satellite strip (xl:flex div inside tm-full-controls)
// It's the first child div inside #tm-full-controls with class containing "hidden xl:flex"
html = html.replace(
  /(<div[^>]*id="tm-full-controls"[^>]*>[\s\S]*?)(<div\s[^>]*class="[^"]*hidden xl:flex[^"]*items-center gap-1 mr-3[^"]*"[\s\S]*?<\/div>\s*<!--\s*Transport controls)/,
  (match, before, passDiv) => {
    // Keep everything before and the transport controls comment, strip the pass div
    return before + '<!-- Transport controls';
  }
);

// 4. Remove COMMANDS bar expand button (the floating commands pill)
// Find and remove the commands toggle button
html = html.replace(
  /<button[^>]*id="bhu-cmd-toggle"[\s\S]*?<\/button>/g,
  ''
);
// Also remove the commands container itself if it's the floating pill at bottom
html = html.replace(
  /<div[^>]*id="bhu-commands-panel"[\s\S]*?<\/div>\s*(?=<!--)/g,
  ''
);

// ─────────────────────────────────────────────────────────────────────────────
// 🟡 YELLOW — RELOCATE / FIX / ENHANCE
// ─────────────────────────────────────────────────────────────────────────────

// 5. Move HORIZON bar: wrap it in a collapsible pill so it doesn't clutter the toolbar
//    Replace the existing bhu-horizon-bar with a compact toggle version
html = html.replace(
  /(<div id="bhu-horizon-bar"[\s\S]*?<\/div>\s*\n)/,
  `<!-- HORIZON BAR — collapsed by default on mobile, shown inline on desktop -->
          <div id="bhu-horizon-bar" class="flex items-center gap-1 bg-slate-900/90 border border-slate-700/80 rounded-lg px-2 py-0.5 shadow-inner mono text-[9.5px] overflow-x-auto no-scrollbar">
            <span class="text-[9px] text-amber-300 font-bold uppercase tracking-wider shrink-0 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
              <span>HORIZON:</span>
            </span>
            <button type="button" id="btn-year-2026" onclick="setPredictiveHorizonYear(2026)"
              class="px-1.5 py-0.5 rounded font-mono font-bold bg-sky-500/25 text-sky-200 border border-sky-400/50 shadow-sm transition whitespace-nowrap"
              title="2026 CE: Deluge Baseline · Ganga Lock 49.5m · Inundation 94.08 km² in Sinks">2026</button>
            <button type="button" id="btn-year-2027" onclick="setPredictiveHorizonYear(2027)"
              class="px-1.5 py-0.5 rounded font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent transition whitespace-nowrap"
              title="2027 CE: Thermal Surge · LST +1.2°C · Runoff +6.5%">2027</button>
            <button type="button" id="btn-year-2028" onclick="setPredictiveHorizonYear(2028)"
              class="px-1.5 py-0.5 rounded font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent transition whitespace-nowrap"
              title="2028 CE: Compound Cloudburst · Ganga Lock 50.4m">2028</button>
            <button type="button" id="btn-year-2029" onclick="setPredictiveHorizonYear(2029)"
              class="px-1.5 py-0.5 rounded font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent transition whitespace-nowrap"
              title="2029 CE: Critical Sukhar Drought · VCI 19%">2029</button>
            <button type="button" id="btn-year-2030" onclick="setPredictiveHorizonYear(2030)"
              class="px-1.5 py-0.5 rounded font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent transition whitespace-nowrap"
              title="2030 CE: Decadal Climate Volatility">2030</button>
            <button type="button" onclick="document.getElementById('bhu-horizon-bar').classList.toggle('hidden')"
              class="ml-auto text-slate-600 hover:text-slate-400 text-[11px] px-1 shrink-0" title="Collapse horizon bar" aria-label="Collapse horizon year selector">&times;</button>
          </div>
`
);

// ─────────────────────────────────────────────────────────────────────────────
// 🟢 GREEN — ENHANCE (AI Assistant / Insights / Vitals tabs)
// ─────────────────────────────────────────────────────────────────────────────

// 6. Enhance left panel "AI Assistant" / "Insights" / "Vitals" tabs styling
//    Add active indicator glow and ensure visible tab styling
const enhancedTabCSS = `
    /* ── ENHANCED LEFT DOCK TABS ── */
    #left-dock-tabs [role="tab"] {
      position: relative;
      font-size: 11px;
      font-weight: 500;
      padding: 5px 10px;
      border-radius: 6px;
      border: none;
      background: none;
      color: #8fa3bd;
      cursor: pointer;
      transition: color 0.15s, background 0.15s;
      white-space: nowrap;
    }
    #left-dock-tabs [role="tab"]:hover {
      color: #c5d4e3;
      background: rgba(255,255,255,0.05);
    }
    #left-dock-tabs [role="tab"][aria-selected="true"] {
      color: #2d9cdb;
      background: rgba(45,156,219,0.1);
      font-weight: 600;
    }
    #left-dock-tabs [role="tab"][aria-selected="true"]::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 20%;
      right: 20%;
      height: 2px;
      background: #2d9cdb;
      border-radius: 2px 2px 0 0;
    }

    /* ── ENHANCED VITALS VIEW ── */
    #left-health-vitals {
      display: none;
      flex-direction: column;
      gap: 10px;
      padding: 10px;
      overflow-y: auto;
    }
    #left-health-vitals.vitals-visible { display: flex !important; }

    /* ── ENHANCED INSIGHTS VIEW ── */
    #left-insights-view {
      display: none;
    }
    #left-insights-view.insights-visible { display: flex !important; }

    /* ── GPS HUD CLOSE BUTTON (top-right inside HUD) ── */
    #holo-live-tracker-hud .hud-close-btn {
      position: absolute;
      top: 6px;
      right: 8px;
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
      font-size: 15px;
      line-height: 1;
      padding: 2px 4px;
      border-radius: 4px;
      transition: color 0.15s;
      z-index: 10;
    }
    #holo-live-tracker-hud .hud-close-btn:hover { color: #f1f5f9; }
    #holo-live-tracker-hud { position: relative; }

    /* ── HELP BUTTON ENHANCED ── */
    #btn-help-sovereign {
      position: relative;
    }
    #bhu-help-tooltip {
      position: absolute;
      left: calc(100% + 10px);
      top: 50%;
      transform: translateY(-50%);
      background: rgba(8,12,22,0.97);
      border: 1px solid rgba(45,156,219,0.3);
      border-radius: 8px;
      padding: 10px 12px;
      width: 220px;
      font-size: 11px;
      color: #c5d4e3;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 999;
      line-height: 1.6;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    #btn-help-sovereign:hover #bhu-help-tooltip,
    #btn-help-sovereign:focus #bhu-help-tooltip {
      opacity: 1;
    }
    #bhu-help-tooltip strong { color: #2d9cdb; display: block; margin-bottom: 4px; }
`;

html = html.replace('</style>', enhancedTabCSS + '\n  </style>');

// ─────────────────────────────────────────────────────────────────────────────
// 7. Fix GPS HUD — add a proper styled close button at top-right of HUD
// ─────────────────────────────────────────────────────────────────────────────
// Remove the stray/poorly styled close button that was added previously
html = html.replace(
  /\s*<button class="px-2 py-1 rounded bg-gray-800 text-white" aria-label="Close GPS HUD"[^>]*>×<\/button>/g,
  ''
);
// Add a proper close button inside the HUD header
html = html.replace(
  /(<div id="holo-live-tracker-hud"[\s\S]*?<div class="flex items-center justify-between border-b[^>]*>)/,
  (match) => {
    return match.replace(
      /<div class="flex items-center justify-between border-b/,
      `<button class="hud-close-btn" aria-label="Close GPS Stream HUD" onclick="document.getElementById('holo-live-tracker-hud').classList.add('hidden')">&times;</button>
            <div class="flex items-center justify-between border-b`
    );
  }
);

// ─────────────────────────────────────────────────────────────────────────────
// 8. Fix left panel tabs — make switchLeftDockTab actually toggle visibility
//    Inject a patched tab switcher after the existing one
// ─────────────────────────────────────────────────────────────────────────────
const tabPatchScript = `
  <script>
  /* ── LEFT DOCK TAB PATCH — ensure Vitals and Insights panels show correctly ── */
  (function patchLeftDockTabs() {
    function doSwitch(tab) {
      var aiView = document.getElementById('left-ai-view');
      var vitalsView = document.getElementById('left-health-vitals');
      var insightsView = document.getElementById('left-insights-view');
      var tabs = document.querySelectorAll('#left-dock-tabs [role="tab"]');

      // Hide all panels
      [aiView, vitalsView, insightsView].forEach(function(el) {
        if (el) {
          el.classList.remove('vitals-visible', 'insights-visible');
          el.style.display = 'none';
        }
      });

      // Deselect all tabs
      tabs.forEach(function(t) { t.setAttribute('aria-selected', 'false'); });

      if (tab === 'ai') {
        if (aiView) aiView.style.display = '';
        var btn = document.getElementById('left-tab-btn-ai');
        if (btn) btn.setAttribute('aria-selected', 'true');
      } else if (tab === 'vitals') {
        if (vitalsView) { vitalsView.style.display = 'flex'; vitalsView.classList.add('vitals-visible'); }
        var btn = document.getElementById('left-tab-btn-vitals');
        if (btn) btn.setAttribute('aria-selected', 'true');
      } else if (tab === 'insights') {
        if (insightsView) { insightsView.style.display = 'flex'; insightsView.classList.add('insights-visible'); }
        var btn = document.getElementById('left-tab-btn-insights');
        if (btn) btn.setAttribute('aria-selected', 'true');
      }
    }

    // Override the global function
    window.switchLeftDockTab = function(tab) { doSwitch(tab); };

    // Wire tab buttons
    document.addEventListener('DOMContentLoaded', function() {
      var tabAi = document.getElementById('left-tab-btn-ai');
      var tabVitals = document.getElementById('left-tab-btn-vitals');
      var tabInsights = document.getElementById('left-tab-btn-insights');
      if (tabAi) tabAi.onclick = function() { doSwitch('ai'); };
      if (tabVitals) tabVitals.onclick = function() { doSwitch('vitals'); };
      if (tabInsights) tabInsights.onclick = function() { doSwitch('insights'); };
    });
  })();
  </script>
`;

// 9. Enhance the "?" help button in the left activity bar
html = html.replace(
  /(<button[^>]*id="btn-help-sovereign"[\s\S]*?)(<\/button>)/,
  (match, before, end) => {
    if (match.includes('bhu-help-tooltip')) return match;
    return before +
      `<div id="bhu-help-tooltip" role="tooltip">
        <strong>BHU LOKA Help</strong>
        <b>3D Map:</b> Drag to orbit, scroll to zoom.<br>
        <b>Layers:</b> Use the layer panel (bottom-right).<br>
        <b>AI Agent:</b> Type in the AI panel (left).<br>
        <b>Tabs:</b> AI · Insights · Vitals in left rail.<br>
        <b>GPS HUD:</b> Click the GPS beacon button.<br>
        <b>Horizon:</b> Click 2026–2030 to simulate.
      </div>` +
      end;
  }
);

// 10. Enhance Vitals panel content if empty
if (!html.includes('vitals-hr-chart') && html.includes('id="left-health-vitals"')) {
  html = html.replace(
    /(<div id="left-health-vitals"[^>]*>)/,
    `$1
      <div class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider px-1 pt-1">Environmental Vitals</div>
      <!-- Air Quality -->
      <div class="panel-inset p-2 flex flex-col gap-1">
        <div class="flex justify-between text-[10px]">
          <span class="text-slate-400">AQI · Patna</span>
          <span class="text-amber-400 font-bold">187 — Unhealthy</span>
        </div>
        <div class="w-full h-1.5 rounded-full bg-slate-800">
          <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500" style="width:62%"></div>
        </div>
        <div class="flex justify-between text-[9px] text-slate-500">
          <span>PM2.5: 142 μg/m³</span><span>PM10: 219 μg/m³</span>
        </div>
      </div>
      <!-- Flood Risk -->
      <div class="panel-inset p-2 flex flex-col gap-1">
        <div class="flex justify-between text-[10px]">
          <span class="text-slate-400">Flood Risk</span>
          <span class="text-rose-400 font-bold">HIGH</span>
        </div>
        <div class="w-full h-1.5 rounded-full bg-slate-800">
          <div class="h-full rounded-full bg-gradient-to-r from-sky-400 to-rose-500" style="width:84%"></div>
        </div>
        <div class="text-[9px] text-slate-500">Ganga Lock: 49.5m · Ponding &lt;46m</div>
      </div>
      <!-- Temperature -->
      <div class="panel-inset p-2 flex flex-col gap-1">
        <div class="flex justify-between text-[10px]">
          <span class="text-slate-400">Surface Temp</span>
          <span class="text-orange-400 font-bold">26.2°C</span>
        </div>
        <div class="w-full h-1.5 rounded-full bg-slate-800">
          <div class="h-full rounded-full bg-gradient-to-r from-sky-400 to-orange-400" style="width:52%"></div>
        </div>
        <div class="text-[9px] text-slate-500">NIR / FLIR · Transpiration active</div>
      </div>
      <!-- Satellite Pass -->
      <div class="panel-inset p-2 flex flex-col gap-1">
        <div class="flex justify-between text-[10px]">
          <span class="text-slate-400">Next Sat Pass</span>
          <span class="text-cyan-400 font-bold">04h 12m</span>
        </div>
        <div class="text-[9px] text-slate-500">Sentinel-1B · L+S Band Dual Ready</div>
        <div class="text-[9px] text-emerald-400">NISAR Radar: Ready</div>
      </div>`
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 11. Add close buttons to other overlapping panels
// ─────────────────────────────────────────────────────────────────────────────
// Add close to bhu-pred-map-hud if missing
if (!html.match(/id="bhu-pred-map-hud"[\s\S]{0,500}hud-close-btn/)) {
  html = html.replace(
    /(<div id="bhu-pred-map-hud"[^>]*>)/,
    `$1
            <button class="hud-close-btn" aria-label="Close Flood HUD" onclick="document.getElementById('bhu-pred-map-hud').classList.add('hidden')">&times;</button>`
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 12. Inject tab patch script before </body>
// ─────────────────────────────────────────────────────────────────────────────
html = html.replace('</body>', tabPatchScript + '\n</body>');

// ─────────────────────────────────────────────────────────────────────────────
// Write file
// ─────────────────────────────────────────────────────────────────────────────
if (html !== original) {
  fs.writeFileSync(FILE, html, 'utf8');
  console.log('Fixed & enhanced: public/index.html');
  console.log('Changes applied:');
  console.log('  RED removed: WebGL2 badge, NASA Presentation header button, PASS strip');
  console.log('  YELLOW fixed: Horizon bar has close button, Help button has tooltip');
  console.log('  GREEN enhanced: GPS HUD close button, Left tabs functional, Vitals panel filled');
  console.log('  ADDED: Close buttons on GPS HUD, Flood HUD');
} else {
  console.log('No changes made (already up to date).');
}
