"""
BHU LOKA - Google Earth Engine (GEE) Data Export & Analysis Pipeline
Harvested from Repos/earthengine-api and Repos/flood-mapping-tool.
Automates acquisition of Sentinel-1 C-SAR GRD, Copernicus 30m DEM, and MODIS Terra LST
for Patna Municipal Corporation (PMC).
"""

import os
import json

def generate_gee_javascript_script():
    """
    Generates ready-to-run Google Earth Engine Code Editor JavaScript script
    for Patna multi-hazard analysis.
    """
    js_content = """// =========================================================================
// BHU LOKA (भूलोक) - GOOGLE EARTH ENGINE SOVEREIGN MONITORING SCRIPT
// Target: Patna Municipal Corporation (PMC), Bihar, India
// Researcher: Prince Kumar (IIT Patna, PA2511CDH37)
// Supervisor: Pallav Rustogi
// =========================================================================

// 1. Define Area of Interest (Patna Municipal Core)
var patna_bounds = ee.Geometry.Rectangle([85.0006, 25.5321, 85.2514, 25.6542]);
Map.centerObject(patna_bounds, 12);
Map.setOptions('HYBRID');

// 2. Sentinel-1 SAR GRD Pre-Flood (Aug 2019) vs Peak Flood (Sept 28 - Oct 2, 2019)
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
  .filterBounds(patna_bounds);

var pre_flood = s1.filterDate('2019-08-01', '2019-08-31').select('VH').median().clip(patna_bounds);
var post_flood = s1.filterDate('2019-09-28', '2019-10-04').select('VH').median().clip(patna_bounds);

// Delta Backscatter (Post - Pre)
var delta_sigma0 = post_flood.subtract(pre_flood).rename('delta_sigma0');

// Bimodal Inundation: Specular Drop (< -3.0 dB) OR Urban Corner Double-Bounce (> +1.5 dB)
var open_water_flood = delta_sigma0.lt(-3.0);
var urban_double_bounce_flood = delta_sigma0.gt(1.5);
var bhu_loka_total_flood = open_water_flood.or(urban_double_bounce_flood);

// 3. Copernicus GLO-30 Digital Elevation Model (DEM) & Depression Sinks
var dem = ee.ImageCollection('COPERNICUS/DEM/GLO30')
  .select('DEM')
  .mosaic()
  .clip(patna_bounds);

var slope = ee.Terrain.slope(dem);
var sinks = dem.lt(47.0).and(slope.lt(1.5)); // Low elevation flat depressions

// 4. NASA MODIS Terra LST Pre-Monsoon Summer 2019 (May 2019 Heatwave)
var modis_lst = ee.ImageCollection('MODIS/061/MOD11A2')
  .filterDate('2019-05-01', '2019-05-31')
  .select('LST_Day_1km')
  .mean()
  .multiply(0.02)
  .subtract(273.15)
  .clip(patna_bounds);

// 5. Visualization Layers
Map.addLayer(dem, {min: 40, max: 55, palette: ['#0d0887', '#6a00a8', '#b12a90', '#e16462', '#fca636', '#f0f921']}, 'Copernicus 30m DEM');
Map.addLayer(sinks.updateMask(sinks), {palette: ['#00ffff']}, 'Depression Sinks (< 47m)');
Map.addLayer(open_water_flood.updateMask(open_water_flood), {palette: ['#0000ff']}, 'SAR Specular Open Flood');
Map.addLayer(urban_double_bounce_flood.updateMask(urban_double_bounce_flood), {palette: ['#ff00ff']}, 'SAR Urban Double-Bounce Flood');
Map.addLayer(modis_lst, {min: 35, max: 47, palette: ['blue', 'yellow', 'red']}, 'NASA MODIS Pre-Monsoon LST (°C)');

print('BHU LOKA GEE Layers Loaded Successfully.');
"""
    return js_content

def run_export_pipeline():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Pipelines")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "bhu_loka_patna_gee_script.js")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(generate_gee_javascript_script())
    print(f"GEE Script successfully exported to: {out_file}")

if __name__ == "__main__":
    run_export_pipeline()

