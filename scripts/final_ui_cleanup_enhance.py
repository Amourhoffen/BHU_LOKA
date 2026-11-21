#!/usr/bin/env python3
"""
BHU LOKA – Final UI Cleanup & 3D Layer Enhancement
===================================================
1. Remove bell / gear / PK avatar buttons from top-right header
2. Remove any remaining bhu-nav-chevron HTML buttons
3. Remove the stale COMMANDS floating dock comment block
4. Replace old 3D layer FAB+panel with the Apple/ISO enhanced version
5. Sync changes to both public/index.html and bhu_loka_cyber_dashboard.html
"""

import re, os, sys, shutil

BASE = r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"
FILES = [
    os.path.join(BASE, "public", "index.html"),
    os.path.join(BASE, "bhu_loka_cyber_dashboard.html"),
]

# ─────────────────────────────────────────────────────────
# CSS to inject before </head>
# ─────────────────────────────────────────────────────────
LAYER_CSS = """
  <!-- ═══ BHU LOKA 3D HAZARD LAYER SYSTEM – Apple/ISO Design ═══ -->
  <style id="bhu-layer-system-css">
    #bhu-3d-fab {
      position: fixed; bottom: 68px; right: 20px; z-index: 2200;
      display: flex; align-items: center; gap: 7px;
      padding: 0 18px 0 14px; height: 40px; border-radius: 20px;
      background: linear-gradient(135deg,rgba(2,132,199,.95) 0%,rgba(6,182,212,.95) 50%,rgba(16,185,129,.9) 100%);
      color: #fff; font-family: 'Space Grotesk',system-ui,sans-serif;
      font-weight: 700; font-size: 11.5px; letter-spacing: .06em;
      border: 1.5px solid rgba(255,255,255,.35);
      box-shadow: 0 0 24px rgba(6,182,212,.55),0 4px 16px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.3);
      cursor: pointer; user-select: none;
      transition: transform .18s cubic-bezier(.34,1.56,.64,1),box-shadow .18s ease;
      backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    }
    #bhu-3d-fab:hover { transform: scale(1.06) translateY(-1px); box-shadow: 0 0 32px rgba(6,182,212,.8),0 8px 24px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.3); }
    #bhu-3d-fab:active { transform: scale(.97); }
    #bhu-3d-fab .fab-icon { width:18px;height:18px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.18);border-radius:6px;flex-shrink:0; }
    #bhu-3d-fab .fab-dot { width:7px;height:7px;border-radius:50%;background:#fff;box-shadow:0 0 8px rgba(255,255,255,.9);flex-shrink:0;animation:bhu-fab-pulse 2.4s ease-in-out infinite; }
    @keyframes bhu-fab-pulse { 0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.82)} }

    #bhu-3d-panel {
      position: fixed; bottom: 118px; right: 20px; z-index: 2199;
      width: 234px;
      background: rgba(5,9,20,.92);
      backdrop-filter: blur(28px) saturate(180%); -webkit-backdrop-filter: blur(28px) saturate(180%);
      border: 1px solid rgba(255,255,255,.12); border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,.8),0 0 0 .5px rgba(255,255,255,.05),inset 0 1px 0 rgba(255,255,255,.07);
      overflow: hidden; transform-origin: bottom right;
      transition: transform .28s cubic-bezier(.34,1.56,.64,1),opacity .22s ease;
    }
    #bhu-3d-panel.lp-hidden { transform: scale(.85) translateY(10px); opacity: 0; pointer-events: none; }
    .lp-header { display:flex;align-items:center;justify-content:space-between;padding:12px 14px 9px;border-bottom:1px solid rgba(255,255,255,.07); }
    .lp-title { font-family:'Space Grotesk',system-ui,sans-serif;font-size:11px;font-weight:700;letter-spacing:.08em;color:rgba(255,255,255,.9);text-transform:uppercase;display:flex;align-items:center;gap:7px; }
    .lp-title-icon { width:20px;height:20px;border-radius:6px;background:linear-gradient(135deg,rgba(6,182,212,.4),rgba(16,185,129,.3));display:flex;align-items:center;justify-content:center; }
    .lp-close { width:22px;height:22px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6);font-size:14px;display:flex;align-items:center;justify-content:center;cursor:pointer;line-height:1;transition:background .15s,color .15s; }
    .lp-close:hover { background:rgba(239,68,68,.3);color:#fff;border-color:rgba(239,68,68,.5); }
    .lp-body { padding:10px 12px 12px;display:flex;flex-direction:column;gap:5px; }
    .lp-row { display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:10px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.055);cursor:pointer;transition:background .14s,border-color .14s,transform .1s;user-select:none; }
    .lp-row:hover { background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.12);transform:translateX(2px); }
    .lp-row.active-layer { background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.14); }
    .lp-dot { width:10px;height:10px;border-radius:50%;flex-shrink:0; }
    .lp-name { flex:1;font-family:'Space Grotesk',system-ui,sans-serif;font-size:11.5px;font-weight:500;color:rgba(255,255,255,.82);letter-spacing:.01em; }
    .lp-toggle { position:relative;width:36px;height:20px;flex-shrink:0; }
    .lp-toggle input { opacity:0;width:0;height:0;position:absolute; }
    .lp-toggle-track { position:absolute;inset:0;border-radius:10px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.1);transition:background .22s,border-color .22s;cursor:pointer; }
    .lp-toggle input:checked + .lp-toggle-track { background:rgba(16,185,129,.85);border-color:rgba(16,185,129,.6);box-shadow:0 0 10px rgba(16,185,129,.4); }
    .lp-toggle-thumb { position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:#fff;transition:left .22s cubic-bezier(.34,1.56,.64,1);pointer-events:none;box-shadow:0 1px 4px rgba(0,0,0,.5); }
    .lp-toggle input:checked ~ .lp-toggle-thumb { left:18px; }
    .lp-footer { display:flex;gap:8px;padding:0 12px 12px; }
    .lp-btn { flex:1;height:30px;border-radius:8px;font-family:'Space Grotesk',system-ui,sans-serif;font-size:10.5px;font-weight:700;letter-spacing:.06em;cursor:pointer;border:none;transition:opacity .15s,transform .12s;display:flex;align-items:center;justify-content:center;gap:4px; }
    .lp-btn:hover { opacity:.85;transform:scale(1.02); }
    .lp-btn:active { transform:scale(.97); }
    .lp-btn-enable { background:linear-gradient(135deg,rgba(2,132,199,.9),rgba(16,185,129,.85));color:#fff; }
    .lp-btn-clear { background:rgba(255,255,255,.08);color:rgba(255,255,255,.65);border:1px solid rgba(255,255,255,.1); }
  </style>
"""

