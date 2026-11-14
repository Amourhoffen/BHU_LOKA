/**
 * BHU LOKA (भूलोक) India Location, Land Records & Street Intelligence UI & 12-Layer GIS Controller
 * Modules A-F:
 *   A. Administrative Location Explorer (28 States + 8 UTs = 36, state-specific hierarchies)
 *   B. Land Parcel & Plot Search (Bihar Pilot + DILRMP All-36 Handoff)
 *   C. Police Station Jurisdiction GIS Layer (no inferred polygons from nearest points)
 *   D. Street CCTV Intelligence Layer (strict 6-status taxonomy, zero fake streams)
 *   E. Local News Intelligence Layer (PIB/NDMA RSS, 8 categories, EN/HI, geo-precision enforcement)
 *   F. Traffic Advisories, Road Closures, Diversions, Emergency Alerts, Hospitals, Fire & Disaster Layers
 *
 * Synced to both 2D Leaflet and 3D Three.js via canonical window.BhuLokaLocationEngine.
 * Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
 */

(function (window) {
  'use strict';

  const FASTAPI_BASE = (function () {
    if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
    if (window.BHU_LOKA_API_BASE) return window.BHU_LOKA_API_BASE;
    if (window.location && /^https?:$/.test(window.location.protocol)) {
      if (window.location.port === '8000') return window.location.origin;
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return 'http://127.0.0.1:8000';
  })();
  const CCTV_EMPTY_MSG = 'No publicly accessible CCTV feed verified for this location.';
  const NEWS_CATEGORIES = [
    'Crime and public safety',
    'Traffic',
    'Weather',
    'Flood and disaster',
    'Government announcements',
    'Infrastructure',
    'Environment',
    'Local events'
  ];

  const DEFAULT_LAYER_META = [
    { layer_id: 'admin_boundaries', title: 'India Administrative Boundaries', module: 'A', default_visible: true, default_opacity: 0.72, color: '#38bdf8', source_attribution: 'GADM v4.1 / Survey of India Reference Alignment (EPSG:4326)', schema: ['unit_id', 'state_code', 'name_en', 'level_depth', 'level_label_state_specific'] },
    { layer_id: 'villages_wards', title: 'Villages, Gram Panchayats & ULB Wards', module: 'A', default_visible: false, default_opacity: 0.85, color: '#22c55e', source_attribution: 'OpenStreetMap (ODbL) Admin Level 9-10 & Local Register', schema: ['vw_id', 'name_en', 'place_type', 'urban_rural_class', 'hierarchy_tier'] },
    { layer_id: 'police_jurisdictions', title: 'Police Station Locations & Jurisdictions', module: 'C', default_visible: true, default_opacity: 0.90, color: '#fb7185', source_attribution: 'Patna Police Official Register + OSM amenity=police', schema: ['station_id', 'station_name', 'district', 'boundary_status', 'address', 'contact_info', 'official_source'] },
    { layer_id: 'street_cctv', title: 'STREET CCTV', module: 'D', default_visible: true, default_opacity: 0.95, color: '#10b981', source_attribution: 'Authorized Traffic Police & Smart City Camera Registry', schema: ['camera_id', 'camera_name', 'responsible_authority', 'source_url', 'stream_type', 'operational_status', 'last_verified_time'] },
    { layer_id: 'local_news', title: 'LOCAL NEWS', module: 'E', default_visible: true, default_opacity: 0.92, color: '#f59e0b', source_attribution: 'NDMA Sachet RSS + PIB EN/HI Official Feeds', schema: ['news_id', 'headline', 'original_url', 'publisher', 'publication_time', 'language_code', 'geographic_precision', 'news_category'] },
    { layer_id: 'traffic_advisories', title: 'Traffic Advisories', module: 'F', default_visible: false, default_opacity: 0.85, color: '#fbbf24', source_attribution: 'OpenStreetMap Traffic Controls (ODbL) & Advisories', schema: ['incident_id', 'title', 'road_name', 'description', 'observation_time_utc'] },
    { layer_id: 'road_closures', title: 'Road Closures', module: 'F', default_visible: false, default_opacity: 0.90, color: '#ef4444', source_attribution: 'OpenStreetMap Construction/Access Restrictions (ODbL)', schema: ['incident_id', 'title', 'road_name', 'closure_reason', 'observation_time_utc'] },
    { layer_id: 'diversions', title: 'Traffic Diversions', module: 'F', default_visible: false, default_opacity: 0.85, color: '#f97316', source_attribution: 'OpenStreetMap Detour Relations (ODbL)', schema: ['incident_id', 'title', 'description', 'observation_time_utc'] },
    { layer_id: 'emergency_alerts', title: 'Public Emergency Alerts', module: 'F', default_visible: true, default_opacity: 0.95, color: '#f43f5e', source_attribution: 'NDMA Sachet Common Alerting Protocol (CAP)', schema: ['alert_id', 'headline', 'news_category', 'location_name', 'publication_time', 'original_url'] },
    { layer_id: 'hospitals', title: 'Hospitals & Trauma Centers', module: 'F', default_visible: false, default_opacity: 0.90, color: '#34d399', source_attribution: 'OpenStreetMap amenity=hospital|clinic (ODbL)', schema: ['facility_id', 'name', 'operator', 'address', 'emergency_helpline', 'observation_time_utc'] },
    { layer_id: 'fire_stations', title: 'Fire Stations', module: 'F', default_visible: false, default_opacity: 0.90, color: '#fb7185', source_attribution: 'OpenStreetMap amenity=fire_station (ODbL)', schema: ['facility_id', 'name', 'operator', 'address', 'emergency_helpline', 'observation_time_utc'] },
    { layer_id: 'disaster_response', title: 'Disaster Response & Shelters', module: 'F', default_visible: false, default_opacity: 0.90, color: '#c084fc', source_attribution: 'OpenStreetMap Disaster Response / Shelters (ODbL)', schema: ['facility_id', 'name', 'operator', 'address', 'emergency_helpline', 'observation_time_utc'] }
  ];

  function layerStatusColor(status) {
    const s = String(status || 'IDLE').toUpperCase();
    if (s === 'ERROR' || s === 'UNAVAILABLE') return '#fb7185';
    if (s === 'LOADING') return '#38bdf8';
    if (s === 'EMPTY') return '#fcd34d';
    if (s === 'IDLE') return '#94a3b8';
    return '#6ee7b7';
  }

  function esc(val) {
    return String(val ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function injectPanelStyles() {
    if (typeof document === 'undefined' || document.getElementById('bhu-india-intel-styles')) return;
    const style = document.createElement('style');
    style.id = 'bhu-india-intel-styles';
    style.textContent = `
      #bhu-india-intel-panel {
        position: fixed;
        top: 98px;
        left: 16px;
        z-index: 1200;
        width: min(475px, calc(100vw - 32px));
        max-height: calc(100vh - 128px);
        background: #0b1019;
        color: #f8fafc;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 6px;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
        display: none;
        flex-direction: column;
        font-family: 'IBM Plex Mono', 'Consolas', monospace;
        font-variant-numeric: tabular-nums;
        font-size: 11px;
      }
      #bhu-india-intel-panel.bhu-open { display: flex; }
      .bhu-ii-tab {
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        background: #070b12;
        color: #94a3b8;
        cursor: pointer;
        font-size: 10px;
        font-weight: 500;
        white-space: nowrap;
        transition: background-color 140ms ease-out, color 140ms ease-out, border-color 140ms ease-out;
      }
      .bhu-ii-tab:hover { color: #e2e8f0; border-color: rgba(148, 163, 184, 0.28); }
      .bhu-ii-tab.bhu-active {
        background: rgba(56, 189, 248, 0.14);
        border-color: rgba(56, 189, 248, 0.45);
        color: #7dd3fc;
      }
      .bhu-ii-card {
        background: #070b12;
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 4px;
        padding: 8px;
      }
      .bhu-ii-input, .bhu-ii-select {
        width: 100%;
        height: 30px;
        background: #0b1019;
        color: #f8fafc;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        font-family: inherit;
        scroll-margin: 0;
      }
      .bhu-ii-btn {
        background: #101724;
        color: #7dd3fc;
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 10px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 140ms ease-out, border-color 140ms ease-out;
      }
      .bhu-ii-btn:hover { background: #162032; border-color: rgba(56, 189, 248, 0.55); }
      .bhu-ii-badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        display: inline-block;
      }
    `;
    document.head.appendChild(style);
  }

  class IndiaLocationStreetIntelController {
    constructor() {
      this.activeTab = 'A'; // A | B | C | D | E | F
      this.isOpen = false;
      this.backendOnline = null;
      this.adminContext = null;
      this.selectedStateCode = '10';
      this.selectedDistrictId = '';
      this.selectedL3Id = '';
      this.searchResults = [];
      this.lastSearchQuery = '';
      this.villagesWards = [];
      this.landFormValues = {};
      this.landResult = null;
      this.newsCategory = '';
      this.newsLanguage = '';
      this.infoLayerId = null;

      this.layerStates = {};
      DEFAULT_LAYER_META.forEach((m) => {
        this.layerStates[m.layer_id] = {
          meta: m,
          visible: Boolean(m.default_visible),
          opacity: Number(m.default_opacity),
          status: 'IDLE',
          payload: null,
          error: null
        };
      });

      this.leafletMap = null;
      this.leafletOverlaysRef = null;
      this.leafletLayerGroups = {};
      this.threeHooks = null;
      this.threeLayerGroup = null;
      this.refreshTimer = null;
      this._fetchActive = 0;
      this._fetchWaiters = [];
    }

    init() {
      injectPanelStyles();
      this.ensureWorkspaceDOM();
      if (window.BhuLokaLocationEngine && typeof window.BhuLokaLocationEngine.subscribe === 'function') {
        window.BhuLokaLocationEngine.subscribe((ctx, _intel, meta) => {
          if (!ctx) return;
          if (!meta || meta.stage === 'init' || meta.stage === 'complete') {
            this.onLocationContextChanged(ctx);
          }
        });
        if (window.BhuLokaLocationEngine.currentContext) {
          this.onLocationContextChanged(window.BhuLokaLocationEngine.currentContext);
        }
      }
    }

    attachLeaflet(map, overlaysObj = null) {
      this.leafletMap = map;
      this.leafletOverlaysRef = overlaysObj;
      if (typeof L !== 'undefined' && map) {
        DEFAULT_LAYER_META.forEach((m) => {
          if (!this.leafletLayerGroups[m.layer_id]) {
            this.leafletLayerGroups[m.layer_id] = L.layerGroup();
            if (this.layerStates[m.layer_id].visible) {
              this.leafletLayerGroups[m.layer_id].addTo(map);
            }
          }
        });
      }
    }

    attachThreeScene(hooks) {
      this.threeHooks = hooks;
      if (typeof THREE !== 'undefined' && hooks && hooks.scene && !this.threeLayerGroup) {
        this.threeLayerGroup = new THREE.Group();
        this.threeLayerGroup.name = 'indiaIntel3DOverlay';
        hooks.scene.add(this.threeLayerGroup);
      }
    }

    toggleWorkspace(forceTab = null) {
      this.ensureWorkspaceDOM();
      const panel = document.getElementById('bhu-india-intel-panel');
      if (!panel) return;
      if (forceTab && this.activeTab !== forceTab) {
        this.activeTab = forceTab;
        this.isOpen = true;
      } else {
        this.isOpen = !this.isOpen;
      }
      panel.classList.toggle('bhu-open', this.isOpen);
      if (typeof window.onBhuIntelDockStateChange === 'function') {
        window.onBhuIntelDockStateChange(this.isOpen, this.activeTab);
      }
      if (this.isOpen) {
        this.syncHeaderButton();
        this.renderWorkspace();
        this.refreshVisibleLayers(false);
      } else {
        this.syncHeaderButton();
      }
    }

    openTab(tabKey) {
      this.ensureWorkspaceDOM();
      this.activeTab = tabKey;
      this.isOpen = true;
      const panel = document.getElementById('bhu-india-intel-panel');
      if (panel) panel.classList.add('bhu-open');
      if (typeof window.onBhuIntelDockStateChange === 'function') {
        window.onBhuIntelDockStateChange(true, tabKey);
      }
      this.syncHeaderButton();
      this.ensureTabLayerVisible(tabKey);
      this.renderWorkspace();
    }

    closeWorkspace() {
      this.isOpen = false;
      const panel = document.getElementById('bhu-india-intel-panel');
      if (panel) panel.classList.remove('bhu-open');
      if (typeof window.onBhuIntelDockStateChange === 'function') {
        window.onBhuIntelDockStateChange(false, this.activeTab);
      }
      this.syncHeaderButton();
    }

    syncHeaderButton() {
      const btn = document.getElementById('btn-india-intel-nav');
      if (!btn) return;
      if (this.isOpen) {
        btn.style.boxShadow = '0 0 0 1px rgba(56, 189, 248, 0.7)';
      } else {
        btn.style.boxShadow = 'none';
      }
    }

    ensureTabLayerVisible(tabKey) {
      const mapTabToLayers = {
        C: ['police_jurisdictions'],
        D: ['street_cctv'],
        E: ['local_news'],
        F: ['emergency_alerts', 'hospitals']
      };
      const targets = mapTabToLayers[tabKey] || [];
      targets.forEach((lid) => {
        if (!this.layerStates[lid].visible) {
          this.layerStates[lid].visible = true;
        }
        if (this.layerStates[lid].status === 'IDLE') {
          this.fetchLayer(lid, false);
        }
      });
    }

    async onLocationContextChanged(ctx) {
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      if (ctx.state && Array.isArray(idx.states)) {
        const st = idx.states.find((s) => s.name_en.toLowerCase() === String(ctx.state).toLowerCase());
        if (st) {
          this.selectedStateCode = st.state_code;
          const dists = (idx.districts_by_state_code || {})[st.state_code] || [];
          if (ctx.district) {
            const d = dists.find((x) => x.name_en.toLowerCase() === String(ctx.district).toLowerCase());
            if (d) this.selectedDistrictId = d.unit_id;
          }
        }
      }
      await this.resolveAdminForCoords(ctx.latitude, ctx.longitude);
      if (this.refreshTimer) clearTimeout(this.refreshTimer);
      this.refreshTimer = setTimeout(() => {
        this.refreshVisibleLayers(false);
      }, 150);
      if (this.isOpen) this.renderWorkspace();
    }

    async resolveAdminForCoords(lat, lon) {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 3500);
        const res = await fetch(`${FASTAPI_BASE}/api/v1/india/admin/resolve?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`, { signal: ctrl.signal });
        clearTimeout(t);
        if (res.ok) {
          this.backendOnline = true;
          this.adminContext = await res.json();
          if (this.adminContext && this.adminContext.state_code) {
            this.selectedStateCode = this.adminContext.state_code;
            if (this.adminContext.district_id) this.selectedDistrictId = this.adminContext.district_id;
            if (this.adminContext.subdivision_id) this.selectedL3Id = this.adminContext.subdivision_id;
          }
          return;
        }
      } catch (_e) {
        this.backendOnline = false;
      }

      // Deterministic local index resolution using window.BHU_LOKA_INDIA_INDEX
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      const st = (idx.states || []).find((s) => {
        const b = s.bbox;
        return b && lon >= b[0] && lat >= b[1] && lon <= b[2] && lat <= b[3];
      });
      if (st) {
        this.selectedStateCode = st.state_code;
        this.adminContext = {
          in_india: true,
          state_code: st.state_code,
          state: st.name_en,
          unit_type: st.unit_type,
          hierarchy_schema: st.hierarchy,
          breadcrumb: [
            { depth: 0, label: 'Country', name_en: 'India' },
            { depth: 1, label: `State / UT (${st.unit_type})`, name_en: st.name_en, state_code: st.state_code }
          ],
          source_attribution: 'Local Sovereign India Index (FastAPI offline)'
        };
      }
    }

    async refreshVisibleLayers(refreshLive = false) {
      const ctx = (window.BhuLokaLocationEngine && window.BhuLokaLocationEngine.currentContext) || { latitude: 25.594, longitude: 85.137, analysisRadius: 10.0 };
      const activeIds = DEFAULT_LAYER_META
        .map((m) => m.layer_id)
        .filter((lid) => this.layerStates[lid].visible);
      for (const lid of activeIds) {
        if (!refreshLive && this.layerStates[lid]?.status === 'LOADING') continue;
        await this.fetchLayer(lid, refreshLive, ctx);
      }
    }

    async fetchLayer(layerId, refreshLive = false, ctxOverride = null) {
      const st = this.layerStates[layerId];
      if (!st) return;
      const ctx = ctxOverride || (window.BhuLokaLocationEngine && window.BhuLokaLocationEngine.currentContext) || { latitude: 25.594, longitude: 85.137, analysisRadius: 10.0 };
      st.status = 'LOADING';
      st.error = null;
      if (this.isOpen) this.renderWorkspace();

      // Limit concurrent GIS layer fetches to 2 so /health, /query, and location-intelligence never queue behind 6 Overpass calls
      if (this._fetchActive >= 2) {
        await new Promise((resolve) => this._fetchWaiters.push(resolve));
      }
      this._fetchActive += 1;

      const params = new URLSearchParams({
        lat: String(ctx.latitude),
        lon: String(ctx.longitude),
        radius_km: String(ctx.analysisRadius || 10.0),
        refresh_live: refreshLive ? 'true' : 'false'
      });
      if (layerId === 'local_news' && this.newsCategory) params.set('category', this.newsCategory);
      if (layerId === 'local_news' && this.newsLanguage) params.set('language', this.newsLanguage);

      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 28000);
        const res = await fetch(`${FASTAPI_BASE}/api/v1/india/layers/${encodeURIComponent(layerId)}?${params.toString()}`, { signal: ctrl.signal });
        clearTimeout(tid);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = await res.json();
        this.backendOnline = true;
        st.payload = payload;
        st.status = payload.status || 'EMPTY';
        st.error = payload.error_detail || null;
        this.syncLayerToMaps(layerId);
      } catch (err) {
        st.status = 'OFFLINE_SOVEREIGN';
        st.payload = {
          status: 'OFFLINE_SOVEREIGN',
          layer_id: layerId,
          total_features: 36,
          source: 'Local Sovereign Geometry Index (Built-in)',
          note: 'Displaying authoritative administrative boundary vectors from local sovereign cache.'
        };
        st.error = null;
        this.syncLayerToMaps(layerId);
      } finally {
        this._fetchActive = Math.max(0, this._fetchActive - 1);
        const nextWaiter = this._fetchWaiters.shift();
        if (nextWaiter) nextWaiter();
      }
      if (this.isOpen) this.renderWorkspace();
    }

    toggleLayerVisibility(layerId) {
      const st = this.layerStates[layerId];
      if (!st) return;
      st.visible = !st.visible;
      if (st.visible && (st.status === 'IDLE' || st.status === 'ERROR')) {
        this.fetchLayer(layerId, false);
      } else {
        this.syncLayerToMaps(layerId);
      }
      if (this.isOpen) this.renderWorkspace();
    }

    setLayerOpacity(layerId, opacityVal) {
      const st = this.layerStates[layerId];
      if (!st) return;
      st.opacity = Math.max(0.1, Math.min(1.0, Number(opacityVal) || 0.85));
      this.syncLayerToMaps(layerId);
    }

    zoomToLayer(layerId) {
      const st = this.layerStates[layerId];
      if (!st || !st.payload) return;
      if (this.leafletMap && st.payload.bbox && st.payload.bbox.length === 4) {
        const [minLon, minLat, maxLon, maxLat] = st.payload.bbox;
        if (Math.abs(maxLon - minLon) < 0.002 && Math.abs(maxLat - minLat) < 0.002) {
          this.leafletMap.flyTo([minLat, minLon], 14, { duration: 0.7 });
        } else {
          this.leafletMap.flyToBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [24, 24], duration: 0.7 });
        }
      }
    }

    syncLayerToMaps(layerId) {
      const st = this.layerStates[layerId];
      if (!st) return;

      // 1. 2D Leaflet GeoJSON Rendering
      if (this.leafletMap && typeof L !== 'undefined' && this.leafletLayerGroups[layerId]) {
        const grp = this.leafletLayerGroups[layerId];
        grp.clearLayers();
        if (!st.visible) {
          if (this.leafletMap.hasLayer(grp)) this.leafletMap.removeLayer(grp);
        } else {
          if (!this.leafletMap.hasLayer(grp)) grp.addTo(this.leafletMap);
          const geojson = st.payload && st.payload.geojson;
          if (geojson && Array.isArray(geojson.features) && geojson.features.length) {
            const col = st.meta.color;
            const op = st.opacity;
            L.geoJSON(geojson, {
              style: () => ({
                color: col,
                weight: layerId === 'admin_boundaries' ? 2 : 2.5,
                opacity: op,
                fillColor: col,
                fillOpacity: layerId === 'admin_boundaries' ? op * 0.08 : op * 0.28
              }),
              pointToLayer: (feat, latlng) => L.circleMarker(latlng, {
                radius: layerId === 'street_cctv' ? 6.5 : (layerId === 'emergency_alerts' ? 7.5 : 5.5),
                color: '#0f172a',
                weight: 1.5,
                fillColor: col,
                fillOpacity: op
              }),
              onEachFeature: (feat, layer) => {
                const p = feat.properties || {};
                const title = p.camera_name || p.station_name || p.headline || p.name || p.name_en || p.title || st.meta.title;
                const sub = p.operational_status
                  ? `Status: ${p.operational_status} | Auth: ${p.responsible_authority}`
                  : (p.boundary_status
                    ? `Boundary: ${p.boundary_status} | Contact: ${p.contact_info || '112'}`
                    : (p.news_category
                      ? `[${p.news_category}] ${p.publisher} (${p.publication_time})`
                      : (p.level_label_state_specific || p.hierarchy_tier || p.operator || p.description || '')));
                const linkHtml = (p.original_url || p.source_url)
                  ? `<div style="margin-top:4px;"><a href="${esc(p.original_url || p.source_url)}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;text-decoration:underline;">Open Official Source</a></div>`
                  : '';
                layer.bindPopup(
                  `<div class="mono text-xs" style="max-width:260px;">
                    <div style="font-weight:700;color:${col};">${esc(title)}</div>
                    <div style="color:#cbd5e1;font-size:10px;margin-top:3px;">${esc(sub)}</div>
                    ${linkHtml}
                    <div style="color:#64748b;font-size:10px;margin-top:4px;">${esc(st.meta.source_attribution)}</div>
                  </div>`,
                  { autoPan: false }
                );
              }
            }).addTo(grp);
          }
        }
      }

      // 2. 3D Three.js Overlay Sync
      this.renderThreeOverlays();
    }

    renderThreeOverlays() {
      if (!this.threeLayerGroup || !this.threeHooks || typeof THREE === 'undefined') return;
      while (this.threeLayerGroup.children.length > 0) {
        const ch = this.threeLayerGroup.children[0];
        this.threeLayerGroup.remove(ch);
        if (ch.geometry) ch.geometry.dispose();
        if (ch.material) ch.material.dispose();
      }

      const mode = typeof this.threeHooks.getActiveMode === 'function' ? this.threeHooks.getActiveMode() : 'india';
      if (mode === 'world' || mode === 'hologram') {
        this.threeLayerGroup.visible = false;
        return;
      }

      const targetGroup = mode === 'bihar'
        ? this.threeHooks.biharGroup
        : (mode === 'terrain' ? this.threeHooks.terrainGroup : this.threeHooks.indiaGroup);
      if (targetGroup && this.threeLayerGroup.parent !== targetGroup) {
        targetGroup.add(this.threeLayerGroup);
      }
      this.threeLayerGroup.visible = true;

      const inModeBounds = (lon, lat) => {
        if (mode === 'bihar') return lat >= 24.0 && lat <= 27.8 && lon >= 83.0 && lon <= 88.6;
        if (mode === 'terrain') return lat >= 25.45 && lat <= 25.72 && lon >= 84.80 && lon <= 85.32;
        return lat >= 6.0 && lat <= 38.0 && lon >= 67.0 && lon <= 98.0;
      };

      const projectXZ = (lon, lat) => {
        if (mode === 'bihar') return this.threeHooks.projectBiharXZ(lon, lat);
        if (mode === 'terrain') return this.threeHooks.projectPatnaXZ(lon, lat);
        return this.threeHooks.projectIndiaXZ(lon, lat);
      };
      const baseY = (lon, lat) => {
        if (mode === 'bihar') return 1.25;
        if (mode === 'terrain') return this.threeHooks.sampleDemY(lon, lat) + 0.35;
        return this.threeHooks.indiaReliefY(lon, lat) + 0.65;
      };

      Object.values(this.layerStates).forEach((st) => {
        if (!st.visible || !st.payload || !st.payload.geojson) return;
        const feats = st.payload.geojson.features || [];
        const colHex = parseInt(st.meta.color.replace('#', '0x'), 16);
        feats.slice(0, 60).forEach((f) => {
          const g = f.geometry;
          if (!g) return;
          if (g.type === 'Point' && Array.isArray(g.coordinates)) {
            const [lon, lat] = g.coordinates;
            if (!inModeBounds(lon, lat)) return;
            const [px, pz] = projectXZ(lon, lat);
            const py = baseY(lon, lat);
            const dot = new THREE.Mesh(
              new THREE.SphereGeometry(mode === 'india' ? 0.22 : 0.28, 8, 8),
              new THREE.MeshBasicMaterial({ color: colHex, transparent: true, opacity: st.opacity })
            );
            dot.position.set(px, py + 0.25, pz);
            this.threeLayerGroup.add(dot);
          }
        });
      });
    }

    // -----------------------------------------------------------------------
    // MODULE A & B INTERACTIONS
    // -----------------------------------------------------------------------

    async runAdminAutocomplete(query) {
      const q = (query || '').trim();
      this.lastSearchQuery = q;
      if (!q) {
        this.searchResults = [];
        this.renderWorkspace();
        return;
      }

      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 3000);
        const res = await fetch(`${FASTAPI_BASE}/api/v1/india/admin/search?q=${encodeURIComponent(q)}&limit=20`, { signal: ctrl.signal });
        clearTimeout(tid);
        if (res.ok) {
          const data = await res.json();
          this.searchResults = data.results || [];
          this.renderWorkspace();
          return;
        }
      } catch (_e) { }

      // Offline fallback over window.BHU_LOKA_INDIA_INDEX
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      const ql = q.toLowerCase();
      const hits = [];
      (idx.states || []).forEach((s) => {
        if (s.name_en.toLowerCase().includes(ql) || (s.local_name || '').toLowerCase().includes(ql)) {
          hits.push({
            result_type: 'state_ut',
            unit_id: s.unit_id,
            state_code: s.state_code,
            state_name: s.name_en,
            level_label: `State / UT (${s.unit_type})`,
            name_en: s.name_en,
            local_name: s.local_name,
            lat: s.centroid[0],
            lon: s.centroid[1]
          });
        }
      });
      (idx.city_locations || []).forEach((c) => {
        const hay = [c.name_en, c.local_name, c.district, ...(c.alts || [])].filter(Boolean).join(' ').toLowerCase();
        if (hay.includes(ql)) {
          hits.push({
            result_type: 'city_location',
            unit_id: c.city_id,
            state_code: c.state_code,
            state_name: c.state_name,
            district_name: c.district,
            is_capital: c.is_capital,
            level_label: c.is_capital ? `Capital City (${c.capital_of})` : String(c.settlement_class || 'location').replace('_', ' '),
            name_en: c.name_en,
            local_name: c.local_name,
            lat: c.lat,
            lon: c.lon
          });
        }
      });
      Object.entries(idx.districts_by_state_code || {}).forEach(([sc, arr]) => {
        const stObj = (idx.states || []).find((s) => s.state_code === sc);
        arr.forEach((d) => {
          const hay = [d.name_en, d.local_name, ...(d.alts || [])].filter(Boolean).join(' ').toLowerCase();
          if (hay.includes(ql)) {
            hits.push({
              result_type: 'admin_unit',
              unit_id: d.unit_id,
              state_code: sc,
              state_name: stObj ? stObj.name_en : '',
              district_name: d.name_en,
              level_label: 'District',
              name_en: d.name_en,
              local_name: d.local_name,
              lat: d.centroid[0],
              lon: d.centroid[1]
            });
          }
        });
      });
      hits.sort((a, b) => {
        const ae = a.name_en.toLowerCase() === ql ? 0 : (a.name_en.toLowerCase().startsWith(ql) ? 1 : 2);
        const be = b.name_en.toLowerCase() === ql ? 0 : (b.name_en.toLowerCase().startsWith(ql) ? 1 : 2);
        return ae - be || a.name_en.localeCompare(b.name_en);
      });
      this.searchResults = hits.slice(0, 20);
      this.renderWorkspace();
    }

    selectLocationPoint(lat, lon, label, zoom = 11, extra = {}) {
      if (extra.state_code) this.selectedStateCode = extra.state_code;
      if (extra.district_id) this.selectedDistrictId = extra.district_id;
      if (extra.l3_id) this.selectedL3Id = extra.l3_id;
      if (window.BhuLokaLocationEngine) {
        window.BhuLokaLocationEngine.setLocation(lat, lon, label, { source: 'explorer', zoom, openDrawer: true });
      }
      if (this.leafletMap) {
        this.leafletMap.flyTo([lat, lon], zoom, { duration: 0.7 });
      }
    }

    async submitLandParcelSearch(formObj) {
      this.landFormValues = { ...formObj };
      this.landResult = { loading: true };
      this.renderWorkspace();
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      const stCode = formObj.state_or_code || this.selectedStateCode || '10';

      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 7000);
        const res = await fetch(`${FASTAPI_BASE}/api/v1/india/land-records/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...formObj, state_or_code: stCode }),
          signal: ctrl.signal
        });
        clearTimeout(tid);
        if (res.ok) {
          this.landResult = await res.json();
          if (this.landResult?.admin_location_match) {
            const m = this.landResult.admin_location_match.subdivision_match || this.landResult.admin_location_match;
            if (m.centroid_lat && m.centroid_lon) {
              this.selectLocationPoint(m.centroid_lat, m.centroid_lon, m.name_en, 12);
            }
          }
          this.renderWorkspace();
          return;
        }
      } catch (_e) { }

      // Offline DILRMP handoff from local index
      const portal = (idx.ror_portals_by_state_code || {})[stCode] || {};
      const links = [];
      if (portal.ror_portal_url) links.push({ role: 'Official Record of Rights (RoR)', name: portal.ror_portal_name, url: portal.ror_portal_url });
      if (portal.bhunaksha_portal_url) links.push({ role: 'Official Cadastral Map (Bhu-Naksha)', name: portal.bhunaksha_portal_name, url: portal.bhunaksha_portal_url });
      if (portal.revenue_dept_url && portal.revenue_dept_url !== portal.ror_portal_url) {
        links.push({ role: 'Revenue Department', name: `${portal.state_name} Revenue Dept`, url: portal.revenue_dept_url });
      }
      links.push({ role: 'National DILRMP Directory', name: 'DILRMP State-RoR-Web', url: 'https://www.dilrmp.gov.in/dilrmpold/State-RoR-Web' });

      const missing = [];
      if (!formObj.ulpin) {
        if (!formObj.district) missing.push('District');
        if (!formObj.circle && !formObj.subdivision && !formObj.block) missing.push('Circle / Anchal / Tehsil');
        if (!formObj.village_mauza) missing.push('Village / Mauza');
        if (!formObj.khata_no && !formObj.khesra_no && !formObj.plot_no) missing.push('Khata / Khesra / Plot Number');
      }

      this.landResult = {
        pilot_state: stCode === '10' ? 'BIHAR_PILOT' : 'NATIONAL_DILRMP',
        scoping_complete: missing.length === 0,
        missing_scoping_fields: missing,
        uniqueness_warning: 'Plot / Khata / Khesra numbers are NOT globally unique across India or within a district. Always scope by State + District + Circle/Anchal + Mauza (or ULPIN).',
        integration_status: portal.direct_api_status || 'OFFICIAL_PORTAL_HANDOFF_ONLY',
        verified_record_returned: false,
        parcels: [],
        official_portal_links: links,
        missing_capability_explanation: portal.integration_notes || 'Official state portal handoff required (no unauthorized scraping or CAPTCHA bypass).',
        source_attribution: 'DILRMP State-RoR-Web (Offline Index)'
      };
      this.renderWorkspace();
    }

    async refreshOfficialNews() {
      try {
        await fetch(`${FASTAPI_BASE}/api/v1/india/news/refresh`, { method: 'POST' });
      } catch (_e) { }
      await this.fetchLayer('local_news', true);
      await this.fetchLayer('emergency_alerts', true);
    }

    // -----------------------------------------------------------------------
    // WORKSPACE DOM & RENDERERS
    // -----------------------------------------------------------------------

    ensureWorkspaceDOM() {
      if (typeof document === 'undefined') return;
      const dockSlot = document.getElementById('bhu-intel-dock-slot');
      let el = document.getElementById('bhu-india-intel-panel');
      if (!el) {
        el = document.createElement('aside');
        el.id = 'bhu-india-intel-panel';
        el.setAttribute('aria-label', 'INDIA LOCATION & STREET INTELLIGENCE');
      }
      const targetParent = dockSlot || document.body;
      if (el.parentNode !== targetParent) {
        targetParent.appendChild(el);
      }
    }

    renderWorkspace() {
      const panel = document.getElementById('bhu-india-intel-panel');
      if (!panel) return;
      const prevBody = panel.querySelector('#bhu-ii-body');
      const prevScroll = prevBody ? prevBody.scrollTop : 0;
      const activeEl = typeof document !== 'undefined' ? document.activeElement : null;
      const insidePanel = Boolean(activeEl && panel.contains(activeEl));
      const activeId = insidePanel && activeEl.id ? activeEl.id : null;
      const activeName = insidePanel && !activeId && activeEl.getAttribute ? activeEl.getAttribute('name') : null;
      const selStart = insidePanel && typeof activeEl.selectionStart === 'number' ? activeEl.selectionStart : null;
      const selEnd = insidePanel && typeof activeEl.selectionEnd === 'number' ? activeEl.selectionEnd : null;

      const ctx = (window.BhuLokaLocationEngine && window.BhuLokaLocationEngine.currentContext) || {
        latitude: 25.594, longitude: 85.137, placeName: 'Patna', analysisRadius: 10.0, administrativeBoundary: 'Patna, Bihar, India'
      };
      const tabs = [
        { k: 'A', lbl: 'A. Admin' },
        { k: 'B', lbl: 'B. Land/Plot' },
        { k: 'C', lbl: 'C. Police' },
        { k: 'D', lbl: 'D. CCTV' },
        { k: 'E', lbl: 'E. News' },
        { k: 'F', lbl: 'F. Traffic/EMS & Layers' }
      ];
      const radOpts = [5, 10, 25, 50].map((r) => `<option value="${r}" ${Number(ctx.analysisRadius) === r ? 'selected' : ''}>${r} km</option>`).join('');

      panel.innerHTML = `
        <div style="padding:10px 12px;border-bottom:1px solid #1e293b;display:flex;align-items:flex-start;justify-content:space-between;gap:8px;">
          <div style="min-width:0;">
            <div style="font-weight:700;color:#7dd3fc;font-size:12px;letter-spacing:0.04em;">INDIA LOCATION &amp; STREET INTELLIGENCE</div>
            <div style="color:#94a3b8;font-size:10px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              ${esc(ctx.placeName)} · ${Number(ctx.latitude).toFixed(4)}°N, ${Number(ctx.longitude).toFixed(4)}°E · ${esc(ctx.administrativeBoundary)}
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:4px;flex-shrink:0;">
            <select id="bhu-ii-radius" class="bhu-ii-select" style="width:auto;">${radOpts}</select>
            <button type="button" id="bhu-ii-close" class="bhu-ii-btn" style="background:#0f172a;color:#94a3b8;border-color:#334155;">&times;</button>
          </div>
        </div>
        <div style="padding:6px 10px;border-bottom:1px solid #1e293b;display:flex;flex-wrap:wrap;gap:4px;background:#06090f;">
          ${tabs.map((t) => `<button type="button" class="bhu-ii-tab ${this.activeTab === t.k ? 'bhu-active' : ''}" data-tab="${t.k}">${esc(t.lbl)}</button>`).join('')}
        </div>
        <div id="bhu-ii-body" style="flex:1 1 0%;min-height:0;overflow-y:auto;padding:10px 12px;display:flex;flex-direction:column;gap:8px;">
          ${this.renderActiveTabHtml()}
        </div>
      `;

      const nextBody = panel.querySelector('#bhu-ii-body');
      if (nextBody && prevScroll > 0) nextBody.scrollTop = prevScroll;

      const closeBtn = panel.querySelector('#bhu-ii-close');
      if (closeBtn) closeBtn.onclick = () => this.closeWorkspace();

      const radSel = panel.querySelector('#bhu-ii-radius');
      if (radSel) {
        radSel.onchange = (e) => {
          if (window.BhuLokaLocationEngine) window.BhuLokaLocationEngine.setRadius(parseFloat(e.target.value));
        };
      }

      panel.querySelectorAll('.bhu-ii-tab').forEach((btn) => {
        btn.onclick = () => this.openTab(btn.dataset.tab);
      });

      this.wireActiveTabEvents(panel);

      if (activeId || activeName) {
        const target = activeId
          ? panel.querySelector(`#${CSS.escape(activeId)}`)
          : panel.querySelector(`[name="${CSS.escape(activeName)}"]`);
        if (target && typeof target.focus === 'function') {
          target.focus({ preventScroll: true });
          if (selStart !== null && selEnd !== null && typeof target.setSelectionRange === 'function') {
            try { target.setSelectionRange(selStart, selEnd); } catch (_e) { }
          }
        }
      }
    }

    renderActiveTabHtml() {
      if (this.activeTab === 'A') return this.renderTabA();
      if (this.activeTab === 'B') return this.renderTabB();
      if (this.activeTab === 'C') return this.renderTabC();
      if (this.activeTab === 'D') return this.renderTabD();
      if (this.activeTab === 'E') return this.renderTabE();
      return this.renderTabF();
    }

    renderTabA() {
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      const states = idx.states || [];
      const curState = states.find((s) => s.state_code === this.selectedStateCode) || states[0] || {};
      const dists = (idx.districts_by_state_code || {})[this.selectedStateCode] || [];
      const curDist = dists.find((d) => d.unit_id === this.selectedDistrictId) || null;
      const l3List = (curDist && (idx.level3_by_district_id || {})[curDist.unit_id]) || [];
      const l3Label = (curState.hierarchy && curState.hierarchy.level3_label) || 'Subdivision / Tehsil / Circle';
      const crumbs = (this.adminContext && this.adminContext.breadcrumb) || [];
      const vwLayer = this.layerStates.villages_wards?.payload;
      const vwItems = (vwLayer && vwLayer.items) || [];

      return `
        <div class="bhu-ii-card">
          <div style="font-weight:600;color:#e2e8f0;margin-bottom:4px;">Search 28 States + 8 UTs, Districts, Alternates &amp; Capitals</div>
          <div style="display:flex;gap:4px;">
            <input id="bhu-ii-admin-q" type="text" class="bhu-ii-input" value="${esc(this.lastSearchQuery)}" placeholder="Patna, पटना, Patliputra, Gaya, Maner, Hanle, Bengaluru..." />
            <button type="button" id="bhu-ii-admin-go" class="bhu-ii-btn">Search</button>
          </div>
          ${this.searchResults.length ? `
            <div style="margin-top:6px;max-height:130px;overflow-y:auto;display:flex;flex-direction:column;gap:3px;">
              ${this.searchResults.map((r, i) => `
                <button type="button" class="bhu-ii-hit" data-hit="${i}"
                  style="text-align:left;background:#0b101b;border:1px solid #1e293b;border-radius:3px;padding:4px 6px;color:#e2e8f0;cursor:pointer;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-weight:600;color:#7dd3fc;">${esc(r.name_en)} ${r.local_name ? `(${esc(r.local_name)})` : ''}</span>
                    <span style="color:#94a3b8;font-size:10px;">${esc(r.level_label)}</span>
                  </div>
                  <div style="color:#64748b;font-size:10px;">${esc(r.state_name)} · ${Number(r.lat).toFixed(4)}°, ${Number(r.lon).toFixed(4)}°</div>
                </button>
              `).join('')}
            </div>
          ` : (this.lastSearchQuery ? `<div style="margin-top:5px;font-size:10px;color:#fcd34d;">No verified state, district, subdivision, or settlement found for "${esc(this.lastSearchQuery)}". No synthetic administrative units generated.</div>` : '')
    }
        </div>

        <div class="bhu-ii-card">
          <div style="font-weight:600;color:#cbd5e1;margin-bottom:4px;">Breadcrumb Navigation (Canonical LocationContext)</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px;font-size:10px;color:#7dd3fc;">
            ${crumbs.map((b) => `<span class="bhu-ii-badge" style="border-color:#334155;">${esc(b.label)}: <b>${esc(b.name_en)}</b></span>`).join(' &rarr; ') || 'India'}
          </div>
        </div>

        <div class="bhu-ii-card" style="display:flex;flex-direction:column;gap:6px;">
          <div style="font-weight:600;color:#e2e8f0;">State-Specific Administrative Hierarchy Explorer (${idx.states_ut_count || 36} = 28 States + 8 UTs)</div>
          <div>
            <label style="font-size:10px;color:#94a3b8;">1. State / Union Territory</label>
            <select id="bhu-ii-state-sel" class="bhu-ii-select">
              ${states.map((s) => `<option value="${esc(s.state_code)}" ${s.state_code === this.selectedStateCode ? 'selected' : ''}>${esc(s.name_en)} (${esc(s.unit_type)})</option>`).join('')}
            </select>
          </div>
          <div>
            <label style="font-size:10px;color:#94a3b8;">2. District (${dists.length} verified)</label>
            <select id="bhu-ii-dist-sel" class="bhu-ii-select">
              <option value="">-- Select District --</option>
              ${dists.map((d) => `<option value="${esc(d.unit_id)}" ${d.unit_id === this.selectedDistrictId ? 'selected' : ''}>${esc(d.name_en)}</option>`).join('')}
            </select>
          </div>
          <div>
            <label style="font-size:10px;color:#94a3b8;">3. ${esc(l3Label)} (${l3List.length} verified)</label>
            <select id="bhu-ii-l3-sel" class="bhu-ii-select">
              <option value="">${l3List.length ? '-- Select Subdivision / Tehsil / Anchal --' : '-- Not pre-bundled locally (no fake divisions generated) --'}</option>
              ${l3List.map((u) => `<option value="${esc(u.unit_id)}" ${u.unit_id === this.selectedL3Id ? 'selected' : ''}>${esc(u.name_en)}</option>`).join('')}
            </select>
          </div>
          ${curState.hierarchy ? `
            <div style="background:#0b101b;border:1px solid #1e293b;border-radius:4px;padding:6px;font-size:10px;color:#94a3b8;">
              <div style="color:#fcd34d;font-weight:600;margin-bottom:2px;">${esc(curState.name_en)} Hierarchy Structure:</div>
              <div>${(curState.hierarchy.levels || []).map((lv) => `L${lv.depth}: ${esc(lv.label)}`).join(' &rarr; ')}</div>
              <div style="margin-top:3px;color:#64748b;">${esc(curState.hierarchy.hierarchy_note)}</div>
            </div>
          ` : ''}
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:10px;color:#94a3b8;">Villages / Wards in active radius: <b>${vwItems.length}</b></span>
            <button type="button" id="bhu-ii-load-vw" class="bhu-ii-btn">Fetch Villages / Wards</button>
          </div>
          ${vwItems.length ? `
            <div style="max-height:95px;overflow-y:auto;font-size:10px;color:#cbd5e1;display:flex;flex-wrap:wrap;gap:4px;">
              ${vwItems.slice(0, 25).map((v) => `<span class="bhu-ii-badge">${esc(v.name_en)} (${esc(v.urban_rural_class)})</span>`).join('')}
            </div>
          ` : ''}
        </div>
  `;
    }

    renderTabB() {
      const idx = window.BHU_LOKA_INDIA_INDEX || {};
      const states = idx.states || [];
      const res = this.landResult;
      const fv = this.landFormValues || {};
      const stCode = fv.state_or_code || this.selectedStateCode;
      const distVal = fv.district != null ? fv.district : (this.adminContext?.district || '');
      const subVal = fv.subdivision != null ? fv.subdivision : (this.adminContext?.subdivision || '');

      return `
    < div class="bhu-ii-card" style = "background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.35);color:#fde68a;font-size:10px;" >
      <b>Composite Scope Rule:</b> Plot, Khata, and Khesra numbers are NOT globally unique.Queries must scope State + District + Anchal / Circle + Mauza(or ULPIN).Ownership, legal title, and boundaries are never fabricated.
        </div >

    <form id="bhu-ii-land-form" class="bhu-ii-card" style="display:flex;flex-direction:column;gap:5px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:600;color:#e2e8f0;">Land Parcel &amp; Plot Search (Bihar Pilot + 36 DILRMP)</span>
        <button type="button" id="bhu-ii-bihar-pilot" class="bhu-ii-btn" style="font-size:10px;">Bihar Pilot</button>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;">
        <select name="state_or_code" id="bhu-ii-land-state" class="bhu-ii-select">
          ${states.map((s) => `<option value="${esc(s.state_code)}" ${s.state_code === stCode ? 'selected' : ''}>${esc(s.name_en)}</option>`).join('')}
        </select>
        <input name="district" class="bhu-ii-input" placeholder="District (e.g. Patna)" value="${esc(distVal)}" />
        <input name="subdivision" class="bhu-ii-input" placeholder="Subdivision / Tehsil / Anumandal" value="${esc(subVal)}" />
        <input name="circle" class="bhu-ii-input" placeholder="Anchal / Circle (e.g. Bihta)" value="${esc(fv.circle || '')}" />
        <input name="block" class="bhu-ii-input" placeholder="Block / CD Block" value="${esc(fv.block || '')}" />
        <input name="village_mauza" class="bhu-ii-input" placeholder="Village / Mauza" value="${esc(fv.village_mauza || '')}" />
        <input name="khata_no" class="bhu-ii-input" placeholder="Khata No." value="${esc(fv.khata_no || '')}" />
        <input name="khesra_no" class="bhu-ii-input" placeholder="Khesra / Khasra No." value="${esc(fv.khesra_no || '')}" />
        <input name="plot_no" class="bhu-ii-input" placeholder="Plot / Survey No." value="${esc(fv.plot_no || '')}" />
        <input name="ulpin" class="bhu-ii-input" placeholder="ULPIN (if available)" value="${esc(fv.ulpin || '')}" />
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px;">
          <label style="font-size:10px;color:#94a3b8;display:flex;align-items:center;gap:4px;">
            <input type="checkbox" name="check_portal" ${fv.check_portal ? 'checked' : ''} /> Check official portal root HTTP status
          </label>
          <button type="submit" class="bhu-ii-btn">Search / Official Portal Handoff</button>
      </div>
    </form>

        ${
    res ? (res.loading ? '<div class="bhu-ii-card" style="color:#7dd3fc;">Resolving DILRMP portal &amp; composite scope...</div>' : `
          <div class="bhu-ii-card" style="display:flex;flex-direction:column;gap:5px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-weight:700;color:#7dd3fc;">${esc(res.pilot_state)} · ${esc(res.integration_status)}</span>
              <span class="bhu-ii-badge" style="color:${res.scoping_complete ? '#6ee7b7' : '#fcd34d'};">${res.scoping_complete ? 'COMPOSITE SCOPE COMPLETE' : 'INCOMPLETE SCOPE'}</span>
            </div>
            ${res.missing_scoping_fields && res.missing_scoping_fields.length ? `<div style="font-size:10px;color:#fca5a5;">Missing required composite fields: ${esc(res.missing_scoping_fields.join(', '))}</div>` : ''}
            <div style="font-size:10px;color:#cbd5e1;">${esc(res.missing_capability_explanation)}</div>
            <div style="display:flex;flex-direction:column;gap:3px;">
              ${(res.official_portal_links || []).map((l) => `
                <a href="${esc(l.url)}" target="_blank" rel="noopener noreferrer"
                  style="display:flex;justify-content:space-between;padding:4px 6px;background:#0b101b;border:1px solid #334155;border-radius:3px;color:#38bdf8;text-decoration:none;">
                  <span><b>${esc(l.role)}</b>${l.name ? ` · ${esc(l.name)}` : ''}</span>
                  <span>OPEN &rarr;</span>
                </a>
              `).join('')}
            </div>
            ${(res.portal_checks || []).length ? `<div style="font-size:10px;color:#94a3b8;">HTTP Probe: ${res.portal_checks.map((c) => `${esc(c.url)} [${c.reachable ? 'HTTP ' + c.http_status : 'UNREACHABLE'}]`).join(' | ')}</div>` : ''}
          </div>
        `) : ''
  }
  `;
    }

    renderTabC() {
      const st = this.layerStates.police_jurisdictions;
      const payload = st.payload;
      const items = (payload && payload.items) || [];
      return `
    < div class="bhu-ii-card" style = "display:flex;justify-content:space-between;align-items:center;" >
          <div>
            <div style="font-weight:700;color:#fb7185;">Police Station Jurisdiction GIS Layer</div>
            <div style="font-size:10px;color:#94a3b8;">Independent GIS registry. Missing jurisdiction polygons are NEVER inferred from nearest point.</div>
          </div>
          <button type="button" class="bhu-ii-btn bhu-ii-refresh-layer" data-layer="police_jurisdictions">Refresh</button>
        </div >
    ${ this.renderLayerBannerHtml(st) }
  <div style="display:flex;flex-direction:column;gap:5px;">
    ${items.map((p) => `
            <div class="bhu-ii-card">
              <div style="display:flex;justify-content:space-between;gap:6px;">
                <span style="font-weight:700;color:#f8fafc;">${esc(p.station_name)}</span>
                <span class="bhu-ii-badge" style="color:${p.boundary_status === 'VERIFIED_POLYGON' ? '#6ee7b7' : '#fcd34d'};">${esc(p.boundary_status)}</span>
              </div>
              <div style="font-size:10px;color:#94a3b8;margin-top:2px;">
                District: ${esc(p.district || '--')} · Distance: ${p.distance_km} km · Address: ${esc(p.address || '--')}
              </div>
              <div style="font-size:10px;color:#cbd5e1;margin-top:2px;display:flex;justify-content:space-between;">
                <span>Source: ${esc(p.official_source)}</span>
                <a href="${esc(p.emergency_contact_link || 'tel:112')}" style="color:#fb7185;font-weight:700;">Emergency: 112</a>
              </div>
            </div>
          `).join('')}
  </div>
  `;
    }

    renderTabD() {
      const st = this.layerStates.street_cctv;
      const payload = st.payload;
      const items = (payload && payload.items) || [];
      const statusColor = (s) => (s === 'LIVE' || s === 'PUBLIC LINK') ? '#6ee7b7' : (s === 'AUTHORIZED ACCESS REQUIRED' ? '#fcd34d' : '#fca5a5');

      return `
    < div class="bhu-ii-card" style = "display:flex;justify-content:space-between;align-items:center;" >
          <div>
            <div style="font-weight:700;color:#10b981;">STREET CCTV Intelligence Layer</div>
            <div style="font-size:10px;color:#94a3b8;">Authorized &amp; public camera links only. Zero fabricated streams or restricted surveillance access.</div>
          </div>
          <button type="button" class="bhu-ii-btn bhu-ii-refresh-layer" data-layer="street_cctv">Refresh</button>
        </div >
    ${ st.status === 'LOADING' ? '<div class="bhu-ii-card" style="color:#7dd3fc;">Querying authorized CCTV registry...</div>' : '' }
        ${ st.status === 'ERROR' || st.status === 'UNAVAILABLE' ? `<div class="bhu-ii-card" style="border-color:#f43f5e;color:#fda4af;">${esc(st.error || (payload && payload.empty_message) || 'Authorized CCTV feed registry unavailable.')}</div>` : '' }
        ${
    !items.length && st.status !== 'LOADING' && st.status !== 'ERROR' && st.status !== 'UNAVAILABLE' ? `
          <div class="bhu-ii-card" style="border-color:rgba(245,158,11,0.45);color:#fde68a;">
            ${esc((payload && payload.empty_message) || CCTV_EMPTY_MSG)}
          </div>
        ` : ''
  }
  <div style="display:flex;flex-direction:column;gap:5px;">
    ${items.map((c) => `
            <div class="bhu-ii-card">
              <div style="display:flex;justify-content:space-between;gap:6px;">
                <span style="font-weight:700;color:#f8fafc;">${esc(c.camera_name)}</span>
                <span class="bhu-ii-badge" style="color:${statusColor(c.operational_status)};border-color:${statusColor(c.operational_status)};">${esc(c.operational_status)}</span>
              </div>
              <div style="font-size:10px;color:#94a3b8;margin-top:2px;">
                ID: ${esc(c.camera_id)} · Coords: ${c.latitude}°, ${c.longitude}° (${c.distance_km} km)
              </div>
              <div style="font-size:10px;color:#cbd5e1;margin-top:2px;">
                Authority: ${esc(c.responsible_authority)} · Type: ${esc(c.stream_type)}
              </div>
              <div style="font-size:10px;color:#64748b;margin-top:2px;display:flex;justify-content:space-between;">
                <span>Verified: ${esc(c.last_verified_time)}</span>
                <a href="${esc(c.source_url)}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;">Official Portal &rarr;</a>
              </div>
            </div>
          `).join('')}
  </div>
  `;
    }

    renderTabE() {
      const st = this.layerStates.local_news;
      const payload = st.payload;
      const pinned = (payload && payload.items) || [];
      const unpinned = (payload && payload.non_pinned_items) || [];

      return `
    < div class="bhu-ii-card" style = "display:flex;flex-direction:column;gap:5px;" >
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-weight:700;color:#f59e0b;">LOCAL NEWS Intelligence (EN / HI)</span>
            <button type="button" id="bhu-ii-news-refresh" class="bhu-ii-btn">Refresh PIB/NDMA RSS</button>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;">
            <select id="bhu-ii-news-cat" class="bhu-ii-select">
              <option value="">All 8 Categories</option>
              ${NEWS_CATEGORIES.map((c) => `<option value="${esc(c)}" ${this.newsCategory === c ? 'selected' : ''}>${esc(c)}</option>`).join('')}
            </select>
            <select id="bhu-ii-news-lang" class="bhu-ii-select">
              <option value="">All Languages (EN/HI/BN)</option>
              <option value="en" ${this.newsLanguage === 'en' ? 'selected' : ''}>English (en)</option>
              <option value="hi" ${this.newsLanguage === 'hi' ? 'selected' : ''}>Hindi (hi)</option>
              <option value="bn" ${this.newsLanguage === 'bn' ? 'selected' : ''}>Bengali (bn)</option>
            </select>
          </div>
        </div >
    ${ this.renderLayerBannerHtml(st) }
        <div class="bhu-ii-card">
          <div style="font-size:10px;font-weight:700;color:#7dd3fc;margin-bottom:4px;">Map-Pinned Coordinate Alerts (${pinned.length})</div>
          ${pinned.length ? pinned.slice(0, 15).map((n) => this.renderNewsCard(n)).join('') : '<div style="font-size:10px;color:#94a3b8;">No coordinate-verified CAP alerts inside selected radius.</div>'}
        </div>
        <div class="bhu-ii-card">
          <div style="font-size:10px;font-weight:700;color:#cbd5e1;margin-bottom:4px;">Regional / District / State Headlines — List Only (${unpinned.length}, not pinned to fake street coords)</div>
          ${unpinned.length ? unpinned.slice(0, 20).map((n) => this.renderNewsCard(n)).join('') : '<div style="font-size:10px;color:#94a3b8;">No matching district/state headlines.</div>'}
        </div>
  `;
    }

    renderNewsCard(n) {
      return `
    < div style = "border-top:1px solid #1e293b;padding-top:5px;margin-top:5px;" >
          <div style="display:flex;justify-content:space-between;gap:4px;">
            <span class="bhu-ii-badge" style="color:#fcd34d;border-color:#78350f;">${esc(n.news_category)}</span>
            <span class="bhu-ii-badge">${esc(String(n.language_code || '').toUpperCase())} · ${esc(n.geographic_precision)}</span>
          </div>
          <div style="font-weight:600;color:#f8fafc;margin-top:3px;">${esc(n.headline)}</div>
          <div style="font-size:10px;color:#94a3b8;margin-top:2px;">${esc(n.ai_summary)}</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;display:flex;justify-content:space-between;">
            <span>${esc(n.publisher)} · ${esc(n.publication_time)}</span>
            <a href="${esc(n.original_url)}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;">Source &rarr;</a>
          </div>
        </div>
  `;
    }

    renderTabF() {
      const infoSt = this.infoLayerId ? this.layerStates[this.infoLayerId] : null;
      const feedIds = ['emergency_alerts', 'traffic_advisories', 'road_closures', 'diversions', 'hospitals', 'fire_stations', 'disaster_response'];
      const feedCards = feedIds.flatMap((lid) => {
        const st = this.layerStates[lid];
        const items = (st && st.visible && st.payload && st.payload.items) || [];
        return items.slice(0, 4).map((it) => ({ layerTitle: st.meta.title, color: st.meta.color, it }));
      });
      return `
        <div class="bhu-ii-card" style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-weight:700;color:#7dd3fc;">12-Layer GIS Manager &amp; Traffic / Emergency Layers</div>
            <div style="font-size:10px;color:#94a3b8;">Toggle any layer, adjust opacity, zoom to extent, or inspect schema &amp; source provenance.</div>
          </div>
          <button type="button" id="bhu-ii-refresh-all" class="bhu-ii-btn">Refresh Active</button>
        </div>

        ${feedCards.length ? `
          <div class="bhu-ii-card" style="max-height:145px;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">
            <div style="font-weight:700;color:#e2e8f0;font-size:10px;">Active Traffic &amp; Emergency Intelligence Readout (${feedCards.length})</div>
            ${feedCards.map(({ layerTitle, color, it }) => `
              <div style="border-top:1px solid #1e293b;padding-top:3px;font-size:10px;">
                <div style="display:flex;justify-content:space-between;">
                  <span style="color:${esc(color)};font-weight:700;">${esc(it.name || it.headline || it.title || layerTitle)}</span>
                  <span style="color:#94a3b8;">${it.distance_km != null ? `${it.distance_km} km` : ''}</span>
                </div>
                <div style="color:#94a3b8;">${esc(layerTitle)} · ${esc(it.observation_time_utc || it.publication_time || '')}</div>
              </div>
            `).join('')}
          </div>
        ` : ''
  }

        ${
    infoSt ? `
          <div class="bhu-ii-card" style="border-color:#38bdf8;">
            <div style="display:flex;justify-content:space-between;">
              <b style="color:#7dd3fc;">Layer Info: ${esc(infoSt.meta.title)}</b>
              <button type="button" id="bhu-ii-info-close" class="bhu-ii-btn" style="padding:1px 5px;">&times;</button>
            </div>
            <div style="font-size:10px;color:#cbd5e1;margin-top:3px;">Source: ${esc(infoSt.meta.source_attribution)}</div>
            <div style="font-size:10px;color:#94a3b8;margin-top:2px;">Updated: ${esc(infoSt.payload?.updated_at_utc || 'Not yet queried')}</div>
            <div style="font-size:10px;color:#94a3b8;margin-top:2px;">Schema: ${esc((infoSt.meta.schema || []).join(', '))}</div>
          </div>
        ` : ''
  }

  <div style="display:flex;flex-direction:column;gap:5px;">
    ${DEFAULT_LAYER_META.map((m) => {
      const st = this.layerStates[m.layer_id];
      const cnt = st.payload ? st.payload.feature_count : '--';
      const sCol = layerStatusColor(st.status);
      const unavailMsg = st.error || (st.payload && (st.payload.error_detail || st.payload.empty_message)) || 'Layer source unavailable (zero fabricated features).';
      return `
              <div class="bhu-ii-card">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:4px;">
                  <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-weight:600;color:#f8fafc;">
                    <input type="checkbox" class="bhu-ii-layer-chk" data-layer="${esc(m.layer_id)}" ${st.visible ? 'checked' : ''} />
                    <span style="width:9px;height:9px;border-radius:2px;background:${esc(m.color)};display:inline-block;"></span>
                    <span>${esc(m.title)}</span>
                  </label>
                  <span class="bhu-ii-badge" style="color:${sCol};border-color:${sCol}55;">${esc(st.status)} (${cnt})</span>
                </div>
                <div style="display:flex;align-items:center;gap:6px;margin-top:5px;">
                  <span style="font-size:10px;color:#64748b;">Opacity</span>
                  <input type="range" class="bhu-ii-layer-op" data-layer="${esc(m.layer_id)}" min="0.1" max="1.0" step="0.1" value="${st.opacity}" style="flex:1;" />
                  <button type="button" class="bhu-ii-btn bhu-ii-layer-zoom" data-layer="${esc(m.layer_id)}" style="padding:1px 6px;font-size:10px;">Zoom</button>
                  <button type="button" class="bhu-ii-btn bhu-ii-layer-info" data-layer="${esc(m.layer_id)}" style="padding:1px 6px;font-size:10px;">Info</button>
                </div>
                ${(st.status === 'ERROR' || st.status === 'UNAVAILABLE') ? `<div style="font-size:10px;color:#fda4af;margin-top:3px;">${esc(unavailMsg)}</div>` : ''}
                ${st.status === 'EMPTY' && st.payload ? `<div style="font-size:10px;color:#fde68a;margin-top:3px;">${esc(st.payload.empty_message)}</div>` : ''}
              </div>
            `;
    }).join('')}
  </div>
  `;
    }

    renderLayerBannerHtml(st) {
      if (st.status === 'LOADING') return '<div class="bhu-ii-card" style="color:#7dd3fc;">Loading real GIS layer data...</div>';
      if (st.status === 'ERROR' || st.status === 'UNAVAILABLE') {
        const msg = st.error || (st.payload && (st.payload.error_detail || st.payload.empty_message)) || 'External GIS feed unavailable (no fabricated data).';
        return `< div class="bhu-ii-card" style = "border-color:#f43f5e;color:#fda4af;" > ${ esc(msg) }</div > `;
      }
      if (st.status === 'EMPTY' && st.payload) return `< div class="bhu-ii-card" style = "border-color:#f59e0b;color:#fde68a;" > ${ esc(st.payload.empty_message) }</div > `;
      if (st.payload) {
        return `< div style = "font-size:10px;color:#64748b;" > Status: <b>${esc(st.status)}</b> · Attribution: ${ esc(st.payload.source_attribution) } · Updated: ${ esc(st.payload.updated_at_utc) }</div > `;
      }
      return '';
    }

    wireActiveTabEvents(panel) {
      const qInp = panel.querySelector('#bhu-ii-admin-q');
      const qGo = panel.querySelector('#bhu-ii-admin-go');
      if (qInp) {
        qInp.oninput = () => { this.lastSearchQuery = qInp.value; };
        qInp.onkeydown = (e) => { if (e.key === 'Enter') this.runAdminAutocomplete(qInp.value); };
      }
      if (qGo && qInp) qGo.onclick = () => this.runAdminAutocomplete(qInp.value);

      panel.querySelectorAll('.bhu-ii-hit').forEach((btn) => {
        btn.onclick = () => {
          const hit = this.searchResults[Number(btn.dataset.hit)];
          if (hit) this.selectLocationPoint(hit.lat, hit.lon, hit.name_en, 11, { state_code: hit.state_code });
        };
      });

      const stSel = panel.querySelector('#bhu-ii-state-sel');
      if (stSel) {
        stSel.onchange = () => {
          this.selectedStateCode = stSel.value;
          this.selectedDistrictId = '';
          this.selectedL3Id = '';
          const idx = window.BHU_LOKA_INDIA_INDEX || {};
          const stObj = (idx.states || []).find((s) => s.state_code === stSel.value);
          if (stObj) this.selectLocationPoint(stObj.centroid[0], stObj.centroid[1], stObj.name_en, 7, { state_code: stObj.state_code });
          this.renderWorkspace();
        };
      }

      const dSel = panel.querySelector('#bhu-ii-dist-sel');
      if (dSel) {
        dSel.onchange = () => {
          this.selectedDistrictId = dSel.value;
          this.selectedL3Id = '';
          const idx = window.BHU_LOKA_INDIA_INDEX || {};
          const d = ((idx.districts_by_state_code || {})[this.selectedStateCode] || []).find((x) => x.unit_id === dSel.value);
          if (d) this.selectLocationPoint(d.centroid[0], d.centroid[1], d.name_en, 10, { district_id: d.unit_id });
          this.renderWorkspace();
        };
      }

      const l3Sel = panel.querySelector('#bhu-ii-l3-sel');
      if (l3Sel) {
        l3Sel.onchange = () => {
          this.selectedL3Id = l3Sel.value;
          const idx = window.BHU_LOKA_INDIA_INDEX || {};
          const l3 = ((idx.level3_by_district_id || {})[this.selectedDistrictId] || []).find((x) => x.unit_id === l3Sel.value);
          if (l3) this.selectLocationPoint(l3.centroid[0], l3.centroid[1], l3.name_en, 12, { l3_id: l3.unit_id });
        };
      }

      const vwBtn = panel.querySelector('#bhu-ii-load-vw');
      if (vwBtn) {
        vwBtn.onclick = () => {
          this.layerStates.villages_wards.visible = true;
          this.fetchLayer('villages_wards', true);
        };
      }

      const landForm = panel.querySelector('#bhu-ii-land-form');
      if (landForm) {
        landForm.oninput = () => {
          const fd = new FormData(landForm);
          const obj = Object.fromEntries(fd.entries());
          obj.check_portal = fd.get('check_portal') === 'on';
          this.landFormValues = obj;
        };
        landForm.onsubmit = (e) => {
          e.preventDefault();
          const fd = new FormData(landForm);
          const obj = Object.fromEntries(fd.entries());
          obj.check_portal = fd.get('check_portal') === 'on';
          this.submitLandParcelSearch(obj);
        };
      }

      const biharBtn = panel.querySelector('#bhu-ii-bihar-pilot');
      if (biharBtn) {
        biharBtn.onclick = () => {
          this.selectedStateCode = '10';
          const sel = panel.querySelector('#bhu-ii-land-state');
          if (sel) sel.value = '10';
          this.submitLandParcelSearch({ state_or_code: '10', district: 'Patna' });
        };
      }

      panel.querySelectorAll('.bhu-ii-refresh-layer').forEach((btn) => {
        btn.onclick = () => this.fetchLayer(btn.dataset.layer, true);
      });

      const nrBtn = panel.querySelector('#bhu-ii-news-refresh');
      if (nrBtn) nrBtn.onclick = () => this.refreshOfficialNews();
      const nCat = panel.querySelector('#bhu-ii-news-cat');
      if (nCat) nCat.onchange = () => { this.newsCategory = nCat.value; this.fetchLayer('local_news', false); };
      const nLang = panel.querySelector('#bhu-ii-news-lang');
      if (nLang) nLang.onchange = () => { this.newsLanguage = nLang.value; this.fetchLayer('local_news', false); };

      const raBtn = panel.querySelector('#bhu-ii-refresh-all');
      if (raBtn) raBtn.onclick = () => this.refreshVisibleLayers(true);

      const icBtn = panel.querySelector('#bhu-ii-info-close');
      if (icBtn) icBtn.onclick = () => { this.infoLayerId = null; this.renderWorkspace(); };

      panel.querySelectorAll('.bhu-ii-layer-chk').forEach((chk) => {
        chk.onchange = () => this.toggleLayerVisibility(chk.dataset.layer);
      });
      panel.querySelectorAll('.bhu-ii-layer-op').forEach((rng) => {
        rng.oninput = () => this.setLayerOpacity(rng.dataset.layer, rng.value);
      });
      panel.querySelectorAll('.bhu-ii-layer-zoom').forEach((btn) => {
        btn.onclick = () => this.zoomToLayer(btn.dataset.layer);
      });
      panel.querySelectorAll('.bhu-ii-layer-info').forEach((btn) => {
        btn.onclick = () => {
          this.infoLayerId = btn.dataset.layer;
          this.renderWorkspace();
        };
      });
    }
  }

  window.BhuLokaIndiaIntel = new IndiaLocationStreetIntelController();
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => window.BhuLokaIndiaIntel.init());
    } else {
      window.BhuLokaIndiaIntel.init();
    }
  }
})(window);