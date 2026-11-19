/**
 * BHU LOKA — Shared Layer Registry & Unified 2D Layer Intelligence Panel
 * ======================================================================
 * Synchronizes active layers, opacity, selected location, and AOI bounds across:
 *   - 2D Earth (bhu_loka_leafmap_interactive.html)
 *   - 3D Earth (index.html / bhu_loka_cyber_dashboard.html)
 *   - Urban Intelligence Studio (bhu_loka_urban_studio.js)
 *
 * Strict Zero-Fabrication Policy:
 *   - Missing or unconfigured providers report explicit UNAVAILABLE status.
 *   - Crime layer NEVER generates fake KDE/synthetic hotspots.
 *   - Zero neon colors. Zero emojis. FontAwesome 6 solid icons only.
 */
(function (window) {
  'use strict';

  const STORAGE_LAYERS_KEY = 'bhu_loka_shared_layers_v1';
  const STORAGE_AOI_KEY = 'bhu_loka_shared_aoi_v1';

  // ═══════════════════════════════════════════════════════════════
  // CANONICAL 14-LAYER CATALOGUE WITH PROVENANCE METADATA
  // ═══════════════════════════════════════════════════════════════
  const LAYER_CATALOG = [
    {
      id: 'heat', name: 'Heat Area (LST)', icon: 'fa-temperature-high', color: '#d97706',
      provider: 'wms',
      wmsUrl: 'https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi',
      wmsLayers: 'MODIS_Terra_Land_Surface_Temp_Day',
      source: 'NASA GIBS / MODIS Terra MOD11A1',
      obsDate: 'Rolling 8-day composite (2026)',
      procDate: 'Near Real-Time WMS',
      resolution: '1 km',
      status: 'OBSERVED',
      legend: 'Thermal surface radiance gradient (Cool blue to warm amber-crimson)'
    },
    {
      id: 'flood', name: 'Flood Zone', icon: 'fa-house-flood-water', color: '#0284c7',
      provider: 'dem_derived',
      source: 'Copernicus DEM 90m + Open-Meteo Elevation Sink Model',
      obsDate: 'Copernicus GLO-90 Baseline',
      procDate: 'Computed on-demand for viewport',
      resolution: '90 m grid',
      status: 'MODELLED',
      legend: 'Lowest 25% elevation depressions & ponding risk cells within active extent'
    },
    {
      id: 'multihazard', name: 'Multi-Hazard', icon: 'fa-triangle-exclamation', color: '#6366f1',
      provider: 'composite',
      source: 'Combined Copernicus DEM Sinks + NASA MODIS LST',
      obsDate: '2026 Baseline + Rolling LST',
      procDate: 'Live client composite',
      resolution: '90 m – 1 km',
      status: 'DERIVED',
      legend: 'Composite overlay of modelled flood depressions and surface thermal stress'
    },
    {
      id: 'safezone', name: 'Safe Zone (Elevated)', icon: 'fa-shield-halved', color: '#059669',
      provider: 'dem_derived',
      source: 'Copernicus DEM 90m Upper-Terrace Classification',
      obsDate: 'Copernicus GLO-90 Baseline',
      procDate: 'Computed on-demand for viewport',
      resolution: '90 m grid',
      status: 'DERIVED',
      legend: 'Upper-quartile topographic ridges & natural levees (relative drainage advantage only)'
    },
    {
      id: 'crime', name: 'High Crime Zone', icon: 'fa-ban', color: '#e11d48',
      provider: 'unavailable',
      source: 'Official NCRB / State Police Georeferenced Feed',
      obsDate: 'N/A',
      procDate: 'N/A',
      resolution: 'N/A',
      status: 'UNAVAILABLE',
      legend: 'Official crime data unavailable. Synthetic or AI-generated crime polygons are strictly prohibited.'
    },
    {
      id: 'sar', name: 'SAR / Flood SAR', icon: 'fa-satellite-dish', color: '#eab308',
      provider: 'dem_derived',
      source: 'Sentinel-1 C-Band Empirical Specular Model (DEM-assisted)',
      obsDate: 'Empirical Monsoon Reference',
      procDate: 'Client hydrological proxy',
      resolution: '90 m proxy',
      status: 'MODELLED',
      legend: 'Modelled low-backscatter standing-water susceptibility zones'
    },
    {
      id: 'dem', name: 'DEM / Elevation', icon: 'fa-mountain', color: '#94a3b8',
      provider: 'dem_grid',
      source: 'Copernicus GLO-90 via Open-Meteo Elevation API',
      obsDate: 'Copernicus DEM 2023/2024',
      procDate: 'Live API query',
      resolution: '90 m',
      status: 'OBSERVED',
      legend: 'Hypsometric elevation tint from valley green to ridge ochre (meters AMSL)'
    },
    {
      id: 'buildings', name: 'Buildings', icon: 'fa-building', color: '#cbd5e1',
      provider: 'osm', osmKey: 'building',
      source: 'OpenStreetMap Contributors (Overpass API)',
      obsDate: 'Live OSM database',
      procDate: 'On-demand vector extraction',
      resolution: 'Building-footprint vector',
      status: 'OBSERVED',
      legend: 'Mapped building footprint polygons (height/levels where tagged)'
    },
    {
      id: 'roads', name: 'Roads', icon: 'fa-road', color: '#e2e8f0',
      provider: 'osm', osmKey: 'road',
      source: 'OpenStreetMap Contributors (Overpass API)',
      obsDate: 'Live OSM database',
      procDate: 'On-demand vector extraction',
      resolution: 'Road-centerline vector',
      status: 'OBSERVED',
      legend: 'Primary/trunk arterials (bright) to residential streets (slate)'
    },
    {
      id: 'greenery', name: 'Greenery / Vegetation', icon: 'fa-tree', color: '#059669',
      provider: 'osm', osmKey: 'greenery',
      source: 'OpenStreetMap Parks, Woods & Green Spaces',
      obsDate: 'Live OSM database',
      procDate: 'On-demand vector extraction',
      resolution: 'Polygon vector',
      status: 'OBSERVED',
      legend: 'Parks, urban forests, meadows, orchards, and mapped tree clusters'
    },
    {
      id: 'water', name: 'Water Bodies', icon: 'fa-water', color: '#38bdf8',
      provider: 'osm', osmKey: 'water',
      source: 'OpenStreetMap Hydrography (Overpass API)',
      obsDate: 'Live OSM database',
      procDate: 'On-demand vector extraction',
      resolution: 'Vector waterlines & basins',
      status: 'OBSERVED',
      legend: 'Rivers, canals, lakes, reservoirs, and mapped ponds'
    },
    {
      id: 'landuse', name: 'Land Use / Land Cover', icon: 'fa-layer-group', color: '#f59e0b',
      provider: 'wms',
      wmsUrl: 'https://services.terrascope.be/wms/v2',
      wmsLayers: 'WORLDCOVER_2021_MAP',
      source: 'ESA WorldCover 2021 v200 (Sentinel-1 + Sentinel-2)',
      obsDate: '2021 Global Annual Map',
      procDate: 'ESA / Terrascope WMS',
      resolution: '10 m',
      status: 'OBSERVED',
      legend: 'Tree cover, shrubland, grassland, cropland, built-up, water, wetlands'
    },
    {
      id: 'population', name: 'Population Density', icon: 'fa-users', color: '#a855f7',
      provider: 'unavailable',
      source: 'WorldPop 100m Unconstrained Grid (requires backend tile proxy)',
      obsDate: 'N/A',
      procDate: 'N/A',
      resolution: '100 m (not configured)',
      status: 'UNAVAILABLE',
      legend: 'Population raster endpoint not configured for direct browser CORS. Backend proxy required.'
    },
    {
      id: 'infrastructure', name: 'Infrastructure', icon: 'fa-hospital', color: '#38bdf8',
      provider: 'osm', osmKey: 'infrastructure',
      source: 'OpenStreetMap Critical Facilities (Overpass API)',
      obsDate: 'Live OSM database',
      procDate: 'On-demand vector extraction',
      resolution: 'Point / polygon vector',
      status: 'OBSERVED',
      legend: 'Hospitals, schools, universities, rail/transit stations, power substations'
    }
  ];

  // ═══════════════════════════════════════════════════════════════
  // SHARED LAYER REGISTRY (SYNCS 2D <-> 3D <-> URBAN STUDIO)
  // ═══════════════════════════════════════════════════════════════
  class BhuLokaLayerRegistry {
    constructor() {
      this.catalog = LAYER_CATALOG;
      this.state = this._loadState();
      this.aoi = this._loadAOI();
      this.listeners = new Set();

      window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_LAYERS_KEY) {
          this.state = this._loadState();
          this._emit('layers');
        } else if (e.key === STORAGE_AOI_KEY) {
          this.aoi = this._loadAOI();
          this._emit('aoi');
        }
      });
    }

    _defaultState() {
      const s = {};
      LAYER_CATALOG.forEach((l) => {
        s[l.id] = { enabled: false, opacity: 0.78, runtimeStatus: l.status };
      });
      return s;
    }

    _loadState() {
      const def = this._defaultState();
      try {
        const raw = localStorage.getItem(STORAGE_LAYERS_KEY);
        if (!raw) return def;
        const parsed = JSON.parse(raw);
        Object.keys(def).forEach((k) => {
          if (parsed[k]) {
            def[k].enabled = Boolean(parsed[k].enabled) && this.getMeta(k).provider !== 'unavailable';
            if (typeof parsed[k].opacity === 'number') def[k].opacity = parsed[k].opacity;
          }
        });
      } catch (_) { }
      return def;
    }

    _loadAOI() {
      try {
        const raw = localStorage.getItem(STORAGE_AOI_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch (_) { return null; }
    }

    _saveState() {
      try { localStorage.setItem(STORAGE_LAYERS_KEY, JSON.stringify(this.state)); } catch (_) { }
    }

    getMeta(id) {
      return LAYER_CATALOG.find((l) => l.id === id) || null;
    }

    get(id) {
      return this.state[id] || { enabled: false, opacity: 0.78, runtimeStatus: 'UNAVAILABLE' };
    }

    set(id, patch) {
      const meta = this.getMeta(id);
      if (!meta) return;
      if (meta.provider === 'unavailable' && patch.enabled) {
        this.state[id] = { ...this.state[id], enabled: false, runtimeStatus: 'UNAVAILABLE' };
        this._emit('layers', id);
        return;
      }
      this.state[id] = { ...this.get(id), ...patch };
      this._saveState();
      this._emit('layers', id);
      window.dispatchEvent(new CustomEvent('bhu-loka:layer-changed', { detail: { id, state: this.state[id] } }));
    }

    setAOI(aoiObj) {
      this.aoi = aoiObj;
      try {
        if (aoiObj) localStorage.setItem(STORAGE_AOI_KEY, JSON.stringify(aoiObj));
        else localStorage.removeItem(STORAGE_AOI_KEY);
      } catch (_) { }
      this._emit('aoi');
      window.dispatchEvent(new CustomEvent('bhu-loka:aoi-changed', { detail: aoiObj }));
    }

    getAOI() { return this.aoi; }

    subscribe(fn) {
      this.listeners.add(fn);
      return () => this.listeners.delete(fn);
    }

    _emit(type, id) {
      this.listeners.forEach((fn) => {
        try { fn({ type, id, state: this.state, aoi: this.aoi }); } catch (_) { }
      });
    }
  }

  window.BhuLokaLayerRegistry = new BhuLokaLayerRegistry();

  // ═══════════════════════════════════════════════════════════════
  // UNIFIED 2D FLOATING LAYER PANEL (FOR bhu_loka_leafmap_interactive.html)
  // ═══════════════════════════════════════════════════════════════
  function init2DLayerPanel(map) {
    if (!map || typeof L === 'undefined') return;
    if (document.getElementById('bhu-2d-layer-fab')) return;

    const reg = window.BhuLokaLayerRegistry;
    const leafletLayers = {};
    let osmCache = { key: null, data: null };
    let demCache = { key: null, data: null };

    // Inject scoped dark aerospace styles (unslop: quiet chrome, zero neon)
    const style = document.createElement('style');
    style.id = 'bhu-2d-layer-panel-css';
    style.textContent = `
      #bhu-2d-layer-fab {
        position: fixed; right: 16px; bottom: 44px; z-index: 1200;
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 14px; border-radius: 10px;
        background: rgba(8, 13, 24, 0.94); color: #e2e8f0;
        border: 1px solid rgba(56, 189, 248, 0.35);
        font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700;
        letter-spacing: 0.05em; cursor: pointer;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55);
        transition: border-color 0.2s, background 0.2s;
      }
      #bhu-2d-layer-fab:hover { border-color: rgba(56, 189, 248, 0.75); background: rgba(15, 23, 42, 0.98); }
      #bhu-2d-layer-fab .b2d-count {
        padding: 1px 6px; border-radius: 999px; font-size: 10px;
        background: rgba(2, 132, 199, 0.22); color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
      }
      #bhu-2d-layer-panel {
        position: fixed; right: 16px; bottom: 92px; z-index: 1200;
        width: 320px; max-height: calc(100vh - 170px);
        display: none; flex-direction: column;
        background: rgba(7, 11, 20, 0.96); backdrop-filter: blur(12px);
        border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px;
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.75);
        color: #cbd5e1; font-family: 'JetBrains Mono', monospace;
        overflow: hidden;
      }
      #bhu-2d-layer-panel.open { display: flex; }
      .b2d-head {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.08);
        background: rgba(11, 17, 30, 0.9);
      }
      .b2d-list { overflow-y: auto; padding: 8px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
      .b2d-row {
        padding: 7px 8px; border-radius: 8px;
        background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(255,255,255,0.06);
      }
      .b2d-row-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
      .b2d-row-title { display: flex; align-items: center; gap: 7px; font-size: 10.5px; color: #e2e8f0; flex: 1; min-width: 0; }
      .b2d-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
      .b2d-badge { font-size: 8px; padding: 1px 5px; border-radius: 4px; font-weight: 700; flex-shrink: 0; }
      .b2d-st-OBSERVED { background: rgba(5,150,105,0.16); color: #34d399; border: 1px solid rgba(5,150,105,0.3); }
      .b2d-st-DERIVED { background: rgba(2,132,199,0.16); color: #38bdf8; border: 1px solid rgba(2,132,199,0.3); }
      .b2d-st-MODELLED { background: rgba(217,119,6,0.16); color: #fbbf24; border: 1px solid rgba(217,119,6,0.3); }
      .b2d-st-UNAVAILABLE { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.28); }
      .b2d-info-btn {
        background: transparent; border: 1px solid rgba(255,255,255,0.08); color: #64748b;
        width: 20px; height: 20px; border-radius: 5px; cursor: pointer; font-size: 9px;
        display: inline-flex; align-items: center; justify-content: center;
      }
      .b2d-info-btn:hover { color: #38bdf8; border-color: rgba(56,189,248,0.4); }
      .b2d-meta {
        display: none; margin-top: 6px; padding: 6px; border-radius: 6px;
        background: rgba(4, 7, 16, 0.85); border: 1px solid rgba(255,255,255,0.06);
        font-size: 9px; line-height: 1.45; color: #94a3b8;
      }
      .b2d-meta.show { display: block; }
      .b2d-opacity { display: flex; align-items: center; gap: 6px; margin-top: 5px; font-size: 9px; color: #64748b; }
      .b2d-opacity input { flex: 1; accent-color: #38bdf8; height: 3px; cursor: pointer; }
      .b2d-foot {
        padding: 8px 10px; border-top: 1px solid rgba(255,255,255,0.08);
        display: flex; align-items: center; justify-content: space-between; gap: 6px;
        background: rgba(11, 17, 30, 0.9);
      }
      .b2d-btn {
        flex: 1; padding: 5px 8px; border-radius: 6px; font-size: 9.5px; font-weight: 700;
        cursor: pointer; border: 1px solid rgba(255,255,255,0.1);
        background: rgba(15, 23, 42, 0.9); color: #cbd5e1;
      }
      .b2d-btn:hover { border-color: rgba(56, 189, 248, 0.45); color: #38bdf8; }
      .b2d-status-bar { font-size: 9px; color: #64748b; padding: 4px 10px; border-top: 1px solid rgba(255,255,255,0.05); }
    `;
    document.head.appendChild(style);

    // Floating button
    const fab = document.createElement('button');
    fab.id = 'bhu-2d-layer-fab';
    fab.type = 'button';
    fab.innerHTML = `<i class="fa-solid fa-layer-group" style="color:#38bdf8;"></i><span>2D LAYERS</span><span class="b2d-count" id="b2d-active-count">0</span>`;
    document.body.appendChild(fab);

    // Floating drawer
    const panel = document.createElement('div');
    panel.id = 'bhu-2d-layer-panel';
    panel.innerHTML = `
      <div class="b2d-head">
        <div style="display:flex;align-items:center;gap:7px;">
          <i class="fa-solid fa-layer-group" style="color:#38bdf8;font-size:11px;"></i>
          <span style="font-size:11px;font-weight:700;color:#f1f5f9;">2D EARTH LAYERS (14)</span>
        </div>
        <button type="button" id="b2d-close-btn" style="background:transparent;border:none;color:#94a3b8;cursor:pointer;font-size:12px;">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
      <div class="b2d-list" id="b2d-layer-list"></div>
      <div class="b2d-status-bar" id="b2d-status-bar">Synced with 3D Earth &amp; Urban Studio</div>
      <div class="b2d-foot">
        <button type="button" class="b2d-btn" id="b2d-refresh-btn"><i class="fa-solid fa-rotate" style="margin-right:4px;"></i>Refresh View</button>
        <button type="button" class="b2d-btn" id="b2d-clear-btn"><i class="fa-solid fa-broom" style="margin-right:4px;"></i>Clear All</button>
      </div>
    `;
    document.body.appendChild(panel);

    fab.onclick = () => panel.classList.toggle('open');
    document.getElementById('b2d-close-btn').onclick = () => panel.classList.remove('open');

    const statusBar = document.getElementById('b2d-status-bar');
    const setStatus = (msg, color = '#94a3b8') => {
      if (statusBar) { statusBar.textContent = msg; statusBar.style.color = color; }
    };

    // Build layer rows
    const listEl = document.getElementById('b2d-layer-list');
    LAYER_CATALOG.forEach((meta) => {
      const st = reg.get(meta.id);
      const isUnavail = meta.provider === 'unavailable';
      const row = document.createElement('div');
      row.className = 'b2d-row';
      row.innerHTML = `
        <div class="b2d-row-top">
          <div class="b2d-row-title" title="${meta.name}">
            <span class="b2d-dot" style="background:${meta.color};"></span>
            <i class="fa-solid ${meta.icon}" style="color:${meta.color};font-size:10px;width:12px;text-align:center;"></i>
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${meta.name}</span>
          </div>
          <span class="b2d-badge b2d-st-${meta.status}" id="b2d-badge-${meta.id}">${meta.status}</span>
          <button type="button" class="b2d-info-btn" data-info="${meta.id}" title="Layer metadata &amp; provenance">
            <i class="fa-solid fa-info"></i>
          </button>
          <input type="checkbox" id="b2d-chk-${meta.id}" ${st.enabled ? 'checked' : ''} ${isUnavail ? 'disabled' : ''}
            style="accent-color:#38bdf8;cursor:${isUnavail ? 'not-allowed' : 'pointer'};">
        </div>
        <div class="b2d-opacity" id="b2d-op-wrap-${meta.id}" style="display:${st.enabled ? 'flex' : 'none'};">
          <span>Opacity</span>
          <input type="range" min="0.1" max="1" step="0.05" value="${st.opacity}" id="b2d-op-${meta.id}">
          <span id="b2d-op-val-${meta.id}">${Math.round(st.opacity * 100)}%</span>
        </div>
        <div class="b2d-meta" id="b2d-meta-${meta.id}">
          <div><strong style="color:#e2e8f0;">Source:</strong> ${meta.source}</div>
          <div><strong style="color:#e2e8f0;">Observation:</strong> ${meta.obsDate} &middot; <strong style="color:#e2e8f0;">Res:</strong> ${meta.resolution}</div>
          <div><strong style="color:#e2e8f0;">Processing:</strong> ${meta.procDate}</div>
          <div><strong style="color:#e2e8f0;">Legend:</strong> ${meta.legend}</div>
        </div>
      `;
      listEl.appendChild(row);

      row.querySelector(`[data-info="${meta.id}"]`).onclick = () => {
        const mEl = document.getElementById(`b2d-meta-${meta.id}`);
        if (mEl) mEl.classList.toggle('show');
      };

      const chk = document.getElementById(`b2d-chk-${meta.id}`);
      const opWrap = document.getElementById(`b2d-op-wrap-${meta.id}`);
      const opRange = document.getElementById(`b2d-op-${meta.id}`);
      const opVal = document.getElementById(`b2d-op-val-${meta.id}`);

      chk.onchange = async () => {
        reg.set(meta.id, { enabled: chk.checked });
        opWrap.style.display = chk.checked ? 'flex' : 'none';
        await syncLayerToMap(meta.id);
        updateActiveCount();
      };

      opRange.oninput = () => {
        const val = parseFloat(opRange.value);
        opVal.textContent = `${Math.round(val * 100)}%`;
        reg.set(meta.id, { opacity: val });
        applyOpacityToLayer(meta.id, val);
      };
    });

    function updateActiveCount() {
      const cnt = LAYER_CATALOG.filter((m) => reg.get(m.id).enabled).length;
      const el = document.getElementById('b2d-active-count');
      if (el) el.textContent = String(cnt);
    }

    function setBadge(id, status) {
      const el = document.getElementById(`b2d-badge-${id}`);
      if (!el) return;
      el.textContent = status;
      el.className = `b2d-badge b2d-st-${status}`;
    }

    function applyOpacityToLayer(id, opacity) {
      const lyr = leafletLayers[id];
      if (!lyr) return;
      if (typeof lyr.setOpacity === 'function') lyr.setOpacity(opacity);
      else if (typeof lyr.setStyle === 'function') lyr.setStyle({ opacity, fillOpacity: opacity * 0.6 });
    }

    async function fetchOsmForViewport() {
      if (map.getZoom() < 13) {
        setStatus('Zoom in to level 13+ for OSM vector layers', '#fbbf24');
        return null;
      }
      const b = map.getBounds();
      const key = `${b.getSouth().toFixed(3)},${b.getWest().toFixed(3)},${b.getNorth().toFixed(3)},${b.getEast().toFixed(3)}`;
      if (osmCache.key === key && osmCache.data) return osmCache.data;
      setStatus('Fetching real OSM vectors (OSM API v0.6)...', '#38bdf8');
      const c = map.getCenter();
      const halfLat = Math.min((b.getNorth() - b.getSouth()) / 2, 0.008);
      const halfLon = Math.min((b.getEast() - b.getWest()) / 2, 0.009);
      const bboxParam = `${(c.lng - halfLon).toFixed(5)},${(c.lat - halfLat).toFixed(5)},${(c.lng + halfLon).toFixed(5)},${(c.lat + halfLat).toFixed(5)}`;
      try {
        const resp = await fetch(`https://api.openstreetmap.org/api/0.6/map.json?bbox=${bboxParam}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        const nodes = {};
        json.elements.forEach((el) => { if (el.type === 'node') nodes[el.id] = [el.lon, el.lat]; });
        const buckets = { building: [], road: [], water: [], greenery: [], infrastructure: [] };
        json.elements.forEach((el) => {
          const tags = el.tags || {};
            if (el.type === 'node' && (tags.amenity || tags.railway || tags.power)) {
              buckets.infrastructure.push({
                type: 'Feature', properties: tags,
                geometry: { type: 'Point', coordinates: [el.lon, el.lat] }
              });
            } else if (el.type === 'way' && el.nodes) {
              const coords = el.nodes.map((id) => nodes[id]).filter(Boolean);
              if (coords.length < 2) return;
              const closed = coords.length >= 4 && coords[0][0] === coords[coords.length - 1][0] && coords[0][1] === coords[coords.length - 1][1];
              const geom = closed ? { type: 'Polygon', coordinates: [coords] } : { type: 'LineString', coordinates: coords };
              if (tags.building) buckets.building.push({ type: 'Feature', properties: tags, geometry: geom });
              else if (tags.highway) buckets.road.push({ type: 'Feature', properties: tags, geometry: geom });
              else if (tags.waterway || tags.natural === 'water' || tags.water) buckets.water.push({ type: 'Feature', properties: tags, geometry: geom });
              else if (['park', 'garden', 'pitch'].includes(tags.leisure) || tags.natural === 'wood' || ['forest', 'grass'].includes(tags.landuse)) buckets.greenery.push({ type: 'Feature', properties: tags, geometry: geom });
              else if (tags.amenity) buckets.infrastructure.push({ type: 'Feature', properties: tags, geometry: geom });
            }
          });
        osmCache = { key, data: buckets };
        const total = Object.values(buckets).reduce((s, a) => s + a.length, 0);
        setStatus(`OSM API v0.6 loaded: ${total} observed features`, '#34d399');
        return buckets;
      } catch (err) {
        setStatus(`OSM API error: ${err.message}`, '#f87171');
        return null;
      }
    }

    async function fetchDemForViewport() {
      const c = map.getCenter();
      const b = map.getBounds();
      const span = Math.min(0.25, Math.max(0.01, b.getNorth() - b.getSouth()));
      const key = `${c.lat.toFixed(3)},${c.lng.toFixed(3)},${span.toFixed(3)}`;
      if (demCache.key === key && demCache.data) return demCache.data;
      setStatus('Fetching Copernicus DEM elevation grid...', '#38bdf8');
      if (window.BhuLokaSiteStudio && typeof window.BhuLokaSiteStudio.fetchDemGrid10x10 === 'function') {
        const dem = await window.BhuLokaSiteStudio.fetchDemGrid10x10(c.lat, c.lng, span, '2D Viewport');
        if (dem) {
          demCache = { key, data: dem };
          setStatus(`DEM loaded: ${dem.metrics.min_m}m – ${dem.metrics.max_m}m AMSL`, '#34d399');
          return dem;
        }
      }
      setStatus('DEM endpoint unavailable', '#f87171');
      return null;
    }

    function buildDemOverlay(dem, mode, opacity) {
      const mat = dem.elev_matrix;
      const gN = mat.length;
      const { south, north, west, east } = dem.bounds;
      const dLat = (north - south) / gN;
      const dLon = (east - west) / gN;
      const mn = dem.metrics.min_m;
      const mx = Math.max(mn + 1, dem.metrics.max_m);
      const group = L.layerGroup();

      for (let r = 0; r < gN; r++) {
        for (let c = 0; c < gN; c++) {
          const val = mat[r][c];
          const t = (val - mn) / (mx - mn);
          const cellNorth = north - r * dLat;
          const cellSouth = cellNorth - dLat;
          const cellWest = west + c * dLon;
          const cellEast = cellWest + dLon;
          let fill = null;
          if (mode === 'dem') {
            fill = t < 0.33 ? '#1e4631' : t < 0.66 ? '#4d7c4f' : '#b48a4e';
          } else if (mode === 'flood' || mode === 'sar') {
            if (t <= 0.28) fill = mode === 'sar' ? '#eab308' : '#0284c7';
          } else if (mode === 'safezone') {
            if (t >= 0.68) fill = '#059669';
          }
          if (!fill) continue;
          L.rectangle([[cellSouth, cellWest], [cellNorth, cellEast]], {
            color: fill, weight: 0.4, opacity: opacity * 0.6,
            fillColor: fill, fillOpacity: opacity * 0.55
          }).bindTooltip(`${val.toFixed(1)} m AMSL (${mode.toUpperCase()})`).addTo(group);
        }
      }
      return group;
    }

    async function syncLayerToMap(id) {
      const meta = reg.getMeta(id);
      const st = reg.get(id);
      if (leafletLayers[id]) {
        map.removeLayer(leafletLayers[id]);
        delete leafletLayers[id];
      }
      if (!st.enabled || !meta || meta.provider === 'unavailable') return;

      if (meta.provider === 'wms') {
        leafletLayers[id] = L.tileLayer.wms(meta.wmsUrl, {
          layers: meta.wmsLayers, format: 'image/png', transparent: true,
          opacity: st.opacity, attribution: meta.source
        }).addTo(map);
        setBadge(id, meta.status);
      } else if (meta.provider === 'osm') {
        const buckets = await fetchOsmForViewport();
        if (!buckets) { setBadge(id, 'UNAVAILABLE'); return; }
        const feats = buckets[meta.osmKey] || [];
        if (!feats.length) {
          setBadge(id, 'UNAVAILABLE');
          setStatus(`No ${meta.name} mapped in OSM for this extent`, '#94a3b8');
          return;
        }
        const styleMap = {
          building: { color: '#94a3b8', weight: 1, fillColor: '#334155', fillOpacity: st.opacity * 0.65 },
          road: { color: '#e2e8f0', weight: 1.8, opacity: st.opacity },
          water: { color: '#0284c7', weight: 1.2, fillColor: '#0284c7', fillOpacity: st.opacity * 0.55 },
          greenery: { color: '#059669', weight: 1, fillColor: '#059669', fillOpacity: st.opacity * 0.5 }
        };
        leafletLayers[id] = L.geoJSON({ type: 'FeatureCollection', features: feats }, {
          style: () => styleMap[meta.osmKey] || { color: meta.color, weight: 1.5, opacity: st.opacity },
          pointToLayer: (f, latlng) => L.circleMarker(latlng, {
            radius: 5, color: '#38bdf8', fillColor: '#0284c7', fillOpacity: st.opacity, weight: 1.5
          }),
          onEachFeature: (f, lyr) => {
            const p = f.properties || {};
            const label = p.name || p.highway || p.building || p.amenity || meta.name;
            lyr.bindTooltip(`${label} (${meta.name})`, { sticky: true });
          }
        }).addTo(map);
        setBadge(id, 'OBSERVED');
      } else if (meta.provider === 'dem_grid' || meta.provider === 'dem_derived') {
        const dem = await fetchDemForViewport();
        if (!dem) { setBadge(id, 'UNAVAILABLE'); return; }
        leafletLayers[id] = buildDemOverlay(dem, id, st.opacity).addTo(map);
        setBadge(id, meta.status);
      } else if (meta.provider === 'composite') {
        const dem = await fetchDemForViewport();
        const grp = L.layerGroup();
        if (dem) buildDemOverlay(dem, 'flood', st.opacity).addTo(grp);
        L.tileLayer.wms('https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi', {
          layers: 'MODIS_Terra_Land_Surface_Temp_Day', format: 'image/png', transparent: true, opacity: st.opacity * 0.65
        }).addTo(grp);
        leafletLayers[id] = grp.addTo(map);
        setBadge(id, 'DERIVED');
      }
    }

    document.getElementById('b2d-refresh-btn').onclick = async () => {
      osmCache = { key: null, data: null };
      demCache = { key: null, data: null };
      for (const m of LAYER_CATALOG) {
        if (reg.get(m.id).enabled) await syncLayerToMap(m.id);
      }
    };

    document.getElementById('b2d-clear-btn').onclick = () => {
      LAYER_CATALOG.forEach((m) => {
        reg.set(m.id, { enabled: false });
        const chk = document.getElementById(`b2d-chk-${m.id}`);
        if (chk) chk.checked = false;
        const opWrap = document.getElementById(`b2d-op-wrap-${m.id}`);
        if (opWrap) opWrap.style.display = 'none';
        if (leafletLayers[m.id]) { map.removeLayer(leafletLayers[m.id]); delete leafletLayers[m.id]; }
      });
      updateActiveCount();
      setStatus('All 2D overlay layers cleared', '#94a3b8');
    };

    // Restore previously active shared layers on load
    updateActiveCount();
    LAYER_CATALOG.forEach((m) => {
      if (reg.get(m.id).enabled) syncLayerToMap(m.id);
    });
  }

  window.initBhuLoka2DLayerPanel = init2DLayerPanel;
})(window);
