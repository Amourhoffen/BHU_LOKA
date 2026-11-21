import re
import os
import shutil
import subprocess

print("=== EXECUTING COMPLETE URBAN SPATIAL INTELLIGENCE PIPELINE ===")

BASE_DIR = r"Bhu Loka - भूलोक"
STUDIO_JS = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
ML_JS = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_ml_inference.js")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
CYBER_HTML = os.path.join(BASE_DIR, "bhu_loka_cyber_dashboard.html")

# 1. Update STUDIO_JS to add startCircleDraw and window methods
with open(STUDIO_JS, "r", encoding="utf-8") as f:
    studio_code = f.read()

# Add startCircleDraw if not already present
if "startCircleDraw()" not in studio_code:
    rect_draw_target = """    startRectDraw() {
      if (!this.map) return;
      this.stopDraw();
      if (this.map.pm) {
        this.map.pm.enableDraw('Rectangle', { snappable: true });
        this._hint('Click two corners on the map to draw a Rectangle AOI');
        return;
      }
      this.drawMode = 'rect';
      this.map.dragging.disable();
      this.map.getContainer().style.cursor = 'crosshair';
      this._hint('Click & drag to draw Rectangle AOI');
    }"""

    rect_and_circle = """    startRectDraw() {
      if (!this.map) return;
      this.stopDraw();
      if (this.map.pm) {
        this.map.pm.enableDraw('Rectangle', { snappable: true });
        this._hint('Click two corners on the map to draw a Rectangle / Square AOI');
        return;
      }
      this.drawMode = 'rect';
      this.map.dragging.disable();
      this.map.getContainer().style.cursor = 'crosshair';
      this._hint('Click & drag to draw Rectangle AOI');
    }

    startCircleDraw() {
      if (!this.map) return;
      this.stopDraw();
      if (this.map.pm) {
        this.map.pm.enableDraw('Circle', { snappable: true });
        this._hint('Click center and drag radius on map to draw Circle AOI (Radial Buffer)');
        return;
      }
      this._hint('Geoman PM required for Circle AOI');
    }"""

    if rect_draw_target in studio_code:
        studio_code = studio_code.replace(rect_draw_target, rect_and_circle)
        print("Added startCircleDraw method to UrbanLeafletEngine")
    else:
        print("Warning: rect_draw_target not found")

# Add window.startUrbanCircleDraw and window.setUrbanMeshType
if "window.startUrbanCircleDraw" not in studio_code:
    window_rect_target = "  window.startUrbanRectDraw = () => { if (ctrl.leaflet) ctrl.leaflet.startRectDraw(); };"
    window_rect_and_circle = """  window.startUrbanRectDraw = () => { if (ctrl.leaflet) ctrl.leaflet.startRectDraw(); };
  window.startUrbanCircleDraw = () => { if (ctrl.leaflet) ctrl.leaflet.startCircleDraw(); };
  window.setUrbanMeshType = (mode) => {
    window.urbanActiveMeshMode = mode;
    ['hex', 'square'].forEach(m => {
      const btn = document.getElementById(`urban-mesh-${m}`);
      if (btn) btn.classList.toggle('active', m === mode);
    });
    if (ctrl.dataset && ctrl.leaflet) {
      ctrl.leaflet.renderExtractedLayers(ctrl.dataset, ctrl.layerVis, ctrl.layerOp);
    }
  };"""
    if window_rect_target in studio_code:
        studio_code = studio_code.replace(window_rect_target, window_rect_and_circle)
        print("Added window.startUrbanCircleDraw and window.setUrbanMeshType")

with open(STUDIO_JS, "w", encoding="utf-8") as f:
    f.write(studio_code)