# ─────────────────────────────────────────────────────────
# HTML+JS to inject before </body>
# ─────────────────────────────────────────────────────────
LAYER_HTML = """
  <!-- ═══ BHU LOKA 3D HAZARD FAB + PANEL ═══ -->
  <button id="bhu-3d-fab" aria-label="Toggle 3D Hazard Layers" onclick="bhuToggle3D()" title="3D Hazard Layer Filters">
    <span class="fab-icon"><i class="fa-solid fa-layer-group" style="font-size:11px;"></i></span>
    <span>3D LAYERS</span>
    <span class="fab-dot"></span>
  </button>

  <div id="bhu-3d-panel" class="lp-hidden" role="dialog" aria-label="3D Hazard Layers" aria-modal="false">
    <div class="lp-header">
      <span class="lp-title">
        <span class="lp-title-icon"><i class="fa-solid fa-map" style="color:rgba(6,182,212,.9);font-size:9px;"></i></span>
        3D LAYERS
      </span>
      <button class="lp-close" onclick="bhuToggle3D()" aria-label="Close">&times;</button>
    </div>
    <div class="lp-body" id="bhu-3d-body"></div>
    <div class="lp-footer">
      <button class="lp-btn lp-btn-enable" onclick="bhuAllLayersOn()" aria-label="Enable all layers">
        <i class="fa-solid fa-eye" style="font-size:10px;"></i> ALL ON
      </button>
      <button class="lp-btn lp-btn-clear" onclick="bhuAllLayersOff()" aria-label="Clear all layers">
        <i class="fa-solid fa-eye-slash" style="font-size:10px;"></i> CLEAR
      </button>
    </div>
  </div>

  <script>
  (function(){
    'use strict';
    var LAYERS=[
      {id:'heat',       label:'Heat Area',       color:'#f97316', key:'heatMesh'},
      {id:'flood',      label:'Flood Zone',      color:'#38bdf8', key:'terrainFloodMesh'},
      {id:'multihazard',label:'Multi-Hazard',    color:'#a855f7', key:'multiHazardGroup'},
      {id:'safezone',   label:'Safe Zone',       color:'#10b981', key:'safeZoneGroup'},
      {id:'crime',      label:'High Crime Zone', color:'#ef4444', key:'crimeZoneGroup'},
      {id:'sar',        label:'SAR / Flood SAR', color:'#facc15', key:'indiaLstGroup'},
      {id:'dem',        label:'DEM / Elevation', color:'#94a3b8', key:'demGroup'}
    ];
    var open=false,built=false;

    window.bhuToggle3D=function(){
      var p=document.getElementById('bhu-3d-panel');
      if(!p)return;
      open=!open;
      if(open){p.classList.remove('lp-hidden');if(!built)_build();}
      else p.classList.add('lp-hidden');
    };

    function _build(){
      built=true;
      var body=document.getElementById('bhu-3d-body');
      if(!body)return;
      LAYERS.forEach(function(l){
        var row=document.createElement('div');
        row.className='lp-row';
        row.setAttribute('tabindex','0');
        row.setAttribute('role','button');
        row.setAttribute('aria-label','Toggle '+l.label);
        row.innerHTML='<span class="lp-dot" style="background:'+l.color+';box-shadow:0 0 8px '+l.color+';"></span>'+
          '<span class="lp-name">'+l.label+'</span>'+
          '<label class="lp-toggle" onclick="event.stopPropagation()" aria-label="Toggle '+l.label+'">'+
          '  <input type="checkbox" id="lt-'+l.id+'" onchange="bhuSetLayer(\''+l.id+'\',this.checked)">'+
          '  <span class="lp-toggle-track"></span>'+
          '  <span class="lp-toggle-thumb"></span>'+
          '</label>';
        row.onclick=function(){var cb=document.getElementById('lt-'+l.id);if(cb){cb.checked=!cb.checked;cb.dispatchEvent(new Event('change'));}};
        row.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();row.click();}};
        body.appendChild(row);
      });
    }

    window.bhuSetLayer=function(id,visible){
      var l=LAYERS.find(function(x){return x.id===id;});
      if(!l)return;
      try{
        var obj=window[l.key]||(window.scene&&window.scene.getObjectByName&&window.scene.getObjectByName(l.key));
        if(obj)obj.visible=visible;
      }catch(e){}
      if(typeof window.setBhuLayerVisibility==='function')window.setBhuLayerVisibility(id,visible);
      document.dispatchEvent(new CustomEvent('bhu-layer-change',{detail:{layer:id,visible:visible}}));
      if(typeof window.showSovereignToast==='function')
        window.showSovereignToast((visible?'🟢 ':'⚫ ')+l.label+' '+(visible?'ON':'OFF'),'info',1800);
      var row=document.querySelector('[aria-label="Toggle '+l.label+'"]');
      if(row)row.classList.toggle('active-layer',visible);
    };

    window.bhuAllLayersOn=function(){LAYERS.forEach(function(l){var cb=document.getElementById('lt-'+l.id);if(cb){cb.checked=true;cb.dispatchEvent(new Event('change'));}});};
    window.bhuAllLayersOff=function(){LAYERS.forEach(function(l){var cb=document.getElementById('lt-'+l.id);if(cb){cb.checked=false;cb.dispatchEvent(new Event('change'));}});};

    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&open)window.bhuToggle3D();});
  })();
  </script>
"""

