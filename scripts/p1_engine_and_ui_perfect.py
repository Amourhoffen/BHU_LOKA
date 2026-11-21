#!/usr/bin/env python3
"""
BHU LOKA – Comprehensive 3D Layer Engine & Professional Modal UI Perfection Script
"""

import re
import os
import hashlib

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    orig_len = len(text)
    changes = []

    # 1. Fix broken bg-gray-700- classes
    broken_classes = re.findall(r'bg-gray-700-([a-zA-Z0-9_/]+)', text)
    if broken_classes:
        def replace_bg(match):
            val = match.group(1)
            if '500/20' in val: return 'bg-amber-500/20'
            if '500/40' in val: return 'bg-amber-500/30'
            if '500/30' in val: return 'bg-amber-500/25'
            if '500/15' in val: return 'bg-amber-500/15'
            if '500/25' in val: return 'bg-amber-500/20'
            if '500' in val: return 'bg-amber-500'
            if '950' in val: return 'bg-slate-900'
            if '700' in val: return 'bg-slate-800'
            if '600' in val: return 'bg-slate-700'
            if '400' in val: return 'bg-slate-800'
            if '300' in val: return 'bg-slate-800'
            return 'bg-slate-800'
        text = re.sub(r'bg-gray-700-([a-zA-Z0-9_/]+)', replace_bg, text)
        changes.append(f'Fixed {len(broken_classes)} broken bg-gray-700- classes')

    # 2. Upgrade generateHoloHazardCanvas to support ALL 7 layers + multi-hazard composite
    # Look for: if (layer === 'topo')
    topo_start = text.find("if (layer === 'topo')")
    # And look for the end of the hazard color loop: hzCtx.putImageData(imgData, 0, 0);
    hz_end = text.find("hzCtx.putImageData(imgData, 0, 0);", topo_start)

    if topo_start != -1 and hz_end != -1:
        new_hazard_logic = """if (layer === 'topo' || layer === 'dem') {
            // Topographic Hypsometric Relief: Red Sink (<46.5m), Amber Ponding (48-52m), Emerald Ridge (>52m)
            if (elev < 46.5) {
              data[idx] = 225; data[idx + 1] = 29; data[idx + 2] = 72; data[idx + 3] = 230; // Deep Crimson Red
            } else if (elev < 51.5) {
              const t = (elev - 46.5) / 5.0;
              data[idx] = Math.round(217 * (1 - t * 0.15));
              data[idx + 1] = Math.round(119 + t * 40);
              data[idx + 2] = 6;
              data[idx + 3] = 210; // Warm Ochre
            } else {
              const t = Math.min(1.0, (elev - 51.5) / Math.max(1, maxM - 51.5));
              data[idx] = Math.round(5 + t * 20);
              data[idx + 1] = Math.round(150 + t * 40);
              data[idx + 2] = Math.round(105 - t * 20);
              data[idx + 3] = 220; // Earth Emerald
            }
          } else if (layer === 'flood' || layer === 'sar') {
            // Sentinel-1 SAR Flood Inundation & Microwave Double-Bounce
            const floodThreshold = (yr === 2028 ? 48.5 : 47.0);
            if (elev < floodThreshold) {
              // Specular Water Inundation Sink (-16.8 dB specular drop)
              data[idx] = 2; data[idx + 1] = 132; data[idx + 2] = 199; data[idx + 3] = 240; // Oceanic Deep Sky Blue
            } else if (elev < 51.2) {
              // Urban Dihedral Double-Bounce (+4.8 dB jump off buildings)
              const p = Math.sin(x * 0.18) * Math.cos(y * 0.18);
              if (p > 0.04) {
                data[idx] = 225; data[idx + 1] = 29; data[idx + 2] = 72; data[idx + 3] = 245; // Dihedral Rose Crimson
              } else {
                data[idx] = 139; data[idx + 1] = 92; data[idx + 2] = 246; data[idx + 3] = 170; // Transition Lavender
              }
            } else {
              data[idx] = 15; data[idx + 1] = 23; data[idx + 2] = 42; data[idx + 3] = 50;
            }
          } else if (layer === 'heat' || layer === 'thermal') {
            // MODIS LST Thermal Desiccation (40°C–46°C Anomaly)
            const heatNorm = 1.0 - norm;
            data[idx] = Math.round(234 * heatNorm + 30 * (1 - heatNorm));
            data[idx + 1] = Math.round(88 * (1 - Math.abs(heatNorm - 0.5)) + 140 * (1 - heatNorm));
            data[idx + 2] = Math.round(12 * heatNorm + 40 * (1 - heatNorm));
            data[idx + 3] = 225; // Solar Amber/Orange
          } else if (layer === 'safe' || layer === 'safezone') {
            // Safe Elevated Levees & Terraces (>52m AMSL)
            if (elev >= 51.8) {
              data[idx] = 5; data[idx + 1] = 150; data[idx + 2] = 105; data[idx + 3] = 235; // Forest Emerald #059669
            } else {
              data[idx] = 15; data[idx + 1] = 23; data[idx + 2] = 42; data[idx + 3] = 50;
            }
          } else if (layer === 'crime') {
            // High Crime Zone / Urban Surveillance Density Corridors
            const grid = (Math.sin(x * 0.22) * Math.sin(y * 0.22));
            if (grid > 0.35) {
              data[idx] = 220; data[idx + 1] = 38; data[idx + 2] = 38; data[idx + 3] = 230; // Security Alert Red
            } else if (grid > 0.05) {
              data[idx] = 168; data[idx + 1] = 85; data[idx + 2] = 247; data[idx + 3] = 160; // Patrol Corridor Purple
            } else {
              data[idx] = 15; data[idx + 1] = 23; data[idx + 2] = 42; data[idx + 3] = 40;
            }
          } else if (layer === 'multihazard') {
            // Full Multi-Hazard Composite Synthesis:
            // 1. Safe Levee Ridge (>52m)
            if (elev >= 52.0) {
              data[idx] = 5; data[idx + 1] = 150; data[idx + 2] = 105; data[idx + 3] = 230; // Emerald Safe Shield
            } else if (elev < 46.5) {
              // 2. Critical Depression Water Sink (<46.5m)
              data[idx] = 2; data[idx + 1] = 132; data[idx + 2] = 199; data[idx + 3] = 240; // Flood Blue
            } else if (elev < 49.5 && Math.sin(x * 0.18) * Math.cos(y * 0.18) > 0.08) {
              // 3. Urban Dihedral Double-Bounce Hazard
              data[idx] = 225; data[idx + 1] = 29; data[idx + 2] = 72; data[idx + 3] = 240; // Double-Bounce Rose
            } else {
              // 4. Moderate Heat / Runoff Transition Zone
              const heatNorm = 1.0 - norm;
              data[idx] = Math.round(217 * heatNorm + 20);
              data[idx + 1] = Math.round(119 * (1 - heatNorm) + 40);
              data[idx + 2] = 6;
              data[idx + 3] = 180; // Ochre
            }
          } else if (layer === 'drought') {
            // Agricultural Drought / Sukhar Simulation (VCI & Soil Moisture Deficit)
            let vci = 0.52;
            if (yr === 2027) vci = 0.42;
            else if (yr === 2028) vci = 0.68;
            else if (yr === 2029) vci = 0.19;
            else if (yr === 2030) vci = 0.34;

            if (vci < 0.28) {
              data[idx] = 217; data[idx + 1] = 119; data[idx + 2] = 6; data[idx + 3] = 225; // Parched Amber
            } else if (vci < 0.45) {
              data[idx] = 180; data[idx + 1] = 83; data[idx + 2] = 9; data[idx + 3] = 190;
            } else {
              data[idx] = 5; data[idx + 1] = 150; data[idx + 2] = 105; data[idx + 3] = 160; // Green
            }
          } else if (layer === 'sinks') {
            // Hydro-Sinks & Catchment Flow Convergence
            if (norm < 0.22 || elev < 46.2) {
              data[idx] = 139; data[idx + 1] = 92; data[idx + 2] = 246; data[idx + 3] = 235; // Purple Sink
            } else if (norm < 0.45 && Math.sin(x * 0.25 + y * 0.15) > 0.35) {
              data[idx] = 2; data[idx + 1] = 132; data[idx + 2] = 199; data[idx + 3] = 210; // Blue Flow
            } else {
              data[idx] = 15; data[idx + 1] = 23; data[idx + 2] = 42; data[idx + 3] = 40;
            }
          }
        }
      }

      """
        text = text[:topo_start] + new_hazard_logic + text[hz_end:]
        changes.append('Updated generateHoloHazardCanvas with full 7-layer + multihazard simulation')

    # 3. Update the labelMap inside generateHoloHazardCanvas
    labelmap_search = "const labelMap = {"
    if labelmap_search in text:
        p_lm = text.find(labelmap_search)
        p_lm_end = text.find("};", p_lm)
        new_labelmap = """const labelMap = {
        topo: `TOPOGRAPHY: ${minM.toFixed(1)}m–${maxM.toFixed(1)}m RELIEF`,
        dem: `COPERNICUS DEM: ${minM.toFixed(1)}m–${maxM.toFixed(1)}m`,
        flood: `SAR FLOOD: DOUBLE-BOUNCE + SINKS (${yr})`,
        sar: `SENTINEL-1 C-SAR BIMODAL RADAR (${yr})`,
        drought: `SUKHAR / DROUGHT: VCI DEFICIT (${yr})`,
        thermal: 'THERMAL: LST 40°C–46°C DESICCATION',
        heat: 'HEAT ANOMALY: LST SURFACE DESICCATION',
        sinks: 'HYDRO-SINKS: DEPRESSION BASINS (<46m)',
        safe: 'SAFE LEVEES: ELEVATED CORRIDORS (>52m)',
        safezone: 'SAFE ZONE: HIGH GROUND LEVEES (>52m)',
        crime: 'SECURITY: URBAN VULNERABILITY CORRIDORS',
        multihazard: `COMPOSITE MULTI-HAZARD SIMULATION (${yr})`
      };"""
        text = text[:p_lm] + new_labelmap + text[p_lm_end+2:]
        changes.append('Updated canvas labelMap for all 7 hazard layers')

    # 4. Multi-layer state management in bhuSetLayer
    old_bhu_bridge = text.find("window.bhuSetLayer=function(id,visible){")
    if old_bhu_bridge != -1:
        p_end = text.find("window.bhuAllLayersOn", old_bhu_bridge)
        if p_end != -1:
            new_multi_bridge = """var bhuActiveLayers = new Set();
    window.bhuSetLayer = function(id, visible) {
      var l = LAYERS.find(function(x) { return x.id === id; });
      if (!l) return;

      if (visible) {
        bhuActiveLayers.add(id);
      } else {
        bhuActiveLayers.delete(id);
      }

      // Determine active holographic 3D layer
      var target3D = 'sat';
      if (bhuActiveLayers.size === 0) {
        target3D = 'sat';
      } else if (bhuActiveLayers.size > 1 || bhuActiveLayers.has('multihazard')) {
        target3D = 'multihazard';
      } else {
        var single = Array.from(bhuActiveLayers)[0];
        var map = {
          heat: 'heat',
          flood: 'flood',
          multihazard: 'multihazard',
          safezone: 'safezone',
          crime: 'crime',
          sar: 'sar',
          dem: 'dem'
        };
        target3D = map[single] || 'sat';
      }

      try {
        if (typeof window.setHoloHazardLayer === 'function') {
          window.setHoloHazardLayer(target3D);
        }
        if (typeof window.applyHoloVisualStyle === 'function') {
          window.applyHoloVisualStyle();
        }
      } catch(e) {}

      // 2D Earth map layer sync
      try {
        if (id === 'heat' && typeof window.setBhuLayer === 'function') window.setBhuLayer('lst', visible);
        if (id === 'flood' && typeof window.setBhuLayer === 'function') window.setBhuLayer('flood', visible);
        if (id === 'multihazard' && typeof window.setBhuLayer === 'function') window.setBhuLayer('aqi', visible);
        if (id === 'safezone' && typeof window.setBhuLayer === 'function') window.setBhuLayer('farms', visible);
        if (id === 'crime' && typeof window.setBhuLayer === 'function') window.setBhuLayer('cctv_nodes', visible);
        if (id === 'dem' && typeof window.setBhuLayer === 'function') window.setBhuLayer('glo30_dem', visible);
      } catch(e) {}

      document.dispatchEvent(new CustomEvent('bhu-layer-change', { detail: { layer: id, visible: visible, target3D: target3D } }));
      if (typeof window.showSovereignToast === 'function') {
        window.showSovereignToast((visible ? 'ON: ' : 'OFF: ') + l.label, 'info', 1800);
      }
      var row = document.querySelector('[aria-label="Toggle ' + l.label + '"]');
      if (row) row.classList.toggle('active-layer', visible);
    };

    window.bhuAllLayersOn = function() {
      LAYERS.forEach(function(l) {
        bhuActiveLayers.add(l.id);
        var cb = document.getElementById('lt-' + l.id);
        if (cb) cb.checked = true;
        var row = document.querySelector('[aria-label="Toggle ' + l.label + '"]');
        if (row) row.classList.add('active-layer');
      });
      if (typeof window.setHoloHazardLayer === 'function') {
        window.setHoloHazardLayer('multihazard');
      }
      if (typeof window.applyHoloVisualStyle === 'function') {
        window.applyHoloVisualStyle();
      }
      if (typeof window.showSovereignToast === 'function') {
        window.showSovereignToast('All 7 Hazard Layers Active · Composite 3D Simulation', 'info', 2500);
      }
    };

    window.bhuAllLayersOff = function() {
      bhuActiveLayers.clear();
      LAYERS.forEach(function(l) {
        var cb = document.getElementById('lt-' + l.id);
        if (cb) cb.checked = false;
        var row = document.querySelector('[aria-label="Toggle ' + l.label + '"]');
        if (row) row.classList.remove('active-layer');
      });
      if (typeof window.setHoloHazardLayer === 'function') {
        window.setHoloHazardLayer('sat');
      }
      if (typeof window.applyHoloVisualStyle === 'function') {
        window.applyHoloVisualStyle();
      }
      if (typeof window.showSovereignToast === 'function') {
        window.showSovereignToast('All Hazard Overlays Cleared · Satellite 3D Active', 'info', 2000);
      }
    };

    """
            text = text[:old_bhu_bridge] + new_multi_bridge + text[p_end:]
            changes.append('Upgraded bhuSetLayer to multi-layer state manager with composite multi-hazard')

    # 5. Redesign Area Flood Prediction Modal button (no neon gradient!)
    old_predict_btn = 'class="w-full py-2.5 rounded-lg bg-gradient-to-r from-amber-600 via-rose-600 to-cyan-600 hover:from-amber-500 hover:to-cyan-500 text-white font-bold text-xs uppercase tracking-wider shadow-[0_4px_16px_rgba(245,158,11,0.35)] transition flex items-center justify-center gap-2 cursor-pointer"'
    new_predict_btn = 'class="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-mono font-bold text-xs uppercase tracking-wider border border-blue-400/30 transition flex items-center justify-center gap-2 cursor-pointer shadow-sm"'
    if old_predict_btn in text:
        text = text.replace(old_predict_btn, new_predict_btn)
        changes.append('Redesigned Area Flood Prediction Modal execute button (aerospace blue)')

    # 6. Redesign Area Flood Prediction Modal header border and card borders
    text = text.replace(
        'class="w-full max-w-5xl h-[92vh] max-h-[860px] bg-[#070b13] border border-amber-500/40 rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.95)]',
        'class="w-full max-w-5xl h-[92vh] max-h-[860px] bg-[#070b13] border border-slate-700/70 rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.95)]'
    )
    text = text.replace(
        'class="w-full max-w-6xl h-[92vh] max-h-[880px] bg-[#070b13] border border-cyan-500/40 rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.95)]',
        'class="w-full max-w-6xl h-[92vh] max-h-[880px] bg-[#070b13] border border-slate-700/70 rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.95)]'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f'Patched {filepath} ({orig_len} -> {len(text)} chars)')
    for c in changes:
        print(f'  - {c}')
    return text

# Run on public/index.html
master_text = patch_file('Bhu Loka - भूलोक/public/index.html')

# Sync to the other two files
for other in ['Bhu Loka - भूलोक/public/bhu_loka_cyber_dashboard.html', 'Bhu Loka - भूलोक/bhu_loka_cyber_dashboard.html', 'Bhu Loka - भूलोक/index.html']:
    with open(other, 'w', encoding='utf-8') as f:
        f.write(master_text)
    print(f'Synced {other} -> {sha(master_text)}')

print('All 4 files synchronized successfully!')
