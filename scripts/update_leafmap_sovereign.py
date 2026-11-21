import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
fpath = os.path.join(repo, 'bhu_loka_leafmap_interactive.html')

with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. New header controls HTML
new_top_controls = '''    <!-- CLEAN SEGMENTED SOVEREIGN MAP SWITCHERS & 28 STATES / 8 UTS SELECTOR -->
    <div class="flex items-center gap-1.5 text-[10px] mono shrink-0 max-w-full overflow-x-auto whitespace-nowrap">
      <div class="hidden xl:flex items-center gap-1 mr-1 shrink-0">
        <input id="gis-addr-input" type="text" placeholder="Place or lat, lon (Mumbai, 34.15, 77.58)..."
          class="bg-[#070b12] border border-slate-700/80 rounded px-2 py-1 text-[10px] text-slate-100 w-32 2xl:w-44 focus:outline-none focus:border-sky-500"
          onkeydown="if(event.key==='Enter') searchAndFlyAddress()">
        <button type="button" onclick="searchAndFlyAddress()"
          class="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2 py-1 rounded font-medium transition">
          Go
        </button>
      </div>

      <!-- Basemap Toggles -->
      <button onclick="setBaseMode('sat')" id="btn-base-sat"
        class="bg-sky-500/20 text-sky-300 border border-sky-500/45 px-2 py-1 rounded font-medium transition">
        Esri Satellite
      </button>
      <button onclick="setBaseMode('osm')" id="btn-base-osm"
        class="bg-[#070b12] hover:bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded font-medium transition">
        OpenStreetMap
      </button>
      <button onclick="setBaseMode('dark')" id="btn-base-dark"
        class="bg-[#070b12] hover:bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded font-medium transition">
        Dark Slate
      </button>

      <span class="h-5 w-px bg-slate-800 mx-0.5"></span>

      <!-- 28 STATES & 8 UNION TERRITORIES INTERACTIVE SELECTOR -->
      <div class="flex items-center gap-1 bg-[#070b12] border border-sky-500/40 rounded px-2 py-1 shrink-0">
        <span class="text-sky-400 font-semibold text-[10px] flex items-center gap-1"><i class="fa-solid fa-landmark-flag"></i> State / UT:</span>
        <select id="sovereign-state-select" onchange="selectSovereignState(this.value)"
          class="bg-transparent text-[10.5px] text-slate-100 font-mono focus:outline-none cursor-pointer max-w-[180px]">
          <option value="" disabled selected>-- 28 States &amp; 8 UTs --</option>
          <optgroup label="28 Indian States" id="optgroup-states"></optgroup>
          <optgroup label="8 Union Territories" id="optgroup-uts"></optgroup>
        </select>
        <button type="button" id="btn-toggle-districts" onclick="toggleCurrentStateDistricts()" title="Toggle Verified District Boundaries"
          class="hidden px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded text-[9px] border border-amber-500/30">
          Districts
        </button>
      </div>

      <span class="h-5 w-px bg-slate-800 mx-0.5"></span>

      <!-- Macro Boundaries -->
      <button onclick="focusIndiaMacro()"
        class="bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2 py-1 rounded font-medium transition"
        title="Zoom to complete Sovereign India boundary (6.75°N to 37.10°N)">
        Pan-India (36)
      </button>

      <!-- Scientific Sentinel-1 Deluge Layer (Ground Truth Benchmark) -->
      <button onclick="activatePatnaSarDeluge()" id="btn-sar-deluge"
        class="bg-sky-500/20 hover:bg-sky-500/30 text-sky-200 border border-sky-500/50 px-2 py-1 rounded font-semibold transition flex items-center gap-1 shadow-[0_0_8px_rgba(56,189,248,0.2)]"
        title="Copernicus Sentinel-1 SAR Patna Deluge 2019 (Verified Empirical Ground Truth)">
        <span class="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse"></span>
        <span>Sentinel-1 SAR Deluge (Patna 2019)</span>
      </button>

      <!-- DEM Topography -->
      <button onclick="focusPatnaDEM()"
        class="bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2 py-1 rounded font-medium transition"
        title="Copernicus 30m Global DEM">
        Copernicus DEM 30m
      </button>

      <!-- Extrude to 3D -->
      <button id="btn-crop-to-3d" type="button" onclick="cropCurrentBoundsTo3D()"
        class="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/50 px-2 py-1 rounded font-semibold transition flex items-center gap-1 shadow-[0_0_8px_rgba(16,185,129,0.2)]"
        title="Crop current Leaflet view bounding box and extrude into 3D DEM Terrain Workstation">
        <span><i class="fa-solid fa-crop-simple mr-0.5"></i> Crop to 3D</span>
      </button>

      <a id="link-open-3d-workstation" href="bhu_loka_cyber_dashboard.html"
        class="bg-sky-500 hover:bg-sky-400 text-slate-950 px-2.5 py-1 rounded font-semibold transition">
        3D Workstation &rarr;
      </a>

      <!-- Map Display Controls -->
      <button type="button" id="btn-2d-legend-toggle" onclick="toggleGisLegend()" title="Show/Hide Map Legend"
        class="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium transition cursor-pointer shrink-0">
        Legend
      </button>
      <button type="button" id="btn-2d-theater" onclick="toggle2DTheaterMode()" aria-pressed="false"
        title="Expand Map (Hide header &amp; legend card)"
        class="inline-flex items-center gap-1 px-2 py-1 rounded bg-sky-500/15 hover:bg-sky-500/25 text-sky-300 border border-sky-500/40 font-semibold transition cursor-pointer shrink-0">
        <span id="btn-2d-theater-label">Expand</span>
      </button>
      <button type="button" id="btn-2d-fullscreen" onclick="toggle2DFullscreen()" aria-pressed="false"
        title="Toggle Browser Fullscreen (ESC to exit)"
        class="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition cursor-pointer shrink-0">
        <span id="btn-2d-fullscreen-label">Fullscreen</span>
      </button>
    </div>
  </header>'''

