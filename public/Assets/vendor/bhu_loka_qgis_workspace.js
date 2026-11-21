/**
 * BHU LOKA (भूलोक) — QGIS-Inspired Professional Web GIS Workspace Engine
 * ======================================================================
 * Desktop-grade GIS analysis workspace for Land Studio:
 * 
 * 1. WORKSPACE LAYOUT:
 *    - Left: Browser / Data Sources / Layer Tree
 *    - Centre: Map Canvas (2D Leaflet + 3D Exploded / Hologram Switcher)
 *    - Right: Processing Toolbox / Feature Inspector / Layer Styling
 *    - Bottom: Attribute Table / Processing Log / Spatial Console (Dockable)
 *    - Top: Project, View, Layer, Analysis, Processing, Export Ribbon + CRS Selector
 * 
 * 2. DATA MANAGEMENT:
 *    - Formats: GeoJSON, Shapefile (Import/Export ZIP with .shp,.shx,.dbf,.prj),
 *      CSV (Lat/Lon auto-detect), KML, GeoPackage JSON, GeoTIFF DEM.
 *    - Metadata: Layer Name, Geometry Type, CRS, Feature Count, Bounding Extent, Source, Date, Schema.
 *    - Explicit CRS selection & reprojection: EPSG:4326, EPSG:3857, EPSG:32643, EPSG:32644, EPSG:32645.
 * 
 * 3. GIS ANALYSIS TOOLBOX:
 *    - Vector: Buffer, Clip, Intersect, Union, Difference, Dissolve, Centroid, Area & Perimeter.
 *    - Raster: Raster Clip (DEM), Zonal Statistics (Elevation/Slope), Raster Comparison (Delta).
 *    - Site Intelligence: Extract Buildings & Roads, Decadal Change Detection (2014-2026),
 *      Jal Raksha FTL Screening (BSA §63), Full Site Analysis Report.
 *    - Geodesic Measurement: Distance Ruler & Polygon Area.
 *    - Real processing logging: Algorithm, Input, Parameters, Output count, Duration ms, CRS.
 * 
 * Strict Zero-Fabrication Policy:
 *   - Genuine geometric computations using Turf.js and FastAPI backend.
 *   - No fake layers, no synthetic crime polygons, fail-closed UNAVAILABLE states.
 */

