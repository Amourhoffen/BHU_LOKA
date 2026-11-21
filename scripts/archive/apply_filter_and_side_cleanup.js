const fs = require('fs');
const path = require('path');

const targetFiles = [
  path.join(__dirname, 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, 'public', 'index.html'),
  path.join(__dirname, 'index.html')
];

targetFiles.forEach(file => {
  if (!fs.existsSync(file)) return;
  let html = fs.readFileSync(file, 'utf8');

  // 1. RED: Remove the side-side chevron circle buttons (prev & next) completely
  html = html.replace(/\s*<button[^>]*class="[^"]*bhu-nav-chevron[^"]*"[\s\S]*?<\/button>/gi, '');
  // Also add CSS to ensure they never display
  if (!html.includes('.bhu-nav-chevron { display: none !important; }')) {
    html = html.replace('</style>', `\n    .bhu-nav-chevron { display: none !important; pointer-events: none !important; }\n  </style>`);
  }

  // 2. ENHANCE: Replace the black/invisible circular button (#btn-3d-layer-toggle)
  // with a prominent, high-tech, glowing labeled pill button that users can immediately see and use
  html = html.replace(/<button[^>]*id="btn-3d-layer-toggle"[\s\S]*?<\/button>/gi, '');

  const enhancedFabButton = `
  <!-- ── ENHANCED HIGH-VISIBILITY 3D HAZARD FILTERS BUTTON ── -->
  <button id="btn-3d-layer-toggle" type="button" onclick="toggleBhu3DLayerPanel()"
    style="position:fixed;bottom:54px;right:18px;z-index:2001;display:flex;align-items:center;gap:8px;padding:8px 16px;border-radius:9999px;background:linear-gradient(135deg,#0284c7,#06b6d4,#10b981);color:#ffffff;font-family:'Space Grotesk',system-ui,sans-serif;font-weight:700;font-size:12px;letter-spacing:0.04em;border:1.5px solid rgba(255,255,255,0.4);box-shadow:0 0 20px rgba(6,182,212,0.6),0 4px 12px rgba(0,0,0,0.6);cursor:pointer;transition:transform 0.15s,box-shadow 0.15s;user-select:none;"
    onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 0 28px rgba(6,182,212,0.85),0 6px 16px rgba(0,0,0,0.7)';"
    onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 0 20px rgba(6,182,212,0.6),0 4px 12px rgba(0,0,0,0.6)';"
    title="Toggle 3D Terrain Hazard Layers &amp; Colormaps">
    <i class="fa-solid fa-layer-group" style="font-size:14px;"></i>
    <span>3D HAZARD FILTERS</span>
    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#ffffff;box-shadow:0 0 8px #ffffff;"></span>
  </button>
  `;

  // 3. ENHANCE: Make the 3D Layer panel directly repaint the 3D terrain mesh in real time!
  const enhancedLayerBridge = `
  <script>
  /* ── 3D TERRAIN LIVE REPAINT & FILTER BRIDGE ── */
  window.setBhuLayerVisibility = function(layerId, active) {
    try {
      // 1. Repaint 3D Hologram Terrain Mesh if in 3D Hologram / Site Analysis Crop mode
      if (typeof setHoloHazardLayer === 'function') {
        if (active) {
          switch (layerId) {
            case 'heat':
              setHoloHazardLayer('thermal'); // Repaints terrain in Red/Thermal LST
              break;
            case 'flood':
              setHoloHazardLayer('flood'); // Repaints terrain in Blue Water Inundation
              break;
            case 'multihazard':
              setHoloHazardLayer('drought'); // Repaints terrain in Orange Agricultural Stress
              break;
            case 'safe':
              setHoloHazardLayer('safe'); // Repaints terrain highlighting Green Safe Ridge >52m
              break;
            case 'crime':
              setHoloHazardLayer('sinks'); // Repaints terrain highlighting Purple Risk Sinks
              break;
            case 'sar':
              setHoloHazardLayer('flood'); // Repaints terrain in Cyan SAR Radar specularity
              break;
            case 'dem':
              setHoloHazardLayer('topo'); // Repaints terrain in Amber Topographic Contours
              break;
          }
        } else {
          // Revert to satellite or elevation view
          setHoloHazardLayer('topo');
        }
      }

      // 2. Also toggle 3D globe layers if in World or India mode
      switch (layerId) {
        case 'heat':
          if (typeof indiaLstGroup !== 'undefined' && indiaLstGroup) indiaLstGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] Heat Area: ' + (active ? 'ACTIVE (Thermal Infrared Red Mesh)' : 'DISABLED'), active ? 'warn' : 'info', 2200);
          }
          break;
        case 'flood':
          if (typeof indiaFloodOverlayGroup !== 'undefined' && indiaFloodOverlayGroup) indiaFloodOverlayGroup.visible = active;
          if (typeof terrainFloodMesh !== 'undefined' && terrainFloodMesh) terrainFloodMesh.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] Flood Zone: ' + (active ? 'ACTIVE (Sentinel-1 SAR Blue Inundation)' : 'DISABLED'), active ? 'info' : 'info', 2200);
          }
          break;
        case 'multihazard':
          if (typeof indiaDroughtGroup !== 'undefined' && indiaDroughtGroup) indiaDroughtGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] Multi-Hazard: ' + (active ? 'ACTIVE (Orange Compound Hazard Colormap)' : 'DISABLED'), active ? 'warn' : 'info', 2200);
          }
          break;
        case 'safe':
          if (typeof indiaLandCorridorsGroup !== 'undefined' && indiaLandCorridorsGroup) indiaLandCorridorsGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] Safe Zone: ' + (active ? 'ACTIVE (Emerald Green Safe Ground >52m)' : 'DISABLED'), active ? 'success' : 'info', 2200);
          }
          break;
        case 'crime':
          if (typeof indiaUrbanCctvGroup !== 'undefined' && indiaUrbanCctvGroup) indiaUrbanCctvGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] Security Grid: ' + (active ? 'ACTIVE (Purple Tactical Safety Pins)' : 'DISABLED'), active ? 'warn' : 'info', 2200);
          }
          break;
        case 'sar':
          if (typeof indiaWaterDynGroup !== 'undefined' && indiaWaterDynGroup) indiaWaterDynGroup.visible = active;
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] SAR Microwave: ' + (active ? 'ACTIVE (Cyan Microwave Loss Specularity)' : 'DISABLED'), active ? 'info' : 'info', 2200);
          }
          break;
        case 'dem':
          if (typeof showSovereignToast === 'function') {
            showSovereignToast('[3D FILTER] 3D DEM: ' + (active ? 'ACTIVE (Copernicus 30m Elevation Topo)' : 'DISABLED'), active ? 'info' : 'info', 2200);
          }
          break;
      }
    } catch (err) {
      console.warn('Error in setBhuLayerVisibility:', err);
    }
  };
  </script>
  `;

  // Insert the enhanced FAB button before the layer panel
  if (html.includes('id="bhu-3d-layer-panel"')) {
    html = html.replace(/(<div id="bhu-3d-layer-panel")/i, enhancedFabButton + '\n  $1');
  } else {
    html = html.replace('</body>', enhancedFabButton + '\n</body>');
  }

  // Update or append the bridge
  if (html.includes('/* ── 3D TERRAIN LIVE REPAINT & FILTER BRIDGE ── */')) {
    html = html.replace(/<script>[\s\S]*?3D TERRAIN LIVE REPAINT & FILTER BRIDGE[\s\S]*?<\/script>/, enhancedLayerBridge);
  } else {
    html = html.replace('</body>', enhancedLayerBridge + '\n</body>');
  }

  fs.writeFileSync(file, html, 'utf8');
  console.log('Processed:', path.basename(file), 'at', file);
});

console.log('ALL FILES PROCESSED SUCCESSFULLY!');