# Replace header block
old_top_block_start = '<!-- CLEAN SEGMENTED MAP SWITCHERS & ADDRESS JUMP -->'
old_top_block_end = '<!-- DOCKED 2D CARTOGRAPHIC WORKSTATION -->'
start_idx = text.find(old_top_block_start)
end_idx = text.find(old_top_block_end)

if start_idx != -1 and end_idx != -1:
    text = text[:start_idx] + new_top_controls + '\n\n  ' + text[end_idx:]
    print('Header controls replaced successfully.')
else:
    print('WARNING: Top block not found!')

# 2. Add #state-sovereign-card inside #gis-center-stage
card_html = '''      <!-- SOVEREIGN STATE & UNION TERRITORY CARD (DYNAMIC) -->
      <div id="state-sovereign-card"
        class="hidden absolute top-3 left-4 bg-[#090e18]/95 border border-sky-500/50 rounded-xl p-3 shadow-2xl backdrop-blur-md z-[980] max-w-sm w-full font-mono text-[11px] text-slate-200">
        <div class="flex items-center justify-between border-b border-slate-700/80 pb-2 mb-2">
          <div>
            <div id="ssc-name-vernacular" class="text-xs font-bold text-sky-400">राज्य / State</div>
            <div id="ssc-name-en" class="text-sm font-extrabold text-slate-100">State Name</div>
          </div>
          <div class="flex items-center gap-1">
            <span id="ssc-unit-type" class="px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40 text-[9px] font-semibold">State</span>
            <button type="button" onclick="closeSovereignStateCard()" class="text-slate-400 hover:text-rose-400 p-1 font-bold text-xs" title="Close Card">✕</button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-[10px] text-slate-300 mb-2.5">
          <div>Capital: <strong id="ssc-capital" class="text-slate-100">--</strong></div>
          <div>Districts: <strong id="ssc-districts" class="text-emerald-300">--</strong></div>
          <div>Centroid: <span id="ssc-centroid" class="text-sky-300">--</span></div>
          <div>State Code: <span id="ssc-code" class="text-amber-300">--</span></div>
        </div>
        <div class="text-[9.5px] text-slate-400 border-t border-slate-800 pt-2 mb-2">
          <div class="font-semibold text-slate-300 mb-0.5">Administrative Hierarchy:</div>
          <div id="ssc-hierarchy" class="text-slate-400 leading-tight">Country → State → District → Tehsil → Block → Panchayat → Village</div>
        </div>
        <div class="text-[8.5px] text-slate-500 border-t border-slate-800/80 pt-1.5 flex items-center justify-between">
          <span>Survey of India · data.gov.in · GADM v4.1</span>
          <button type="button" onclick="focusIndiaMacro()" class="text-sky-400 hover:underline">Reset Pan-India</button>
        </div>
      </div>\n'''