# 2. Update HTML files (index.html and bhu_loka_cyber_dashboard.html)
def update_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # A. Update CartoDB raster tile url in crop studio
    old_carto_tile = 'img.src = (basemap === \'osm\')\n            ? `https://basemaps.cartocdn.com/rastertiles/voyager/${zoom}/${tx}/${ty}.png`\n            : `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${zoom}/${ty}/${tx}`;'
    new_carto_tile = 'img.src = (basemap === \'osm\')\n            ? `https://tile.openstreetmap.org/${zoom}/${tx}/${ty}.png`\n            : `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${zoom}/${ty}/${tx}`;'
    if old_carto_tile in html:
        html = html.replace(old_carto_tile, new_carto_tile)
        print(f"[{os.path.basename(filepath)}] Replaced CartoDB tile URL with OSM standard tile URL")
    else:
        # Try regex replacement if whitespace differed
        html = re.sub(
            r'img\.src\s*=\s*\(basemap\s*===\s*[\'"]osm[\'"]\)\s*\?\s*`https://basemaps\.cartocdn\.com/rastertiles/voyager/\$\{zoom\}/\$\{tx\}/\$\{ty\}\.png`',
            'img.src = (basemap === \'osm\') ? `https://tile.openstreetmap.org/${zoom}/${tx}/${ty}.png`',
            html
        )
        print(f"[{os.path.basename(filepath)}] Replaced CartoDB tile URL via regex")

    # B. Update draw buttons row to include Circle
    old_draw_row = """            <div style="display:grid;grid-template-columns:1fr 1fr auto;gap:4px;">
              <button type="button" id="urban-draw-rect" class="us3-btn" onclick="startUrbanRectDraw()" title="Draw Rectangle AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg> <span>Rect</span>
              </button>
              <button type="button" id="urban-draw-poly" class="us3-btn" onclick="startUrbanPolyDraw()" title="Draw Polygon AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 18 21 6 21 2 8.5 12 2"/></svg> <span>Poly</span>
              </button>
              <button type="button" id="urban-clear-aoi" class="us3-btn" onclick="clearUrbanAOI()" title="Clear AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              </button>
            </div>"""

    new_draw_row = """            <div style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:4px;">
              <button type="button" id="urban-draw-rect" class="us3-btn" onclick="startUrbanRectDraw()" title="Draw Rectangle / Square AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg> <span>Rect</span>
              </button>
              <button type="button" id="urban-draw-circle" class="us3-btn" onclick="startUrbanCircleDraw()" title="Draw Radial Circle AOI (Buffer)">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/></svg> <span>Circle</span>
              </button>
              <button type="button" id="urban-draw-poly" class="us3-btn" onclick="startUrbanPolyDraw()" title="Draw Polygon AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 18 21 6 21 2 8.5 12 2"/></svg> <span>Poly</span>
              </button>
              <button type="button" id="urban-clear-aoi" class="us3-btn" onclick="clearUrbanAOI()" title="Clear AOI">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
              </button>
            </div>"""

    if old_draw_row in html:
        html = html.replace(old_draw_row, new_draw_row)
        print(f"[{os.path.basename(filepath)}] Added Circle AOI draw button")

    # C. Update 2D controls to add Hex / Square toggle switch
    old_2d_controls = """            <div id="urban-2d-controls" style="display:flex;align-items:center;gap:4px;">
              <span id="urban-draw-hint" style="display:none;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#38bdf8;margin-right:6px;"></span>
              <button type="button" id="urban-basemap-satellite" class="us3-btn active" onclick="switchUrbanBasemap('satellite')">Satellite</button>
              <button type="button" id="urban-basemap-osm" class="us3-btn" onclick="switchUrbanBasemap('osm')">OSM</button>
              <button type="button" id="urban-basemap-terrain" class="us3-btn" onclick="switchUrbanBasemap('terrain')">Terrain</button>
              <button type="button" id="urban-basemap-dark" class="us3-btn" onclick="switchUrbanBasemap('dark')">Dark</button>
            </div>"""

    new_2d_controls = """            <div id="urban-2d-controls" style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
              <span id="urban-draw-hint" style="display:none;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#38bdf8;margin-right:6px;"></span>
              <button type="button" id="urban-basemap-satellite" class="us3-btn active" onclick="switchUrbanBasemap('satellite')">Satellite</button>
              <button type="button" id="urban-basemap-osm" class="us3-btn" onclick="switchUrbanBasemap('osm')">OSM</button>
              <button type="button" id="urban-basemap-terrain" class="us3-btn" onclick="switchUrbanBasemap('terrain')">Terrain</button>
              <button type="button" id="urban-basemap-dark" class="us3-btn" onclick="switchUrbanBasemap('dark')">Dark</button>
              <div style="display:inline-flex;align-items:center;gap:2px;background:#050811;padding:2px 4px;border-radius:5px;border:1px solid rgba(255,255,255,0.08);margin-left:4px;">
                <span style="font-size:9px;color:#94a3b8;font-weight:600;padding:0 2px;">Zone Grid:</span>
                <button type="button" id="urban-mesh-hex" class="us3-btn active" onclick="setUrbanMeshType('hex')" style="font-size:9px;padding:2px 5px;" title="Honeycomb Hexagonal Mesh">⬡ Hex</button>
                <button type="button" id="urban-mesh-square" class="us3-btn" onclick="setUrbanMeshType('square')" style="font-size:9px;padding:2px 5px;" title="Square Block Grid">⬛ Square</button>
              </div>
            </div>"""

    if old_2d_controls in html:
        html = html.replace(old_2d_controls, new_2d_controls)
        print(f"[{os.path.basename(filepath)}] Added Zone Grid (Hex / Square) toggle switch to 2D toolbar")

    # D. Add Object Identity Decoder floating legend inside urban-2d-panel
    old_map_panel = """          <div id="urban-2d-panel" style="flex:1 1 auto;min-height:0;display:flex;flex-direction:column;position:relative;width:100%;height:100%;">
            <div id="urban-leaflet-map" style="width:100%;height:100%;min-height:350px;position:absolute;inset:0;background:#09090B;z-index:1;"></div>
          </div>"""

    new_map_panel = """          <div id="urban-2d-panel" style="flex:1 1 auto;min-height:0;display:flex;flex-direction:column;position:relative;width:100%;height:100%;">
            <div id="urban-leaflet-map" style="width:100%;height:100%;min-height:350px;position:absolute;inset:0;background:#09090B;z-index:1;"></div>
            <!-- AI Optical / Color Spectral Object Decoder Legend -->
            <div id="urban-spectral-legend" style="position:absolute;top:10px;right:10px;z-index:900;display:flex;align-items:center;gap:7px;background:rgba(5,8,17,0.88);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.12);padding:4px 9px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#e2e8f0;pointer-events:auto;box-shadow:0 4px 16px rgba(0,0,0,0.5);">
              <span style="color:#94a3b8;font-weight:700;">AI DECODER:</span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Concrete / RCC Roofs"><span style="width:8px;height:8px;border-radius:2px;background:#f8fafc;border:1px solid #94a3b8;"></span> <strong style="color:#f8fafc;">Bldgs</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Terracotta / Brick Red Roofs"><span style="width:8px;height:8px;border-radius:2px;background:#ea580c;"></span> <strong style="color:#ea580c;">Terracotta</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Galvanized / Metal Tin Roofs"><span style="width:8px;height:8px;border-radius:2px;background:#0284c7;"></span> <strong style="color:#38bdf8;">Tin</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Individual Trees & Green Canopy"><span style="width:8px;height:8px;border-radius:2px;background:#10b981;"></span> <strong style="color:#34d399;">Trees</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Designated Parks & Grounds"><span style="width:8px;height:8px;border-radius:2px;background:#059669;"></span> <strong style="color:#10b981;">Parks</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Lakes, Ponds & Statutory 30m FTL Buffer"><span style="width:8px;height:8px;border-radius:2px;background:#0284c7;"></span> <strong style="color:#38bdf8;">Water/FTL</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Road Hierarchy"><span style="width:8px;height:8px;border-radius:2px;background:#94a3b8;"></span> <strong style="color:#cbd5e1;">Roads</strong></span>
              <span style="display:inline-flex;align-items:center;gap:3px;" title="Railway Tracks & Corridors (Anti-Hallucination Masked)"><span style="width:8px;height:2px;background:#f59e0b;border-top:1px dashed #f59e0b;"></span> <strong style="color:#fbbf24;">Rail</strong></span>
            </div>
          </div>"""

    if old_map_panel in html:
        html = html.replace(old_map_panel, new_map_panel)
        print(f"[{os.path.basename(filepath)}] Added AI Spectral Object Decoder Legend to 2D Map viewport")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[{os.path.basename(filepath)}] Written successfully")

update_html(INDEX_HTML)
update_html(CYBER_HTML)

# 3. Synchronize to public/
for src in [STUDIO_JS, ML_JS, INDEX_HTML, CYBER_HTML]:
    rel = os.path.relpath(src, BASE_DIR)
    dst = os.path.join(BASE_DIR, "public", rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Synchronized {rel} -> public/{rel}")

print("=== COMPLETE PIPELINE EXECUTED SUCCESSFULLY ===")