def remove_element(html, pattern, flags=re.DOTALL | re.IGNORECASE):
    """Remove a matched block; return cleaned HTML + count of replacements."""
    result, n = re.subn(pattern, '', html, flags=flags)
    return result, n

def process_file(path):
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        return

    # Backup
    shutil.copy2(path, path + ".bak")

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    original_len = len(html)

    # ── 1. Remove bell button (btn-api-chip) ──────────────────────
    html, n1 = remove_element(html,
        r'<button[^>]+id=["\']btn-api-chip["\'][^>]*>.*?</button>')
    print(f"  Bell btn removed: {n1} match(es)")

    # ── 2. Remove gear/settings button (toggleHeroMap) ────────────
    html, n2 = remove_element(html,
        r'<button[^>]+onclick=["\']toggleHeroMap\(\)["\'][^>]*>.*?</button>')
    print(f"  Gear btn removed: {n2} match(es)")

    # ── 3. Remove PK avatar block ──────────────────────────────────
    # Matches: <div class="flex items-center gap-1.5 pl-2 border-l..."> ... </div></div>
    html, n3 = remove_element(html,
        r'<div\s+class=["\']flex items-center gap-1\.5 pl-2 border-l[^"\']*["\']>\s*<div[^>]*>.*?PK.*?</div>\s*</div>\s*(?:<div[^>]*>.*?Prince Kumar.*?</div>\s*</div>)?')
    print(f"  PK avatar removed: {n3} match(es)")

    # ── 4. Remove any bhu-nav-chevron HTML buttons ─────────────────
    html, n4 = remove_element(html,
        r'<button[^>]+class=["\'][^"\']*bhu-nav-chevron[^"\']*["\'][^>]*>.*?</button>')
    print(f"  Chevron btns removed: {n4} match(es)")

    # ── 5. Remove old COMMANDS dock comment block ──────────────────
    html, n5 = remove_element(html,
        r'<!--\s*=+\s*SOVEREIGN FLOATING WORKSPACE COMMAND DOCK.*?-->\s*\n?\s*\n?')
    print(f"  COMMANDS dock comment removed: {n5} match(es)")

    # ── 6. Remove old 3D layer button (btn-3d-layer-toggle) ────────
    html, n6 = remove_element(html,
        r'<!--\s*──\s*(?:ENHANCED|BHU LOKA) [^-]*(?:3D|LAYER)[^-]*──\s*-->\s*' +
        r'<button[^>]+id=["\']btn-3d-layer-toggle["\'][^>]*>.*?</button>')
    if n6 == 0:
        html, n6 = remove_element(html,
            r'<button[^>]+id=["\']btn-3d-layer-toggle["\'][^>]*>.*?</button>')
    print(f"  Old 3D FAB btn removed: {n6} match(es)")

    # ── 7. Remove old bhu-3d-layer-panel ──────────────────────────
    html, n7 = remove_element(html,
        r'<div[^>]+id=["\']bhu-3d-layer-panel["\'][^>]*>.*?(?=\s*<!--\s*═|</body>)',
        flags=re.DOTALL)
    if n7 == 0:
        html, n7 = remove_element(html,
            r'<div[^>]+id=["\']bhu-3d-layer-panel["\'][^>]*>.*?</div>\s*</div>\s*</div>')
    print(f"  Old 3D panel removed: {n7} match(es)")

    # ── 8. Remove duplicate layer system CSS if already injected ──
    html, _ = remove_element(html,
        r'<style id=["\']bhu-layer-system-css["\']>.*?</style>')
    # Remove duplicate script blocks
    html, _ = remove_element(html,
        r'<script>\s*\(function\(\)\{\s*\'use strict\';\s*var LAYERS=\[.*?\}\)\(\);\s*</script>',
        flags=re.DOTALL)

    # ── 9. Inject CSS before </head> ──────────────────────────────
    if '</head>' in html:
        html = html.replace('</head>', LAYER_CSS + '\n</head>', 1)
        print("  CSS injected before </head>")

    # ── 10. Inject HTML+JS before </body> ─────────────────────────
    if '</body>' in html:
        html = html.replace('</body>', LAYER_HTML + '\n</body>', 1)
        print("  HTML+JS injected before </body>")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    new_len = len(html)
    print(f"  Size: {original_len:,} → {new_len:,} bytes")
    print(f"  DONE: {os.path.basename(path)}\n")

if __name__ == '__main__':
    for fp in FILES:
        print(f"\nProcessing: {fp}")
        process_file(fp)
    print("All done. Ready for firebase deploy.")