stage_search = '<!-- CENTER STAGE: LEAFLET INTERACTIVE MAP + COMPACT LEGEND -->\n    <div id="gis-center-stage" class="flex-1 min-w-0 relative flex flex-col h-full overflow-hidden">'
if stage_search in text:
    text = text.replace(stage_search, stage_search + '\n' + card_html)
    print('Added #state-sovereign-card')
else:
    print('WARNING: Center stage marker not found!')

# 3. Update SAR dock title
if 'DANCING WITH THE SARS' in text:
    text = text.replace('DANCING WITH THE SARS', 'SENTINEL-1 SAR DELUGE (GROUND TRUTH)')
    text = text.replace('NASA\n            2026', '10m GRD')
    text = text.replace('NASA 2026', '10m GRD')
    print('Updated SAR dock title')

# 4. JavaScript Engine for 28 States & 8 UTs
js_sovereign_engine = '''
    // ==========================================
    // ALL 28 STATES + 8 UNION TERRITORIES SOVEREIGN ENGINE
    // ==========================================
    const STATE_CAPITALS = {
      "Andaman and Nicobar Islands": "Port Blair",
      "Andhra Pradesh": "Amaravati",
      "Arunachal Pradesh": "Itanagar",
      "Assam": "Dispur",
      "Bihar": "Patna",
      "Chandigarh": "Chandigarh",
      "Chhattisgarh": "Raipur",
      "Dadra and Nagar Haveli and Daman and Diu": "Daman",
      "Delhi": "New Delhi",
      "Goa": "Panaji",
      "Gujarat": "Gandhinagar",
      "Haryana": "Chandigarh",
      "Himachal Pradesh": "Shimla",
      "Jammu and Kashmir": "Srinagar / Jammu",
      "Jharkhand": "Ranchi",
      "Karnataka": "Bengaluru",
      "Kerala": "Thiruvananthapuram",
      "Ladakh": "Leh",
      "Lakshadweep": "Kavaratti",
      "Madhya Pradesh": "Bhopal",
      "Maharashtra": "Mumbai",
      "Manipur": "Imphal",
      "Meghalaya": "Shillong",
      "Mizoram": "Aizawl",
      "Nagaland": "Kohima",
      "Odisha": "Bhubaneswar",
      "Puducherry": "Puducherry",
      "Punjab": "Chandigarh",
      "Rajasthan": "Jaipur",
      "Sikkim": "Gangtok",
      "Tamil Nadu": "Chennai",
      "Telangana": "Hyderabad",
      "Tripura": "Agartala",
      "Uttar Pradesh": "Lucknow",
      "Uttarakhand": "Dehradun",
      "West Bengal": "Kolkata"
    };

    let activeSelectedStateLayer = null;
    let activeSelectedStateName = null;

    function populateSovereignStateDropdown() {
      const optStates = document.getElementById('optgroup-states');
      const optUts = document.getElementById('optgroup-uts');
      if (!optStates || !optUts) return;

      if (!window.BHU_LOKA_INDIA_INDEX || !window.BHU_LOKA_INDIA_INDEX.states) return;

      optStates.innerHTML = '';
      optUts.innerHTML = '';

      const list = window.BHU_LOKA_INDIA_INDEX.states.slice();
      list.sort((a, b) => a.name_en.localeCompare(b.name_en));

      list.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.name_en;
        const vern = u.local_name ? ` · ${u.local_name}` : '';
        opt.textContent = `${u.name_en}${vern}`;
        if (u.unit_type === 'State') {
          optStates.appendChild(opt);
        } else {
          optUts.appendChild(opt);
        }
      });
    }

    function highlightSovereignStatePolygon(stateName) {
      if (activeSelectedStateLayer) {
        map.removeLayer(activeSelectedStateLayer);
        activeSelectedStateLayer = null;
      }
      if (!window.BHU_LOKA_REAL_DATA || !window.BHU_LOKA_REAL_DATA.india_states) return;

      const feat = window.BHU_LOKA_REAL_DATA.india_states.features.find(
        f => f.properties && f.properties.name && f.properties.name.toLowerCase() === stateName.toLowerCase()
      );
      if (!feat) return;

      activeSelectedStateLayer = L.geoJSON(feat, {
        style: {
          color: '#38bdf8',
          weight: 3.2,
          fillColor: '#38bdf8',
          fillOpacity: 0.22,
          dashArray: null
        }
      }).addTo(map);
    }

    function selectSovereignState(stateName) {
      if (!stateName) return;
      activeSelectedStateName = stateName;
      const sel = document.getElementById('sovereign-state-select');
      if (sel && sel.value !== stateName) sel.value = stateName;

      let unit = null;
      if (window.BHU_LOKA_INDIA_INDEX && window.BHU_LOKA_INDIA_INDEX.states) {
        unit = window.BHU_LOKA_INDIA_INDEX.states.find(s => s.name_en.toLowerCase() === stateName.toLowerCase());
      }

      if (unit) {
        if (unit.bbox && unit.bbox.length === 4) {
          map.flyToBounds([[unit.bbox[1], unit.bbox[0]], [unit.bbox[3], unit.bbox[2]]], { padding: [36, 36], duration: 1.2 });
        } else if (unit.centroid) {
          map.flyTo([unit.centroid[0], unit.centroid[1]], 7.5, { duration: 1.0 });
        }
        displaySovereignStateCard(unit);
      }

      highlightSovereignStatePolygon(stateName);

      const distBtn = document.getElementById('btn-toggle-districts');
      if (distBtn) {
        if (stateName.toLowerCase() === 'bihar') {
          distBtn.classList.remove('hidden');
          distBtn.textContent = 'Toggle 38 Districts';
        } else {
          distBtn.classList.add('hidden');
        }
      }

      const legTitle = document.getElementById('legend-title');
      if (legTitle) {
        legTitle.innerText = `${stateName.toUpperCase()} · SOVEREIGN BOUNDARY`;
      }
    }

    function displaySovereignStateCard(unit) {
      const card = document.getElementById('state-sovereign-card');
      if (!card) return;

      const capital = STATE_CAPITALS[unit.name_en] || 'Verified Administrative Seat';
      document.getElementById('ssc-name-en').innerText = unit.name_en;
      document.getElementById('ssc-name-vernacular').innerText = unit.local_name ? `${unit.local_name} (${unit.unit_type})` : unit.unit_type;
      document.getElementById('ssc-unit-type').innerText = unit.unit_type;
      document.getElementById('ssc-capital').innerText = capital;
      document.getElementById('ssc-code').innerText = unit.state_code || unit.unit_id || 'IND';

      let distStr = '--';
      if (unit.hierarchy && unit.hierarchy.hierarchy_note) {
        const m = unit.hierarchy.hierarchy_note.match(/(\\d+)\\s+Districts/i);
        if (m) distStr = `${m[1]} Districts`;
        else distStr = unit.hierarchy.hierarchy_note.split(',')[0];
      } else if (unit.name_en === 'Bihar') {
        distStr = '38 Districts';
      }
      document.getElementById('ssc-districts').innerText = distStr;

      if (unit.centroid) {
        document.getElementById('ssc-centroid').innerText = `${unit.centroid[0].toFixed(2)}°N, ${unit.centroid[1].toFixed(2)}°E`;
      }

      if (unit.hierarchy && unit.hierarchy.levels) {
        const labels = unit.hierarchy.levels.slice(1, 6).map(l => l.key.replace(/_/g, ' '));
        document.getElementById('ssc-hierarchy').innerText = labels.join(' → ');
      } else {
        document.getElementById('ssc-hierarchy').innerText = 'State → District → Sub-Division / Tehsil → Block → Panchayat / Ward';
      }

      card.classList.remove('hidden');
    }

    function closeSovereignStateCard() {
      const card = document.getElementById('state-sovereign-card');
      if (card) card.classList.add('hidden');
      if (activeSelectedStateLayer) {
        map.removeLayer(activeSelectedStateLayer);
        activeSelectedStateLayer = null;
      }
      const sel = document.getElementById('sovereign-state-select');
      if (sel) sel.value = '';
      activeSelectedStateName = null;
    }

    let districtsLayerVisible = false;
    function toggleCurrentStateDistricts() {
      if (activeSelectedStateName && activeSelectedStateName.toLowerCase() === 'bihar') {
        if (!districtsLayerVisible) {
          map.addLayer(biharDistrictsLayer);
          districtsLayerVisible = true;
          document.getElementById('btn-toggle-districts').classList.add('bg-amber-500/30');
        } else {
          map.removeLayer(biharDistrictsLayer);
          districtsLayerVisible = false;
          document.getElementById('btn-toggle-districts').classList.remove('bg-amber-500/30');
        }
      }
    }

    function activatePatnaSarDeluge() {
      sarModeActive = true;
      map.flyTo([25.61, 85.14], 12.5, { duration: 1.0 });

      const dock = document.getElementById('sar-floating-dock');
      if (dock) dock.classList.remove('hidden');
      const hud = document.getElementById('sar-pixel-hud');
      if (hud) hud.classList.remove('hidden');

      setSarDisplayMode('post');
      if (!map.hasLayer(sarGainLayer)) map.addLayer(sarGainLayer);
      if (!map.hasLayer(sarPermWaterLayer)) map.addLayer(sarPermWaterLayer);

      const legTitle = document.getElementById('legend-title');
      if (legTitle) legTitle.innerText = "COPERNICUS SENTINEL-1 SAR · PATNA DELUGE (GROUND TRUTH)";
    }
    window.activatePatnaSarDeluge = activatePatnaSarDeluge;
    window.activateDancingWithSARs = activatePatnaSarDeluge; // backward compatibility
'''

