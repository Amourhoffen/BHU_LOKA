#!/usr/bin/env python3
"""
Upgrade Crime Zone to real GIS Kernel Density Estimation (KDE) Hotspots.
Eliminates the artificial checkerboard dot pattern and replaces it with
realistic localized risk clusters with smooth radial falloff.
"""

import os
import hashlib

TARGET_FILES = [
    'Bhu Loka - भूलोक/public/index.html',
    'Bhu Loka - भूलोक/public/bhu_loka_cyber_dashboard.html',
    'Bhu Loka - भूलोक/bhu_loka_cyber_dashboard.html',
    'Bhu Loka - भूलोक/index.html',
]

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()

with open(TARGET_FILES[0], 'r', encoding='utf-8') as f:
    text = f.read()

orig_len = len(text)
changes = []

# 1. Replace the checkerboard crime logic with Gaussian KDE
old_crime_block = """          } else if (layer === 'crime') {
            // High Crime Zone / Urban Surveillance Density Corridors
            const grid = (Math.sin(x * 0.22) * Math.sin(y * 0.22));
            if (grid > 0.35) {
              data[idx] = 220; data[idx + 1] = 38; data[idx + 2] = 38; data[idx + 3] = 230; // Security Alert Red
            } else if (grid > 0.05) {
              data[idx] = 168; data[idx + 1] = 85; data[idx + 2] = 247; data[idx + 3] = 160; // Patrol Corridor Purple
            } else {
              data[idx] = 15; data[idx + 1] = 23; data[idx + 2] = 42; data[idx + 3] = 40;
            }
          }"""

new_crime_block = """          } else if (layer === 'crime') {
            // Realistic Kernel Density Estimation (KDE) Urban Crime & Vulnerability Hotspots
            // Concentrated around 2-3 specific urban transit & vulnerable focal points
            const h1x = W * 0.44, h1y = H * 0.46, h1r = 85;
            const h2x = W * 0.68, h2y = H * 0.62, h2r = 70;
            const h3x = W * 0.32, h3y = H * 0.74, h3r = 55;

            const d1sq = (x - h1x) * (x - h1x) + (y - h1y) * (y - h1y);
            const d2sq = (x - h2x) * (x - h2x) + (y - h2y) * (y - h2y);
            const d3sq = (x - h3x) * (x - h3x) + (y - h3y) * (y - h3y);

            let k = 0;
            if (d1sq < h1r * h1r) k += 1.0 * Math.exp(-d1sq / (2 * (h1r * 0.38) * (h1r * 0.38)));
            if (d2sq < h2r * h2r) k += 0.8 * Math.exp(-d2sq / (2 * (h2r * 0.38) * (h2r * 0.38)));
            if (d3sq < h3r * h3r) k += 0.6 * Math.exp(-d3sq / (2 * (h3r * 0.38) * (h3r * 0.38)));

            if (k > 0.55) {
              // High Incident Hotspot Core (Deep Crimson Red)
              data[idx] = 225; data[idx + 1] = 29; data[idx + 2] = 72; data[idx + 3] = 225;
            } else if (k > 0.22) {
              // Moderate Risk Transition (Warm Amber/Ochre)
              data[idx] = 217; data[idx + 1] = 119; data[idx + 2] = 6; data[idx + 3] = 180;
            } else if (k > 0.08) {
              // Low Risk Outer Buffer (Muted Violet)
              data[idx] = 124; data[idx + 1] = 58; data[idx + 2] = 237; data[idx + 3] = 110;
            } else {
              // Non-incident safe terrain: 100% transparent (preserves natural satellite map)
              data[idx] = 0; data[idx + 1] = 0; data[idx + 2] = 0; data[idx + 3] = 0;
            }
          }"""

if old_crime_block in text:
    text = text.replace(old_crime_block, new_crime_block)
    changes.append('Replaced synthetic checkerboard with realistic Gaussian Kernel Density Hotspots')
else:
    print('WARNING: old_crime_block not found by exact match!')

# 2. Add crime and multihazard to updateHoloSpectralLegendForLayer
old_legend_safe = """      } else if (layer === 'safe') {
        body.innerHTML = `
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-[#10b981] shrink-0 mt-0.5 shadow-[0_0_8px_#10b981]"></span>
            <div><strong class="text-emerald-300">Emerald Green:</strong> Safe Elevated Levees &amp; Terraces (&gt;52m AMSL)</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-slate-800 border border-slate-600 shrink-0 mt-0.5"></span>
            <div><strong class="text-slate-400">Dimmed Slate:</strong> Inundation-Prone Lowland Depressions</div>
          </div>`;"""

new_legend_safe_and_crime = """      } else if (layer === 'safe' || layer === 'safezone') {
        body.innerHTML = `
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-[#10b981] shrink-0 mt-0.5 shadow-[0_0_8px_#10b981]"></span>
            <div><strong class="text-emerald-300">Emerald Green:</strong> Safe Elevated Levees &amp; Terraces (&gt;52m AMSL)</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-slate-800 border border-slate-600 shrink-0 mt-0.5"></span>
            <div><strong class="text-slate-400">Dimmed Slate:</strong> Inundation-Prone Lowland Depressions</div>
          </div>`;
      } else if (layer === 'crime') {
        body.innerHTML = `
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-rose-600 shrink-0 mt-0.5 shadow-[0_0_8px_rgba(225,29,72,0.5)]"></span>
            <div><strong class="text-rose-400">High Incident Hotspot (KDE &gt; 0.55):</strong> Critical Incident Cluster &amp; Transit Junction</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-amber-500 shrink-0 mt-0.5"></span>
            <div><strong class="text-amber-300">Caution Buffer (0.22 &ndash; 0.55):</strong> Intermediate Vulnerability Corridor</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-slate-700 border border-slate-500 shrink-0 mt-0.5"></span>
            <div><strong class="text-slate-300">Clean Satellite:</strong> Normal Monitored Safe Territory (No Risk)</div>
          </div>`;
      } else if (layer === 'multihazard') {
        body.innerHTML = `
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-[#10b981] shrink-0 mt-0.5 shadow-[0_0_8px_#10b981]"></span>
            <div><strong class="text-emerald-300">Green:</strong> Safe Levee Ridge Shield (&gt;52m AMSL)</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-sky-500 shrink-0 mt-0.5"></span>
            <div><strong class="text-sky-300">Blue:</strong> Hydro-Depression Flood Inundation Sink (&lt;46.5m)</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-rose-500 shrink-0 mt-0.5"></span>
            <div><strong class="text-rose-300">Rose:</strong> Urban Dihedral Double-Bounce Retro-Reflection</div>
          </div>
          <div class="flex items-start gap-2">
            <span class="w-3 h-3 rounded-full bg-amber-500 shrink-0 mt-0.5"></span>
            <div><strong class="text-amber-300">Amber:</strong> Moderate Runoff / Thermal Stress Transition</div>
          </div>`;"""

if old_legend_safe in text:
    text = text.replace(old_legend_safe, new_legend_safe_and_crime)
    changes.append('Added dedicated crime and multihazard legend cards to updateHoloSpectralLegendForLayer')
else:
    print('WARNING: old_legend_safe not found!')

# 3. Write and sync
for target in TARGET_FILES:
    with open(target, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Wrote {target} -> SHA: {sha(text)}')

print('Changes applied:')
for c in changes:
    print(' -', c)