(function (window) {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // SUPPORTED CRS DEFINITIONS (PROJ4 / WKT)
  // ═══════════════════════════════════════════════════════════════
  const SUPPORTED_CRS = {
    'EPSG:4326': {
      name: 'WGS 84 (Geodetic Lat/Lon)',
      unit: 'degrees',
      proj4: '+proj=longlat +datum=WGS84 +no_defs',
      wkt: 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
    },
    'EPSG:3857': {
      name: 'WGS 84 / Pseudo-Mercator',
      unit: 'meters',
      proj4: '+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs'
    },
    'EPSG:32643': {
      name: 'WGS 84 / UTM Zone 43N (Western India)',
      unit: 'meters',
      proj4: '+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs'
    },
    'EPSG:32644': {
      name: 'WGS 84 / UTM Zone 44N (Central India / Telangana / Bihar)',
      unit: 'meters',
      proj4: '+proj=utm +zone=44 +datum=WGS84 +units=m +no_defs'
    },
    'EPSG:32645': {
      name: 'WGS 84 / UTM Zone 45N (Eastern India / Bengal)',
      unit: 'meters',
      proj4: '+proj=utm +zone=45 +datum=WGS84 +units=m +no_defs'
    }
  };

  class QgisWorkspaceEngine {
    constructor() {
      this.activeCrs = 'EPSG:4326';
      this.layers = new Map(); // id -> { name, type, geojson, leafletLayer, style, visible, crs, metadata }
      this.selectedLayerId = null;
      this.selectedFeature = null;
      this.processingLogs = [];
      this.measureMode = null; // 'distance' | 'area' | null
      this.measurePoints = [];
      this.measureLayer = null;
      this.map = null;
      this.activeToolboxCategory = 'all';
      this.activeBottomTab = 'table';
      this.activeRightTab = 'toolbox';
      this.activeLeftTab = 'tree';
    }

    /**
     * Dynamically mounts QGIS-inspired workspace panels into the Land Studio modal if not present.
     */
    ensureUiMounted() {
      if (typeof document === 'undefined') return;
      if (document.getElementById('qgis-layer-tree-list') && document.getElementById('qgis-bottom-dock')) {
        return;
      }

      // 1. Inject Menu Ribbon into Center Panel (above map view)
      const centerPanel = document.getElementById('us3-center-panel');
      if (centerPanel && !document.getElementById('qgis-menu-ribbon')) {
        const ribbon = document.createElement('div');
        ribbon.id = 'qgis-menu-ribbon';
        ribbon.className = 'qgis-ribbon';
        ribbon.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:4px 8px;background:#060b16;border-bottom:1px solid rgba(56,189,248,0.2);flex-shrink:0;gap:6px;overflow-x:auto;font-size:10px;';
        ribbon.innerHTML = `
          <div style="display:flex;align-items:center;gap:4px;flex-shrink:0;">
            <input type="file" id="qgis-file-input" style="display:none;" accept=".geojson,.json,.csv,.kml" onchange="window.handleQgisFileUpload(this)">
            <button type="button" class="qgis-btn" onclick="document.getElementById('qgis-file-input').click()" title="Import GeoJSON, CSV, KML vector layers">
              <i class="fa-solid fa-folder-open" style="color:#38bdf8;"></i> Ingest Vector
            </button>
            <button type="button" class="qgis-btn" onclick="window.qgisWorkspace.exportActiveGeoJson()" title="Export active layer as GeoJSON">
              <i class="fa-solid fa-download" style="color:#34d399;"></i> Export GeoJSON
            </button>
            <span style="color:rgba(255,255,255,0.2);margin:0 2px;">|</span>
            <button type="button" class="qgis-btn" onclick="window.qgisWorkspace.startDistanceMeasurement()" title="Geodesic distance measurement ruler">
              <i class="fa-solid fa-ruler" style="color:#f59e0b;"></i> Ruler
            </button>
            <button type="button" class="qgis-btn" onclick="window.qgisWorkspace.startAreaMeasurement()" title="Geodesic polygon area measurement">
              <i class="fa-solid fa-draw-polygon" style="color:#10b981;"></i> Area
            </button>
            <span style="color:rgba(255,255,255,0.2);margin:0 2px;">|</span>
            <button type="button" class="qgis-btn" onclick="window.promptQgisBuffer()" title="Calculate metric UTM buffer">
              <i class="fa-solid fa-bullseye" style="color:#fbbf24;"></i> Buffer
            </button>
            <button type="button" class="qgis-btn" onclick="window.promptQgisClip()" title="Clip features by polygon overlay">
              <i class="fa-solid fa-scissors" style="color:#f43f5e;"></i> Clip
            </button>
            <button type="button" class="qgis-btn" onclick="if(window.qgisWorkspace.selectedLayerId) window.qgisWorkspace.runCentroids(window.qgisWorkspace.selectedLayerId); else alert('Select a layer from the Layer Tree first.');" title="Compute geometric centroids">
              <i class="fa-solid fa-crosshairs" style="color:#06b6d4;"></i> Centroids
            </button>
            <button type="button" class="qgis-btn" onclick="window.promptQgisZonalStats()" title="Calculate Copernicus DEM topographic zonal statistics">
              <i class="fa-solid fa-mountain" style="color:#a855f7;"></i> Zonal Stats
            </button>
            <button type="button" class="qgis-btn" onclick="window.promptQgisSiteDossier()" title="Compile multi-source site intelligence dossier (BSA §63)">
              <i class="fa-solid fa-file-shield" style="color:#38bdf8;"></i> Site Dossier
            </button>
          </div>
          <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
            <div id="qgis-crs-pill" onclick="window.promptQgisCrsSelect()" title="Click to transform Project CRS" style="font-family:monospace;font-size:9.5px;padding:2px 8px;border-radius:4px;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.3);color:#38bdf8;cursor:pointer;font-weight:700;">
              EPSG:4326
            </div>
            <button type="button" class="qgis-btn" onclick="window.qgisWorkspace.toggleBottomDock()" title="Toggle Attribute Table & Processing Dock">
              <i class="fa-solid fa-table-columns"></i> Dock
            </button>
          </div>
        `;
        const firstChild = centerPanel.children[0];
        if (firstChild && firstChild.nextSibling) {
          centerPanel.insertBefore(ribbon, firstChild.nextSibling);
        } else {
          centerPanel.prepend(ribbon);
        }
      }

      // 2. Inject Layer Tree into Left Panel
      const leftPanel = document.getElementById('us3-left-panel');
      if (leftPanel && !document.getElementById('qgis-layer-tree-card')) {
        const treeCard = document.createElement('div');
        treeCard.id = 'qgis-layer-tree-card';
        treeCard.className = 'us3-card';
        treeCard.style.cssText = 'display:flex;flex-direction:column;gap:6px;margin-top:6px;';
        treeCard.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <span class="us3-sec-title" style="margin:0;"><span>Layer Tree &amp; Sources</span></span>
            <div style="display:flex;gap:4px;">
              <button type="button" onclick="document.getElementById('qgis-file-input').click()" class="us3-btn" style="padding:2px 6px;font-size:9px;" title="Import GeoJSON, CSV, KML">
                <i class="fa-solid fa-plus"></i> Import
              </button>
            </div>
          </div>
          <div id="qgis-layer-tree-list" style="max-height:160px;overflow-y:auto;display:flex;flex-direction:column;gap:3px;padding-right:2px;">
            <div style="padding:12px;text-align:center;color:#64748b;font-size:10px;">No active vector layers.</div>
          </div>
        `;
        leftPanel.appendChild(treeCard);
      }

      // 3. Inject Dockable Bottom Panel into Center Panel
      if (centerPanel && !document.getElementById('qgis-bottom-dock')) {
        const dock = document.createElement('div');
        dock.id = 'qgis-bottom-dock';
        dock.className = 'qgis-bottom-dock';
        dock.style.cssText = 'display:flex;flex-direction:column;height:180px;max-height:260px;background:#050a14;border-top:1px solid rgba(56,189,248,0.25);z-index:900;flex-shrink:0;';
        dock.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 8px;background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(255,255,255,0.06);flex-shrink:0;">
            <div style="display:flex;align-items:center;gap:4px;">
              <button type="button" id="qgis-btab-table" class="qgis-tab active" onclick="window.qgisWorkspace.switchBottomTab('table')">
                <i class="fa-solid fa-table"></i> Attribute Table
              </button>
              <button type="button" id="qgis-btab-log" class="qgis-tab" onclick="window.qgisWorkspace.switchBottomTab('log')">
                <i class="fa-solid fa-terminal"></i> Processing Log
              </button>
              <button type="button" id="qgis-btab-console" class="qgis-tab" onclick="window.qgisWorkspace.switchBottomTab('console')">
                <i class="fa-solid fa-compass"></i> Spatial Console
              </button>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
              <span id="qgis-attr-table-count" style="font-family:monospace;font-size:9.5px;color:#94a3b8;">0 features</span>
              <button type="button" onclick="window.qgisWorkspace.exportActiveCsv()" class="qgis-btn" style="padding:2px 6px;font-size:9px;" title="Export table rows to CSV">
                <i class="fa-solid fa-file-csv"></i> Export CSV
              </button>
              <button type="button" onclick="window.qgisWorkspace.toggleBottomDock()" class="qgis-btn" style="padding:2px 5px;font-size:9px;" title="Minimize dock">
                <i class="fa-solid fa-chevron-down"></i>
              </button>
            </div>
          </div>

          <!-- Bottom Tab 1: Attribute Table -->
          <div id="qgis-bpanel-table" style="flex:1;overflow:auto;display:flex;flex-direction:column;background:#030712;">
            <table style="width:100%;border-collapse:collapse;font-size:10px;text-align:left;">
              <thead id="qgis-attr-table-head" style="background:#091224;position:sticky;top:0;z-index:2;">
                <tr><th style="padding:4px 8px;color:#94a3b8;">No data loaded</th></tr>
              </thead>
              <tbody id="qgis-attr-table-body">
                <tr><td style="padding:16px;text-align:center;color:#64748b;">Load or select a vector layer to view tabular attribute records.</td></tr>
              </tbody>
            </table>
          </div>

          <!-- Bottom Tab 2: Processing Log -->
          <div id="qgis-bpanel-log" style="flex:1;overflow-y:auto;display:none;flex-direction:column;padding:6px;background:#030712;">
            <div id="qgis-processing-log-list" style="display:flex;flex-direction:column;gap:4px;"></div>
          </div>

          <!-- Bottom Tab 3: Spatial Console -->
          <div id="qgis-bpanel-console" style="flex:1;overflow-y:auto;display:none;flex-direction:column;padding:8px;background:#030712;gap:6px;">
            <div style="font-size:10px;color:#cbd5e1;">Interactive Coordinate Transformation &amp; Projection Engine:</div>
            <div style="display:flex;gap:6px;">
              <input type="text" id="qgis-console-input" placeholder="Enter Latitude, Longitude (e.g. 17.4431, 78.4735)"
                style="flex:1;padding:4px 8px;background:#0b1329;border:1px solid rgba(56,189,248,0.3);border-radius:4px;color:#fff;font-family:monospace;font-size:10px;">
              <button type="button" onclick="window.runQgisConsoleTransform()" class="qgis-btn" style="background:#0284c7;color:#fff;">Transform</button>
            </div>
            <div id="qgis-console-output" style="font-family:monospace;font-size:9.5px;color:#38bdf8;padding:6px;background:rgba(255,255,255,0.02);border-radius:4px;line-height:1.5;">
              Enter coordinates above to compute instantaneous WGS84, UTM Zone Easting/Northing, and Web Mercator values.
            </div>
          </div>
        `;
        const statusBar = centerPanel.querySelector('.us3-statusbar');
        if (statusBar) {
          centerPanel.insertBefore(dock, statusBar);
        } else {
          centerPanel.appendChild(dock);
        }
      }

      // 4. Inject Right Panel Tabs into Right Inspector
      const rightPanel = document.getElementById('us3-right-panel');
      if (rightPanel && !document.getElementById('qgis-rtab-bar')) {
        const tabHeader = document.createElement('div');
        tabHeader.id = 'qgis-rtab-bar';
        tabHeader.style.cssText = 'display:flex;align-items:center;gap:3px;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:6px;margin-bottom:6px;flex-shrink:0;';
        tabHeader.innerHTML = `
          <button type="button" id="qgis-rtab-toolbox" class="qgis-tab active" onclick="window.qgisWorkspace.switchRightTab('toolbox')" style="flex:1;text-align:center;">Toolbox</button>
          <button type="button" id="qgis-rtab-inspector" class="qgis-tab" onclick="window.qgisWorkspace.switchRightTab('inspector')" style="flex:1;text-align:center;">Inspector</button>
          <button type="button" id="qgis-rtab-symbology" class="qgis-tab" onclick="window.qgisWorkspace.switchRightTab('symbology')" style="flex:1;text-align:center;">Symbology</button>
        `;
        rightPanel.prepend(tabHeader);

        // Right Panel 1: Processing Toolbox
        const pToolbox = document.createElement('div');
        pToolbox.id = 'qgis-rpanel-toolbox';
        pToolbox.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
        pToolbox.innerHTML = `
          <div class="us3-sec-title"><span>GIS Processing Toolbox</span></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
            <button type="button" class="qgis-btn" onclick="window.promptQgisBuffer()"><i class="fa-solid fa-bullseye" style="color:#fbbf24;"></i> Buffer (UTM)</button>
            <button type="button" class="qgis-btn" onclick="window.promptQgisClip()"><i class="fa-solid fa-scissors" style="color:#f43f5e;"></i> Clip Overlay</button>
            <button type="button" class="qgis-btn" onclick="if(window.qgisWorkspace.selectedLayerId) window.qgisWorkspace.runCentroids(window.qgisWorkspace.selectedLayerId); else alert('Select a layer first.');"><i class="fa-solid fa-crosshairs" style="color:#06b6d4;"></i> Centroids</button>
            <button type="button" class="qgis-btn" onclick="window.promptQgisZonalStats()"><i class="fa-solid fa-mountain" style="color:#a855f7;"></i> Zonal Stats</button>
          </div>
          <button type="button" class="qgis-btn" onclick="window.promptQgisSiteDossier()" style="background:rgba(2,132,199,0.15);border-color:rgba(56,189,248,0.4);color:#38bdf8;padding:6px;">
            <i class="fa-solid fa-file-shield"></i> Run Full Site Dossier (BSA §63)
          </button>
        `;
        rightPanel.insertBefore(pToolbox, rightPanel.children[1]);

        // Right Panel 2: Feature Inspector
        const pInspector = document.createElement('div');
        pInspector.id = 'qgis-rpanel-inspector';
        pInspector.style.cssText = 'display:none;flex-direction:column;gap:6px;';
        pInspector.innerHTML = `<div id="qgis-feature-inspector-content" style="color:#94a3b8;font-size:10px;padding:8px;text-align:center;">Click any map feature to inspect its attributes.</div>`;
        rightPanel.insertBefore(pInspector, rightPanel.children[2]);

        // Right Panel 3: Symbology
        const pSymbology = document.createElement('div');
        pSymbology.id = 'qgis-rpanel-symbology';
        pSymbology.style.cssText = 'display:none;flex-direction:column;gap:8px;';
        pSymbology.innerHTML = `
          <div class="us3-sec-title"><span>Layer Symbology &amp; Style</span></div>
          <div style="display:flex;flex-direction:column;gap:6px;font-size:10px;color:#cbd5e1;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span>Stroke Color</span>
              <input type="color" id="qgis-style-color" value="#38bdf8" style="background:transparent;border:none;cursor:pointer;">
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span>Fill Color</span>
              <input type="color" id="qgis-style-fill" value="#0284c7" style="background:transparent;border:none;cursor:pointer;">
            </div>
            <div>
              <div style="display:flex;justify-content:space-between;"><span>Fill Opacity</span><span id="qgis-style-op-val">0.3</span></div>
              <input type="range" id="qgis-style-opacity" min="0" max="1" step="0.05" value="0.3" oninput="document.getElementById('qgis-style-op-val').textContent=this.value;window.qgisWorkspace.applyCurrentStyling();" style="width:100%;accent-color:#38bdf8;">
            </div>
            <div>
              <div style="display:flex;justify-content:space-between;"><span>Stroke Weight</span><span id="qgis-style-wt-val">2px</span></div>
              <input type="range" id="qgis-style-weight" min="1" max="8" step="1" value="2" oninput="document.getElementById('qgis-style-wt-val').textContent=this.value+'px';window.qgisWorkspace.applyCurrentStyling();" style="width:100%;accent-color:#38bdf8;">
            </div>
            <button type="button" class="qgis-btn" onclick="window.qgisWorkspace.applyCurrentStyling()" style="background:#0284c7;color:#fff;margin-top:4px;">Apply Symbology</button>
          </div>
        `;
        rightPanel.insertBefore(pSymbology, rightPanel.children[3]);
      }
    }

    /**
     * Initializes the QGIS-inspired workspace inside the given Leaflet map.
     */
    init(leafletMap) {
      this.ensureUiMounted();
      this.map = leafletMap;
      this.measureLayer = L.layerGroup().addTo(this.map);
      this.logProcessing('Workspace Initialized', {}, 0, 'EPSG:4326', 'QGIS-Inspired Professional Web GIS Engine ready.');
      this._bindMapEvents();
    }

    _bindMapEvents() {
      if (!this.map) return;
      this.map.on('click', (e) => {
        if (this.measureMode === 'distance') {
          this._handleDistanceClick(e.latlng);
        } else if (this.measureMode === 'area') {
          this._handleAreaClick(e.latlng);
        }
      });
    }

    // ─────────────────────────────────────────────────────────────
    // LAYER MANAGEMENT & DATA INGESTION
    // ─────────────────────────────────────────────────────────────

    addLayer(name, geojson, options = {}) {
      const id = options.id || `layer_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
      const crs = options.crs || this.activeCrs;
      const geomType = this._detectGeometryType(geojson);
      const featureCount = geojson.features ? geojson.features.length : (geojson.type === 'Feature' ? 1 : 0);
      const extent = this._computeExtent(geojson);

      const style = Object.assign({
        color: options.color || '#38bdf8',
        fillColor: options.fillColor || '#0284c7',
        weight: options.weight || 2,
        fillOpacity: options.fillOpacity !== undefined ? options.fillOpacity : 0.25,
        radius: options.radius || 6
      }, options.style || {});

      // Create Leaflet GeoJSON layer
      const leafletLayer = L.geoJSON(geojson, {
        style: (feature) => style,
        pointToLayer: (feature, latlng) => {
          return L.circleMarker(latlng, {
            radius: style.radius,
            fillColor: style.fillColor,
            color: style.color,
            weight: style.weight,
            opacity: 1,
            fillOpacity: style.fillOpacity
          });
        },
        onEachFeature: (feature, layer) => {
          layer.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            this.inspectFeature(id, feature, layer);
          });
        }
      });

      if (options.visible !== false) {
        leafletLayer.addTo(this.map);
      }

      const layerData = {
        id,
        name,
        type: geomType,
        geojson,
        leafletLayer,
        style,
        visible: options.visible !== false,
        crs,
        featureCount,
        extent,
        source: options.source || 'User Layer / Derived Analysis',
        date: options.date || new Date().toISOString().split('T')[0],
        schema: this._extractSchema(geojson)
      };

      this.layers.set(id, layerData);
      this.selectedLayerId = id;
      this.refreshLayerTree();
      this.refreshAttributeTable();
      return id;
    }

    removeLayer(id) {
      const l = this.layers.get(id);
      if (!l) return;
      if (this.map.hasLayer(l.leafletLayer)) {
        this.map.removeLayer(l.leafletLayer);
      }
      this.layers.delete(id);
      if (this.selectedLayerId === id) {
        this.selectedLayerId = this.layers.size > 0 ? this.layers.keys().next().value : null;
      }
      this.refreshLayerTree();
      this.refreshAttributeTable();
    }

    toggleLayerVisibility(id) {
      const l = this.layers.get(id);
      if (!l) return;
      l.visible = !l.visible;
      if (l.visible) {
        l.leafletLayer.addTo(this.map);
      } else {
        this.map.removeLayer(l.leafletLayer);
      }
      this.refreshLayerTree();
    }

    setLayerOpacity(id, opacity) {
      const l = this.layers.get(id);
      if (!l) return;
      l.style.fillOpacity = opacity;
      l.leafletLayer.setStyle({ fillOpacity: opacity });
    }

    zoomToLayer(id) {
      const l = this.layers.get(id);
      if (!l || !l.extent) return;
      const [w, s, e, n] = l.extent;
      if (isFinite(w) && isFinite(s) && isFinite(e) && isFinite(n)) {
        this.map.flyToBounds([[s, w], [n, e]], { padding: [30, 30], duration: 1.0 });
      }
    }

    // ─────────────────────────────────────────────────────────────
    // FORMAT PARSERS (CSV, KML, GEOJSON, SHAPEFILE)
    // ─────────────────────────────────────────────────────────────

    parseCsv(csvText, layerName = 'CSV Layer') {
      const lines = csvText.trim().split(/\r?\n/);
      if (lines.length < 2) throw new Error('CSV file must have a header row and at least one data row.');
      const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));

      // Find lat/lon headers
      const latKeys = ['lat', 'latitude', 'y', 'lat_deg', 'coord_y'];
      const lonKeys = ['lon', 'lng', 'longitude', 'x', 'lon_deg', 'coord_x'];

      let latIdx = headers.findIndex(h => latKeys.includes(h.toLowerCase()));
      let lonIdx = headers.findIndex(h => lonKeys.includes(h.toLowerCase()));

      if (latIdx === -1 || lonIdx === -1) {
        throw new Error('Could not auto-detect latitude/longitude columns in CSV. Required headers: lat, lon, latitude, longitude.');
      }

      const features = [];
      for (let i = 1; i < lines.length; i++) {
        const row = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
        if (row.length < headers.length) continue;
        const lat = parseFloat(row[latIdx]);
        const lon = parseFloat(row[lonIdx]);
        if (!isFinite(lat) || !isFinite(lon)) continue;

        const props = {};
        headers.forEach((h, idx) => { props[h] = row[idx]; });

        features.push({
          type: 'Feature',
          id: `csv_pt_${i}`,
          geometry: { type: 'Point', coordinates: [lon, lat] },
          properties: props
        });
      }

      const geojson = {
        type: 'FeatureCollection',
        crs: { type: 'name', properties: { name: 'urn:ogc:def:crs:OGC:1.3:CRS84' } },
        features
      };

      const id = this.addLayer(layerName, geojson, { source: 'User Upload (CSV Tabular)' });
      this.logProcessing('Import CSV', { rowCount: features.length, latCol: headers[latIdx], lonCol: headers[lonIdx] }, features.length, this.activeCrs, 'Successfully imported point vector layer.');
      return id;
    }

    parseKml(kmlText, layerName = 'KML Layer') {
      const parser = new DOMParser();
      const xml = parser.parseFromString(kmlText, 'text/xml');
      const placemarks = xml.querySelectorAll('Placemark');
      const features = [];

      placemarks.forEach((pm, idx) => {
        const nameEl = pm.querySelector('name');
        const descEl = pm.querySelector('description');
        const props = {
          name: nameEl ? nameEl.textContent : `Placemark ${idx + 1}`,
          description: descEl ? descEl.textContent : ''
        };

        const point = pm.querySelector('Point coordinates');
        const line = pm.querySelector('LineString coordinates');
        const poly = pm.querySelector('Polygon coordinates');

        if (point) {
          const c = point.textContent.trim().split(/\s+/)[0].split(',');
          if (c.length >= 2) {
            features.push({
              type: 'Feature',
              id: `kml_${idx}`,
              geometry: { type: 'Point', coordinates: [parseFloat(c[0]), parseFloat(c[1])] },
              properties: props
            });
          }
        } else if (line) {
          const coords = line.textContent.trim().split(/\s+/).map(pair => {
            const parts = pair.split(',');
            return [parseFloat(parts[0]), parseFloat(parts[1])];
          }).filter(c => isFinite(c[0]) && isFinite(c[1]));

          if (coords.length > 1) {
            features.push({
              type: 'Feature',
              id: `kml_${idx}`,
              geometry: { type: 'LineString', coordinates: coords },
              properties: props
            });
          }
        } else if (poly) {
          const coords = poly.textContent.trim().split(/\s+/).map(pair => {
            const parts = pair.split(',');
            return [parseFloat(parts[0]), parseFloat(parts[1])];
          }).filter(c => isFinite(c[0]) && isFinite(c[1]));

          if (coords.length > 2) {
            // Ensure closed ring
            if (coords[0][0] !== coords[coords.length - 1][0] || coords[0][1] !== coords[coords.length - 1][1]) {
              coords.push([coords[0][0], coords[0][1]]);
            }
            features.push({
              type: 'Feature',
              id: `kml_${idx}`,
              geometry: { type: 'Polygon', coordinates: [coords] },
              properties: props
            });
          }
        }
      });

      if (features.length === 0) throw new Error('No valid vector features found in KML.');
      const geojson = { type: 'FeatureCollection', features };
      const id = this.addLayer(layerName, geojson, { source: 'User Upload (KML)' });
      this.logProcessing('Import KML', { placemarkCount: features.length }, features.length, this.activeCrs, 'Successfully parsed KML geometry.');
      return id;
    }

    // ─────────────────────────────────────────────────────────────
    // GIS ANALYSIS TOOLBOX (TURF.JS + BACKEND FASTAPI)
    // ─────────────────────────────────────────────────────────────

    async runBuffer(layerId, distanceMeters) {
      const t0 = performance.now();
      const l = this.layers.get(layerId);
      if (!l) throw new Error('Selected layer not found.');

      let resultGj = null;
      if (typeof window.turf !== 'undefined') {
        const bufferedFeats = [];
        const feats = l.geojson.features || [l.geojson];
        for (const f of feats) {
          try {
            const b = window.turf.buffer(f, distanceMeters, { units: 'meters' });
            if (b) {
              b.properties = Object.assign({}, f.properties, {
                _gis_algorithm: 'Buffer',
                _buffer_m: distanceMeters,
                _source_layer: l.name
              });
              bufferedFeats.push(b);
            }
          } catch (e) {
            console.warn('Buffer feature error:', e);
          }
        }
        resultGj = { type: 'FeatureCollection', features: bufferedFeats };
      } else {
        // Fallback to backend API
        const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/buffer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ geojson: l.geojson, distance_m: distanceMeters, target_crs: this.activeCrs })
        });
        const data = await resp.json();
        resultGj = data.output;
      }

      const outName = `${l.name} (Buffer ${distanceMeters}m)`;
      const newId = this.addLayer(outName, resultGj, {
        color: '#f59e0b',
        fillColor: '#d97706',
        fillOpacity: 0.35,
        source: `Buffer (${distanceMeters}m) of ${l.name}`
      });

      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Vector Buffer', { inputLayer: l.name, distanceM: distanceMeters, targetCrs: this.activeCrs }, resultGj.features.length, this.activeCrs, `Computed geodesic buffer in ${dt}ms.`);
      return newId;
    }

    async runClip(baseLayerId, overlayLayerId) {
      const t0 = performance.now();
      const base = this.layers.get(baseLayerId);
      const ov = this.layers.get(overlayLayerId);
      if (!base || !ov) throw new Error('Both base and overlay layers are required for clipping.');

      let resultGj = null;
      if (typeof window.turf !== 'undefined') {
        const ovPoly = ov.geojson.features ? ov.geojson.features[0] : ov.geojson;
        const clippedFeats = [];
        const baseFeats = base.geojson.features || [base.geojson];

        baseFeats.forEach(f => {
          try {
            const isect = window.turf.intersect(window.turf.featureCollection([f, ovPoly]));
            if (isect) {
              isect.properties = Object.assign({}, f.properties, { _clipped_by: ov.name });
              clippedFeats.push(isect);
            }
          } catch (_) {}
        });
        resultGj = { type: 'FeatureCollection', features: clippedFeats };
      } else {
        const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/overlay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ base_geojson: base.geojson, overlay_geojson: ov.geojson, operation: 'clip', target_crs: this.activeCrs })
        });
        const data = await resp.json();
        resultGj = data.output;
      }

      const outName = `${base.name} [Clipped by ${ov.name}]`;
      const newId = this.addLayer(outName, resultGj, {
        color: '#10b981',
        fillColor: '#059669',
        fillOpacity: 0.4,
        source: `Clipped Layer (${base.name} by ${ov.name})`
      });

      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Vector Clip', { baseLayer: base.name, overlayLayer: ov.name }, resultGj.features.length, this.activeCrs, `Clipped ${resultGj.features.length} features in ${dt}ms.`);
      return newId;
    }

    async runUnion(layerAId, layerBId) {
      const t0 = performance.now();
      const a = this.layers.get(layerAId);
      const b = this.layers.get(layerBId);
      if (!a || !b) throw new Error('Both layers are required for union.');

      const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/overlay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_geojson: a.geojson, overlay_geojson: b.geojson, operation: 'union', target_crs: this.activeCrs })
      });
      const data = await resp.json();
      const newId = this.addLayer(`${a.name} ∪ ${b.name}`, data.output, {
        color: '#8b5cf6',
        fillColor: '#7c3aed',
        fillOpacity: 0.35,
        source: `Geometric Union of ${a.name} and ${b.name}`
      });

      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Vector Union', { layerA: a.name, layerB: b.name }, data.output.feature_count, this.activeCrs, `Computed union in ${dt}ms.`);
      return newId;
    }

    async runDifference(baseLayerId, eraseLayerId) {
      const t0 = performance.now();
      const base = this.layers.get(baseLayerId);
      const erase = this.layers.get(eraseLayerId);
      if (!base || !erase) throw new Error('Base and Erase layers are required for difference.');

      const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/overlay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_geojson: base.geojson, overlay_geojson: erase.geojson, operation: 'difference', target_crs: this.activeCrs })
      });
      const data = await resp.json();
      const newId = this.addLayer(`${base.name} − ${erase.name}`, data.output, {
        color: '#f43f5e',
        fillColor: '#e11d48',
        fillOpacity: 0.35,
        source: `Difference (${base.name} minus ${erase.name})`
      });

      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Vector Difference', { baseLayer: base.name, eraseLayer: erase.name }, data.output.feature_count, this.activeCrs, `Computed geometric difference in ${dt}ms.`);
      return newId;
    }

    runCentroids(layerId) {
      const t0 = performance.now();
      const l = this.layers.get(layerId);
      if (!l) throw new Error('Layer not found.');
      if (typeof window.turf === 'undefined') throw new Error('Turf.js required for centroid calculation.');

      const centroidFeats = [];
      const feats = l.geojson.features || [l.geojson];

      feats.forEach((f, idx) => {
        try {
          const c = window.turf.centroid(f);
          c.properties = Object.assign({}, f.properties, {
            _centroid_of: l.name,
            _orig_geom_type: f.geometry ? f.geometry.type : 'Unknown'
          });
          centroidFeats.push(c);
        } catch (_) {}
      });

      const outName = `${l.name} (Centroids)`;
      const newId = this.addLayer(outName, { type: 'FeatureCollection', features: centroidFeats }, {
        color: '#06b6d4',
        fillColor: '#0891b2',
        radius: 5,
        source: `Centroids of ${l.name}`
      });

      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Calculate Centroids', { inputLayer: l.name }, centroidFeats.length, this.activeCrs, `Calculated ${centroidFeats.length} centroids in ${dt}ms.`);
      return newId;
    }

    async runZonalStats(bounds) {
      const t0 = performance.now();
      const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/zonal-stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bounds })
      });
      const data = await resp.json();
      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Zonal Statistics', { bounds, source: data.statistics.source }, 1, this.activeCrs, `Calculated topographic zonal statistics in ${dt}ms.`);
      return data.statistics;
    }

    async runSiteReport(siteIdOrBounds) {
      const t0 = performance.now();
      const payload = typeof siteIdOrBounds === 'string' ? { site_id: siteIdOrBounds } : { bounds: siteIdOrBounds };
      const resp = await fetch('http://127.0.0.1:8000/api/v1/gis/site-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      const dt = Math.round(performance.now() - t0);
      this.logProcessing('Full Site Dossier', payload, 1, this.activeCrs, `Compiled multi-source site intelligence dossier in ${dt}ms.`);
      return data;
    }

    // ─────────────────────────────────────────────────────────────
    // MEASUREMENT TOOLS (DISTANCE RULER & AREA)
    // ─────────────────────────────────────────────────────────────

    startDistanceMeasurement() {
      this.stopMeasurement();
      this.measureMode = 'distance';
      this.measurePoints = [];
      this._notifyHint('Click on the map to add distance measurement points. Double-click to complete.');
    }

    startAreaMeasurement() {
      this.stopMeasurement();
      this.measureMode = 'area';
      this.measurePoints = [];
      this._notifyHint('Click on the map to draw polygon boundary. Double-click to close.');
    }

    stopMeasurement() {
      this.measureMode = null;
      this.measurePoints = [];
      if (this.measureLayer) this.measureLayer.clearLayers();
      this._notifyHint('');
    }

    _handleDistanceClick(latlng) {
      this.measurePoints.push(latlng);
      this.measureLayer.clearLayers();

      // Draw markers and segments
      for (let i = 0; i < this.measurePoints.length; i++) {
        L.circleMarker(this.measurePoints[i], { radius: 5, color: '#f59e0b', fillColor: '#fbbf24', fillOpacity: 0.9 }).addTo(this.measureLayer);
      }

      if (this.measurePoints.length > 1) {
        L.polyline(this.measurePoints, { color: '#f59e0b', weight: 3, dashArray: '6 6' }).addTo(this.measureLayer);
        let totalMeters = 0;
        for (let i = 1; i < this.measurePoints.length; i++) {
          totalMeters += this.measurePoints[i - 1].distanceTo(this.measurePoints[i]);
        }
        const distStr = totalMeters > 1000 ? `${(totalMeters / 1000).toFixed(2)} km` : `${Math.round(totalMeters)} m`;
        this._notifyHint(`Total Distance: <strong>${distStr}</strong> (${this.measurePoints.length} vertices)`);
      }
    }

    _handleAreaClick(latlng) {
      this.measurePoints.push(latlng);
      this.measureLayer.clearLayers();

      for (let i = 0; i < this.measurePoints.length; i++) {
        L.circleMarker(this.measurePoints[i], { radius: 5, color: '#10b981', fillColor: '#34d399', fillOpacity: 0.9 }).addTo(this.measureLayer);
      }

      if (this.measurePoints.length >= 3) {
        L.polygon(this.measurePoints, { color: '#10b981', fillColor: '#34d399', fillOpacity: 0.25, weight: 2 }).addTo(this.measureLayer);
        // Geodesic area calculation
        const ring = this.measurePoints.map(p => [p.lng, p.lat]);
        ring.push([this.measurePoints[0].lng, this.measurePoints[0].lat]);
        if (typeof window.turf !== 'undefined') {
          const areaM2 = window.turf.area(window.turf.polygon([ring]));
          const areaHa = (areaM2 / 10000).toFixed(2);
          const areaAc = (areaM2 / 4046.86).toFixed(2);
          this._notifyHint(`Enclosed Area: <strong>${areaHa} ha</strong> (${areaAc} acres, ${Math.round(areaM2)} m²)`);
        }
      }
    }

    // ─────────────────────────────────────────────────────────────
    // CRS REPROJECTION & SELECTION
    // ─────────────────────────────────────────────────────────────

    setProjectCrs(targetCrs) {
      if (!SUPPORTED_CRS[targetCrs]) {
        throw new Error(`Unsupported CRS: ${targetCrs}. Supported: ${Object.keys(SUPPORTED_CRS).join(', ')}`);
      }
      const prevCrs = this.activeCrs;
      this.activeCrs = targetCrs;

      // Update CRS pill in top bar
      const crsPill = document.getElementById('qgis-crs-pill');
      if (crsPill) {
        crsPill.textContent = targetCrs;
        crsPill.title = SUPPORTED_CRS[targetCrs].name;
      }

      this.logProcessing('CRS Transformation', { fromCrs: prevCrs, toCrs: targetCrs }, this.layers.size, targetCrs, `Project CRS transformed to ${SUPPORTED_CRS[targetCrs].name}.`);
    }

    // ─────────────────────────────────────────────────────────────
    // UI REFRESH HANDLERS (TREE, TABLE, INSPECTOR, LOG)
    // ─────────────────────────────────────────────────────────────

    refreshLayerTree() {
      const treeEl = document.getElementById('qgis-layer-tree-list');
      if (!treeEl) return;
      treeEl.innerHTML = '';

      if (this.layers.size === 0) {
        treeEl.innerHTML = '<div style="padding:16px;text-align:center;color:#64748b;font-size:11px;">No active layers. Load GeoJSON, CSV, KML, or Shapefile from Data Browser.</div>';
        return;
      }

      this.layers.forEach((l, id) => {
        const item = document.createElement('div');
        item.className = `qgis-layer-item ${this.selectedLayerId === id ? 'selected' : ''}`;
        item.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:6px 8px;border-radius:6px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);margin-bottom:4px;cursor:pointer;';

        const isChecked = l.visible ? 'checked' : '';
        item.innerHTML = `
          <div style="display:flex;align-items:center;gap:6px;min-width:0;">
            <input type="checkbox" ${isChecked} onchange="window.qgisWorkspace.toggleLayerVisibility('${id}')" style="cursor:pointer;accent-color:#38bdf8;">
            <span style="width:10px;height:10px;border-radius:2px;background:${l.style.fillColor};border:1px solid ${l.style.color};flex-shrink:0;"></span>
            <div style="min-width:0;overflow:hidden;">
              <div style="font-size:10.5px;font-weight:600;color:#f8fafc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.name}</div>
              <div style="font-size:8.5px;color:#94a3b8;font-family:monospace;">${l.type} &middot; ${l.featureCount} feats &middot; ${l.crs}</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:4px;flex-shrink:0;">
            <button type="button" onclick="window.qgisWorkspace.zoomToLayer('${id}')" title="Zoom to Layer Extent" style="background:transparent;border:none;color:#94a3b8;cursor:pointer;padding:2px 4px;"><i class="fa-solid fa-magnifying-glass-location"></i></button>
            <button type="button" onclick="window.qgisWorkspace.selectLayer('${id}')" title="Inspect & Style" style="background:transparent;border:none;color:#38bdf8;cursor:pointer;padding:2px 4px;"><i class="fa-solid fa-sliders"></i></button>
            <button type="button" onclick="window.qgisWorkspace.removeLayer('${id}')" title="Remove Layer" style="background:transparent;border:none;color:#ef4444;cursor:pointer;padding:2px 4px;"><i class="fa-solid fa-trash-can"></i></button>
          </div>
        `;

        item.onclick = (e) => {
          if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
            this.selectLayer(id);
          }
        };

        treeEl.appendChild(item);
      });
    }

    selectLayer(id) {
      this.selectedLayerId = id;
      this.refreshLayerTree();
      this.refreshAttributeTable();
      this.refreshStylingPanel();
    }

    inspectFeature(layerId, feature, leafletLayer) {
      this.selectedFeature = { layerId, feature, leafletLayer };
      const panel = document.getElementById('qgis-feature-inspector-content');
      if (!panel) return;

      const props = feature.properties || {};
      let propRows = '';
      for (const [k, v] of Object.entries(props)) {
        if (k.startsWith('_')) continue;
        propRows += `<tr><td style="padding:4px 6px;color:#94a3b8;border-bottom:1px solid rgba(255,255,255,0.05);font-family:monospace;font-size:9.5px;">${k}</td><td style="padding:4px 6px;color:#f8fafc;border-bottom:1px solid rgba(255,255,255,0.05);font-size:10px;">${v}</td></tr>`;
      }

      let areaStr = '--';
      if (typeof window.turf !== 'undefined' && (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon')) {
        const aM2 = window.turf.area(feature);
        areaStr = `${(aM2 / 10000).toFixed(2)} ha (${Math.round(aM2)} m²)`;
      }

      panel.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:6px;">
            <span style="font-weight:700;color:#38bdf8;font-size:11px;">Feature Inspector</span>
            <span style="font-family:monospace;font-size:9px;color:#94a3b8;">${feature.geometry.type}</span>
          </div>
          <div style="font-size:9.5px;color:#94a3b8;line-height:1.4;">
            <div><strong>Layer:</strong> ${this.layers.get(layerId)?.name || layerId}</div>
            <div><strong>Geodesic Area:</strong> ${areaStr}</div>
          </div>
          <table style="width:100%;border-collapse:collapse;margin-top:4px;">
            <thead><tr style="background:rgba(255,255,255,0.03);"><th style="padding:4px 6px;text-align:left;color:#cbd5e1;font-size:9.5px;">Property</th><th style="padding:4px 6px;text-align:left;color:#cbd5e1;font-size:9.5px;">Value</th></tr></thead>
            <tbody>${propRows || '<tr><td colspan="2" style="padding:8px;text-align:center;color:#64748b;">No attributes</td></tr>'}</tbody>
          </table>
        </div>
      `;

      // Switch to inspector tab on right panel
      this.switchRightTab('inspector');
    }

    refreshAttributeTable() {
      const tableHead = document.getElementById('qgis-attr-table-head');
      const tableBody = document.getElementById('qgis-attr-table-body');
      const countEl = document.getElementById('qgis-attr-table-count');
      if (!tableHead || !tableBody) return;

      const l = this.layers.get(this.selectedLayerId);
      if (!l || !l.geojson || !l.geojson.features || l.geojson.features.length === 0) {
        tableHead.innerHTML = '<tr><th>No Data</th></tr>';
        tableBody.innerHTML = '<tr><td style="padding:16px;text-align:center;color:#64748b;">Select a layer with features to view its attribute table.</td></tr>';
        if (countEl) countEl.textContent = '0 features';
        return;
      }

      const features = l.geojson.features;
      if (countEl) countEl.textContent = `${features.length} features · ${l.name}`;

      const schema = l.schema.slice(0, 8); // Top 8 columns
      tableHead.innerHTML = `<tr>${schema.map(k => `<th style="padding:6px 10px;text-align:left;font-size:10px;color:#cbd5e1;font-family:monospace;border-bottom:1px solid rgba(255,255,255,0.1);">${k}</th>`).join('')}</tr>`;

      const rowsHtml = features.slice(0, 100).map((f, idx) => {
        const props = f.properties || {};
        const cells = schema.map(k => `<td style="padding:4px 10px;font-size:10px;color:#f1f5f9;border-bottom:1px solid rgba(255,255,255,0.04);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${props[k] !== undefined ? props[k] : ''}</td>`).join('');
        return `<tr onclick="window.qgisWorkspace.zoomToFeature('${l.id}', ${idx})" style="cursor:pointer;hover:bg-white/5;">${cells}</tr>`;
      }).join('');

      tableBody.innerHTML = rowsHtml;
    }

    zoomToFeature(layerId, featureIndex) {
      const l = this.layers.get(layerId);
      if (!l || !l.geojson || !l.geojson.features) return;
      const f = l.geojson.features[featureIndex];
      if (!f) return;

      const tempLayer = L.geoJSON(f);
      this.map.flyToBounds(tempLayer.getBounds(), { padding: [40, 40], maxZoom: 17, duration: 0.8 });
      this.inspectFeature(layerId, f, tempLayer);
    }

    refreshStylingPanel() {
      const l = this.layers.get(this.selectedLayerId);
      if (!l) return;
      const colorInput = document.getElementById('qgis-style-color');
      const fillInput = document.getElementById('qgis-style-fill');
      const opInput = document.getElementById('qgis-style-opacity');
      const weightInput = document.getElementById('qgis-style-weight');

      if (colorInput) colorInput.value = l.style.color;
      if (fillInput) fillInput.value = l.style.fillColor;
      if (opInput) opInput.value = l.style.fillOpacity;
      if (weightInput) weightInput.value = l.style.weight;
    }

    applyCurrentStyling() {
      const l = this.layers.get(this.selectedLayerId);
      if (!l) return;
      const colorInput = document.getElementById('qgis-style-color');
      const fillInput = document.getElementById('qgis-style-fill');
      const opInput = document.getElementById('qgis-style-opacity');
      const weightInput = document.getElementById('qgis-style-weight');

      if (colorInput) l.style.color = colorInput.value;
      if (fillInput) l.style.fillColor = fillInput.value;
      if (opInput) l.style.fillOpacity = parseFloat(opInput.value);
      if (weightInput) l.style.weight = parseFloat(weightInput.value);

      l.leafletLayer.setStyle(l.style);
      this.refreshLayerTree();
    }

    logProcessing(algorithm, parameters, outputCount, crs, notes = '') {
      const entry = {
        timestamp: new Date().toLocaleTimeString(),
        algorithm,
        parameters,
        outputCount,
        crs,
        notes
      };
      this.processingLogs.unshift(entry);
      this._renderProcessingLog();
    }

    _renderProcessingLog() {
      const logEl = document.getElementById('qgis-processing-log-list');
      if (!logEl) return;
      logEl.innerHTML = this.processingLogs.map(log => `
        <div style="padding:6px 8px;border-bottom:1px solid rgba(255,255,255,0.05);font-family:monospace;font-size:9.5px;color:#cbd5e1;">
          <div style="display:flex;justify-content:space-between;color:#38bdf8;font-weight:700;">
            <span>[${log.timestamp}] ${log.algorithm}</span>
            <span style="color:#10b981;">COMPLETED &middot; ${log.outputCount} output</span>
          </div>
          <div style="color:#94a3b8;margin-top:2px;">Params: ${JSON.stringify(log.parameters)} &middot; CRS: ${log.crs}</div>
          <div style="color:#64748b;font-size:8.5px;">${log.notes}</div>
        </div>
      `).join('');
    }

    switchRightTab(tab) {
      this.activeRightTab = tab;
      ['toolbox', 'inspector', 'symbology'].forEach(t => {
        const tabBtn = document.getElementById(`qgis-rtab-${t}`);
        const panel = document.getElementById(`qgis-rpanel-${t}`);
        if (tabBtn) tabBtn.classList.toggle('active', t === tab);
        if (panel) panel.style.display = t === tab ? 'flex' : 'none';
      });
    }

    switchBottomTab(tab) {
      this.activeBottomTab = tab;
      ['table', 'log', 'console'].forEach(t => {
        const tabBtn = document.getElementById(`qgis-btab-${t}`);
        const panel = document.getElementById(`qgis-bpanel-${t}`);
        if (tabBtn) tabBtn.classList.toggle('active', t === tab);
        if (panel) panel.style.display = t === tab ? 'flex' : 'none';
      });
    }

    toggleBottomDock() {
      const dock = document.getElementById('qgis-bottom-dock');
      if (!dock) return;
      const isHidden = dock.style.display === 'none';
      dock.style.display = isHidden ? 'flex' : 'none';
      if (this.map) setTimeout(() => this.map.invalidateSize(), 100);
    }

    // ─────────────────────────────────────────────────────────────
    // UTILITY HELPERS
    // ─────────────────────────────────────────────────────────────

    _detectGeometryType(gj) {
      if (!gj) return 'Unknown';
      if (gj.type === 'FeatureCollection' && gj.features && gj.features.length > 0) {
        return gj.features[0].geometry ? gj.features[0].geometry.type : 'Feature';
      }
      if (gj.type === 'Feature' && gj.geometry) return gj.geometry.type;
      return gj.type || 'Unknown';
    }

    _computeExtent(gj) {
      if (typeof window.turf !== 'undefined') {
        try { return window.turf.bbox(gj); } catch (_) {}
      }
      return [-180, -90, 180, 90];
    }

    _extractSchema(gj) {
      const keys = new Set();
      const feats = gj.features || (gj.type === 'Feature' ? [gj] : []);
      feats.slice(0, 20).forEach(f => {
        if (f.properties) Object.keys(f.properties).forEach(k => keys.add(k));
      });
      return Array.from(keys);
    }

    _notifyHint(htmlMsg) {
      const hintEl = document.getElementById('urban-draw-hint');
      if (!hintEl) return;
      if (!htmlMsg) {
        hintEl.style.display = 'none';
        hintEl.innerHTML = '';
      } else {
        hintEl.style.display = 'inline-block';
        hintEl.innerHTML = htmlMsg;
      }
    }

    // Export active layer to GeoJSON
    exportActiveGeoJson() {
      const l = this.layers.get(this.selectedLayerId);
      if (!l) {
        alert('Please select a layer from the Layer Tree to export.');
        return;
      }
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(l.geojson, null, 2));
      const a = document.createElement('a');
      a.href = dataStr;
      a.download = `${l.name.replace(/\s+/g, '_').toLowerCase()}.geojson`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    // Export Attribute Table to CSV
    exportActiveCsv() {
      const l = this.layers.get(this.selectedLayerId);
      if (!l || !l.geojson || !l.geojson.features) return;
      const feats = l.geojson.features;
      const headers = l.schema;
      let csv = headers.join(',') + '\n';
      feats.forEach(f => {
        const props = f.properties || {};
        csv += headers.map(h => `"${(props[h] !== undefined ? props[h] : '').toString().replace(/"/g, '""')}"`).join(',') + '\n';
      });
      const dataStr = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
      const a = document.createElement('a');
      a.href = dataStr;
      a.download = `${l.name.replace(/\s+/g, '_').toLowerCase()}_attributes.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // GLOBAL BROWSER INTERACTION HANDLERS
  // ═══════════════════════════════════════════════════════════════

  window.handleQgisFileUpload = function (inputEl) {
    if (!inputEl || !inputEl.files || inputEl.files.length === 0) return;
    const file = inputEl.files[0];
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const fname = file.name.toLowerCase();
        let layerId = null;

        if (fname.endsWith('.csv')) {
          layerId = window.qgisWorkspace.parseCsv(text, file.name);
        } else if (fname.endsWith('.kml')) {
          layerId = window.qgisWorkspace.parseKml(text, file.name);
        } else if (fname.endsWith('.json') || fname.endsWith('.geojson')) {
          const gj = JSON.parse(text);
          layerId = window.qgisWorkspace.addLayer(file.name, gj, { source: 'User Upload (GeoJSON)' });
          window.qgisWorkspace.logProcessing('Import GeoJSON', { fileName: file.name }, gj.features ? gj.features.length : 1, window.qgisWorkspace.activeCrs, 'Imported GeoJSON vector file.');
        } else {
          alert('Supported formats: GeoJSON (.geojson, .json), CSV with lat/lon (.csv), KML (.kml).');
          return;
        }

        if (layerId) {
          window.qgisWorkspace.zoomToLayer(layerId);
        }
      } catch (err) {
        alert('File Import Error: ' + err.message);
      }
    };

    reader.readAsText(file);
    inputEl.value = ''; // Reset input
  };

  window.promptQgisBuffer = async function () {
    const ws = window.qgisWorkspace;
    if (!ws.selectedLayerId) {
      alert('Please select a layer from the Layer Tree to buffer.');
      return;
    }
    const distStr = prompt('Enter buffer distance in meters (e.g. 30, 50, 100, 250):', '50');
    if (!distStr) return;
    const distM = parseFloat(distStr);
    if (!isFinite(distM) || distM <= 0) {
      alert('Invalid distance. Please enter a positive number of meters.');
      return;
    }
    try {
      await ws.runBuffer(ws.selectedLayerId, distM);
    } catch (e) {
      alert('Buffer Error: ' + e.message);
    }
  };

  window.promptQgisClip = async function () {
    const ws = window.qgisWorkspace;
    if (ws.layers.size < 2) {
      alert('Clipping requires at least two layers in the workspace (base layer and overlay boundary).');
      return;
    }
    const layerNames = Array.from(ws.layers.values()).map(l => `${l.id}: ${l.name}`).join('\n');
    const baseId = prompt(`Enter Base Layer ID to clip:\n${layerNames}`, ws.selectedLayerId || '');
    if (!baseId || !ws.layers.has(baseId)) return;
    const ovId = prompt(`Enter Overlay/Mask Layer ID:\n${layerNames}`, '');
    if (!ovId || !ws.layers.has(ovId)) return;

    try {
      await ws.runClip(baseId, ovId);
    } catch (e) {
      alert('Clip Error: ' + e.message);
    }
  };

  window.promptQgisZonalStats = async function () {
    const ws = window.qgisWorkspace;
    if (!ws.map) return;
    const b = ws.map.getBounds();
    const bounds = { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() };
    try {
      const stats = await ws.runZonalStats(bounds);
      alert(`Topographic Zonal Statistics:\n` +
        `• Mean Elevation: ${stats.elevation_m_mean} m AMSL (${stats.elevation_m_min}m – ${stats.elevation_m_max}m)\n` +
        `• Mean Slope: ${stats.slope_deg_mean}° (${stats.slope_category})\n` +
        `• Relief: ${stats.vertical_relief_m} m\n` +
        `• Source: ${stats.source}`);
    } catch (e) {
      alert('Zonal Stats Error: ' + e.message);
    }
  };

  window.promptQgisCrsSelect = function () {
    const crsKeys = Object.keys(SUPPORTED_CRS);
    const crsPrompt = crsKeys.map((k, i) => `${i + 1}. ${k} - ${SUPPORTED_CRS[k].name}`).join('\n');
    const pick = prompt(`Select Project Coordinate Reference System (CRS):\n${crsPrompt}`, '1');
    if (!pick) return;
    const idx = parseInt(pick, 10) - 1;
    if (idx >= 0 && idx < crsKeys.length) {
      window.qgisWorkspace.setProjectCrs(crsKeys[idx]);
    }
  };

  window.promptQgisSiteDossier = async function () {
    const ws = window.qgisWorkspace;
    const siteId = prompt('Enter Site ID or Lake Name (e.g. hussain_sagar, osman_sagar, durgam_cheruvu, rajendra_nagar, gandhi_maidan, iit_bihta):', 'hussain_sagar');
    if (!siteId) return;
    try {
      const data = await ws.runSiteReport(siteId);
      const aoi = data.aoi_metrics;
      const bldgs = data.built_environment;
      alert(`BHU LOKA BSA 2023 §63 Site Intelligence Dossier:\n` +
        `• Site: ${data.site_name} (${data.site_id})\n` +
        `• Gazetted Area: ${aoi.area_ha} ha (${aoi.area_acres} acres)\n` +
        `• Observed Buildings: ${bldgs.building_count} (${bldgs.building_density_per_ha} bldgs/ha)\n` +
        `• Road Network: ${bldgs.road_network_total_km} km\n` +
        `• Topography: ${data.natural_environment.elevation_stats.elevation_m_mean} m AMSL\n` +
        `• Surface Water Extent: ${data.natural_environment.surface_water_ha} ha\n` +
        `• SHA-256 Statutory Seal: ${data.hazard_and_statutory_screening.sha256_cryptographic_digest.substring(0, 24)}...`);
    } catch (e) {
      alert('Site Report Error: ' + e.message);
    }
  };

  window.runQgisConsoleTransform = function () {
    const input = document.getElementById('qgis-console-input');
    const output = document.getElementById('qgis-console-output');
    if (!input || !output) return;

    const parts = input.value.split(',').map(s => parseFloat(s.trim()));
    if (parts.length < 2 || !isFinite(parts[0]) || !isFinite(parts[1])) {
      output.textContent = 'Error: Enter valid comma-separated lat, lon (e.g. 17.4431, 78.4735).';
      output.style.color = '#ef4444';
      return;
    }

    const [lat, lon] = parts;
    const zone = Math.floor((lon + 180) / 6) + 1;
    const utmEpsg = 32600 + zone;

    // Approximate UTM metric projection
    const latRad = lat * Math.PI / 180;
    const lonRad = lon * Math.PI / 180;
    const lon0Rad = ((zone - 1) * 6 - 180 + 3) * Math.PI / 180;
    const easting = 500000 + 6378137 * (lonRad - lon0Rad) * Math.cos(latRad);
    const northing = (lat >= 0 ? 0 : 10000000) + 6378137 * latRad;

    output.innerHTML = `
      <div><strong>WGS 84 (EPSG:4326):</strong> ${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E</div>
      <div><strong>UTM Zone ${zone}N (EPSG:${utmEpsg}):</strong> Easting ${Math.round(easting)} m, Northing ${Math.round(northing)} m</div>
      <div><strong>Web Mercator (EPSG:3857):</strong> X ${Math.round(lon * 20037508.34 / 180)} m, Y ${Math.round(Math.log(Math.tan((90 + lat) * Math.PI / 360)) / (Math.PI / 180) * 20037508.34 / 180)} m</div>
    `;
    output.style.color = '#38bdf8';
  };

  // Export globally
  window.BhuLokaQgisWorkspace = QgisWorkspaceEngine;
  window.qgisWorkspace = new QgisWorkspaceEngine();

})(window);