# Wire state click in indiaStatesLayer
old_on_each = '''      onEachFeature: (feat, layer) => {
        layer.bindTooltip(`${feat.properties.name} (${feat.properties.type || 'State/UT'})`, { sticky: true });
      }'''

new_on_each = '''      onEachFeature: (feat, layer) => {
        layer.bindTooltip(`${feat.properties.name} (${feat.properties.type || 'State/UT'})`, { sticky: true });
        layer.on('click', () => {
          selectSovereignState(feat.properties.name);
        });
      }'''

if old_on_each in text:
    text = text.replace(old_on_each, new_on_each)
    print('Wired state polygon click to selectSovereignState')
else:
    print('WARNING: old_on_each not found!')

# Insert js_sovereign_engine before activateDancingWithSARs or focusIndiaMacro
macro_search = 'function focusIndiaMacro() {'
if macro_search in text:
    text = text.replace(macro_search, js_sovereign_engine + '\n    ' + macro_search)
    print('Inserted js_sovereign_engine before focusIndiaMacro')
else:
    print('WARNING: focusIndiaMacro not found!')

# Call populateSovereignStateDropdown() on DOMContentLoaded
init_call = 'populateSovereignStateDropdown();'
if 'populateSovereignStateDropdown()' not in text:
    ready_marker = 'map.setView([22.5, 82.5], 5);'
    if ready_marker in text:
        text = text.replace(ready_marker, ready_marker + '\n    ' + init_call)
        print('Added populateSovereignStateDropdown() call on map setup')

# Write root and public
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated root bhu_loka_leafmap_interactive.html')

pub_path = os.path.join(repo, 'public', 'bhu_loka_leafmap_interactive.html')
with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated public bhu_loka_leafmap_interactive.html')
