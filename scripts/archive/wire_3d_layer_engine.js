const fs = require('fs');
const path = require('path');

const targetFiles = [
  path.join(__dirname, 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'index.html'),
  path.join(__dirname, 'index.html')
];

const layerEngineScript = `
  <script>
  /* ── 3D HAZARD & MULTI-LAYER ENGINE BRIDGE ── */
  window.setBhuLayerVisibility = function(layerId, active) {
    try {
      switch (layerId) {
        case 'heat': // Heat Area (Red)
          if (typeof indiaLstGroup !== 'undefined' && indiaLstGroup) indiaLstGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] Heat Area: ' + (active ? 'ON · NASA MODIS 46.2°C Thermal Anomaly' : 'OFF'), active ? 'warn' : 'info', 2200);
          }
          break;

        case 'flood': // Flood Zone (Blue)
          if (typeof indiaFloodOverlayGroup !== 'undefined' && indiaFloodOverlayGroup) indiaFloodOverlayGroup.visible = active;
          if (typeof terrainFloodMesh !== 'undefined' && terrainFloodMesh) terrainFloodMesh.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] Flood Zone: ' + (active ? 'ON · Sentinel-1 SAR 94.08 km² Inundation' : 'OFF'), active ? 'info' : 'info', 2200);
          }
          break;

        case 'multihazard': // Multi-Hazard Zone (Orange)
          if (typeof indiaDroughtGroup !== 'undefined' && indiaDroughtGroup) indiaDroughtGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] Multi-Hazard: ' + (active ? 'ON · Drought VCI <35% & Heat Overlap' : 'OFF'), active ? 'warn' : 'info', 2200);
          }
          break;

        case 'safe': // Safe Zone (Green)
          if (typeof indiaLandCorridorsGroup !== 'undefined' && indiaLandCorridorsGroup) indiaLandCorridorsGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] Safe Refuge: ' + (active ? 'ON · Bihta / IIT Patna >52m Safe Corridors' : 'OFF'), active ? 'success' : 'info', 2200);
          }
          break;

        case 'crime': // High-Crime Zone / Urban Surveillance (Purple)
          if (typeof indiaUrbanCctvGroup !== 'undefined' && indiaUrbanCctvGroup) indiaUrbanCctvGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] Security Grid: ' + (active ? 'ON · Municipal Surveillance & Incident Hotspots' : 'OFF'), active ? 'warn' : 'info', 2200);
          }
          break;

        case 'sar': // SAR / Flood SAR (Cyan)
          if (typeof indiaWaterDynGroup !== 'undefined' && indiaWaterDynGroup) indiaWaterDynGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] SAR Microwave: ' + (active ? 'ON · Specular Reflection -16.8 dB' : 'OFF'), active ? 'info' : 'info', 2200);
          }
          break;

        case 'dem': // DEM / Elevation (Amber)
          if (typeof terrainGroup !== 'undefined' && terrainGroup) {
            // DEM topography toggle
          }
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D LAYER] 3D DEM Topo: ' + (active ? 'ON · Copernicus 30m Global Elevation Model' : 'OFF'), active ? 'info' : 'info', 2200);
          }
          break;
      }
    } catch (e) {
      console.warn('[3D Layer] Exception toggling layer:', e);
    }
  };
  </script>
`;

targetFiles.forEach(file => {
  if (!fs.existsSync(file)) return;
  let html = fs.readFileSync(file, 'utf8');
  if (!html.includes('3D HAZARD & MULTI-LAYER ENGINE BRIDGE')) {
    html = html.replace('</body>', layerEngineScript + '\n</body>');
    fs.writeFileSync(file, html, 'utf8');
    console.log('Bridge injected into:', path.basename(file), 'at', file);
  } else {
    console.log('Bridge already in:', path.basename(file));
  }
});
