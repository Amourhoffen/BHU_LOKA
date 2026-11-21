import re
import os
import shutil

print("=== STARTING ADVANCED OBJECT-SPECIFIC GEOSPATIAL RE-ENGINEERING ===")

BASE_DIR = r"Bhu Loka - भूलोक"
STUDIO_JS = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_urban_studio.js")
ML_JS = os.path.join(BASE_DIR, "Assets", "vendor", "bhu_loka_ml_inference.js")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
CYBER_HTML = os.path.join(BASE_DIR, "bhu_loka_cyber_dashboard.html")

# 1. Update bhu_loka_ml_inference.js
with open(ML_JS, "r", encoding="utf-8") as f:
    ml_code = f.read()

# Update detectRooftopsFromSatellite signature and add railway, water, park exclusion
old_sig = "function detectRooftopsFromSatellite(bounds, aoiGeoJson, existingOsmBuildings = [], existingOsmRoads = [], mode = 'balanced')"
new_sig = "function detectRooftopsFromSatellite(bounds, aoiGeoJson, existingOsmBuildings = [], existingOsmRoads = [], mode = 'balanced', existingOsmInfra = [], existingOsmWater = [], existingOsmGreen = [])"

if old_sig in ml_code:
    ml_code = ml_code.replace(old_sig, new_sig)
    print("Updated detectRooftopsFromSatellite signature in ML JS")

# Add railway and water/park drawing to exCvs in detectRooftopsFromSatellite
old_ex_block = """    exCtx.fillStyle = '#fff';
    (existingOsmBuildings || []).forEach((f) => {
      if (!f.geometry || f.geometry.type !== 'Polygon') return;
      exCtx.beginPath();
      f.geometry.coordinates[0].forEach(([lon, lat], i) => {
        const [px, py] = toPx(lon, lat);
        if (i === 0) exCtx.moveTo(px, py); else exCtx.lineTo(px, py);
      });
      exCtx.closePath(); exCtx.fill();
    });
    const exMask = exCvs.getImageData(0, 0, W, H).data;"""

new_ex_block = """    // Railway tracks exclusion (buffer 30m)
    exCtx.strokeStyle = '#fff';
    exCtx.lineWidth = Math.max(3, Math.round(7.2 / Math.max(0.4, spanX_m / W)));
    (existingOsmInfra || []).forEach((f) => {
      if (!f.geometry) return;
      const isRail = f.properties && (f.properties.railway || f.properties._layer === 'railway' || f.properties.highway === 'railway');
      if (!isRail) return;
      if (f.geometry.type === 'LineString') {
        exCtx.beginPath();
        f.geometry.coordinates.forEach(([lon, lat], i) => {
          const [px, py] = toPx(lon, lat);
          if (i === 0) exCtx.moveTo(px, py); else exCtx.lineTo(px, py);
        });
        exCtx.stroke();
      }
    });

    // Water bodies & Canals exclusion mask
    exCtx.fillStyle = '#fff';
    (existingOsmWater || []).forEach((f) => {
      if (!f.geometry) return;
      const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates[0]] : (f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates.map(c => c[0]) : []);
      polys.forEach(ring => {
        exCtx.beginPath();
        ring.forEach(([lon, lat], i) => {
          const [px, py] = toPx(lon, lat);
          if (i === 0) exCtx.moveTo(px, py); else exCtx.lineTo(px, py);
        });
        exCtx.closePath(); exCtx.fill();
      });
    });

    // Designated Parks & Sports pitches exclusion mask
    (existingOsmGreen || []).forEach((f) => {
      if (!f.geometry) return;
      const isPark = f.properties && (f.properties._kind === 'park' || ['park', 'pitch', 'stadium', 'track'].includes(f.properties.leisure));
      if (!isPark) return;
      const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates[0]] : [];
      polys.forEach(ring => {
        exCtx.beginPath();
        ring.forEach(([lon, lat], i) => {
          const [px, py] = toPx(lon, lat);
          if (i === 0) exCtx.moveTo(px, py); else exCtx.lineTo(px, py);
        });
        exCtx.closePath(); exCtx.fill();
      });
    });

    // Existing Buildings exclusion mask
    (existingOsmBuildings || []).forEach((f) => {
      if (!f.geometry || f.geometry.type !== 'Polygon') return;
      exCtx.beginPath();
      f.geometry.coordinates[0].forEach(([lon, lat], i) => {
        const [px, py] = toPx(lon, lat);
        if (i === 0) exCtx.moveTo(px, py); else exCtx.lineTo(px, py);
      });
      exCtx.closePath(); exCtx.fill();
    });
    const exMask = exCvs.getImageData(0, 0, W, H).data;"""

if old_ex_block in ml_code:
    ml_code = ml_code.replace(old_ex_block, new_ex_block)
    print("Enhanced exclusion mask on ML canvas (railway + water + parks)")

with open(ML_JS, "w", encoding="utf-8") as f:
    f.write(ml_code)

print("ML JS updated successfully.")
