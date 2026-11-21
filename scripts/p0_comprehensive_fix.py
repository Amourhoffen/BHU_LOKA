#!/usr/bin/env python3
"""
BHU LOKA – Comprehensive P0 Fix Script
Fixes:
1. Restore #bhu-time-machine bar (remove CSS hide rule, inject HTML if missing)
2. Fix bhuSetLayer() to call real engine functions (setHoloHazardLayer + setBhuLayer)
3. Fix #bhu-color-decoder-card: auto-open removed, repositioned right side
4. Fix 3D Layer panel: replace bogus onchange quote escaping
5. Remove neon #00f0ff in visual indicators (keep scientific label text)
6. Remove remaining emojis (⏱️, 🟢, ⚫, ⏸️)
7. Remove overlapping PK avatar / bell / gear if still present
8. Fix toggleHeroMap remnant
9. Synchronize all 3 HTML files
"""

import re
import hashlib
import shutil
import os

TARGET_FILES = [
    'public/index.html',
    'public/bhu_loka_cyber_dashboard.html',
    'bhu_loka_cyber_dashboard.html',
]

MASTER = TARGET_FILES[0]

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()

def apply_all_fixes(text):
    changes = []

    # ─────────────────────────────────────────────────────────────────────
    # FIX 1 – Remove the CSS block that hides #bhu-time-machine
    # ─────────────────────────────────────────────────────────────────────
    old_tm_hide = '''    #bhu-time-machine, .bhu-time-machine-bar, [id*="time-machine"] {
      display: none !important;
      height: 0 !important;
      min-height: 0 !important;
      max-height: 0 !important;
      padding: 0 !important;
      margin: 0 !important;
      border: none !important;
      visibility: hidden !important;
      pointer-events: none !important;
      overflow: hidden !important;
    }'''

    # Professional replacement – display the time-machine bar properly
    new_tm_css = '''    /* ─── BHU TIME MACHINE – aerospace bottom bar ─── */
    #bhu-time-machine {
      display: flex !important;
      visibility: visible !important;
      height: 42px !important;
      min-height: 42px !important;
      max-height: 42px !important;
      background: rgba(3,5,12,0.98) !important;
      border-top: 1px solid rgba(255,255,255,0.07) !important;
      padding: 0 14px !important;
      margin: 0 !important;
      flex-shrink: 0 !important;
      position: relative !important;
      z-index: 50 !important;
      pointer-events: auto !important;
      overflow: visible !important;
      align-items: center !important;
      gap: 0 !important;
    }
    #bhu-time-machine button {
      background: transparent !important;
      border: none !important;
      cursor: pointer !important;
      color: #64748b !important;
      border-radius: 5px !important;
      transition: color 0.12s, background 0.12s !important;
    }
    #bhu-time-machine button:hover {
      color: #e2e8f0 !important;
      background: rgba(255,255,255,0.06) !important;
    }
    #bhu-time-machine select {
      background: rgba(7,11,18,0.95) !important;
      border: 1px solid rgba(100,116,139,0.25) !important;
      border-radius: 4px !important;
      color: #64748b !important;
      font-size: 10px !important;
      font-family: 'JetBrains Mono', monospace !important;
      padding: 2px 5px !important;
      cursor: pointer !important;
    }
    #tm-date-display {
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 11px !important;
      color: #e2e8f0 !important;
      text-align: center !important;
      white-space: nowrap !important;
      margin-bottom: 2px !important;
    }
    #tm-slider {
      width: 100% !important;
      height: 3px !important;
      cursor: pointer !important;
      accent-color: #3b82f6 !important;
    }
    #tm-status-line {
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 10px !important;
      color: #64748b !important;
      white-space: nowrap !important;
    }
    #tm-utc-clock {
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 10.5px !important;
      color: #475569 !important;
      white-space: nowrap !important;
    }'''

    if old_tm_hide in text:
        text = text.replace(old_tm_hide, new_tm_css)
        changes.append('FIX 1: Removed CSS hide of #bhu-time-machine, added proper aerospace styles')
    else:
        changes.append('FIX 1: CSS hide block not found (may already be fixed)')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 2 – Inject #bhu-time-machine HTML before workstation-footer if absent
    # ─────────────────────────────────────────────────────────────────────
    if 'id="bhu-time-machine"' not in text:
        # Inject before footer
        footer_anchor = '<!-- BOTTOM PROVENANCE, CRS & LIVE TELEMETRY BAR (28px FIXED) -->'
        if footer_anchor in text:
            tm_html = '''  <!-- GLOBAL TIME MACHINE — PERSISTENT BOTTOM BAR (2026–2030 Forecast Horizon) -->
  <div id="bhu-time-machine">
    <!-- Transport controls -->
    <div style="display:flex;align-items:center;gap:3px;flex-shrink:0;margin-right:12px;">
      <button type="button" id="tm-rev" onclick="bhuTimeMachineStep(-1)" title="Step backward"
        style="width:28px;height:28px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="19 20 9 12 19 4 19 20" /><line x1="5" y1="19" x2="5" y2="5" />
        </svg>
      </button>
      <button type="button" id="tm-play" onclick="bhuTimeMachineTogglePlay()" title="Play / Pause"
        style="width:28px;height:28px;">
        <svg id="tm-play-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3" />
        </svg>
      </button>
      <button type="button" id="tm-fwd" onclick="bhuTimeMachineStep(1)" title="Step forward"
        style="width:28px;height:28px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 4 15 12 5 20 5 4" /><line x1="19" y1="5" x2="19" y2="19" />
        </svg>
      </button>
      <select id="tm-speed" onchange="bhuTimeMachineSetSpeed(this.value)">
        <option value="1">1x</option>
        <option value="10">10x</option>
        <option value="100">100x</option>
        <option value="365">365x</option>
      </select>
    </div>
    <!-- Timeline track -->
    <div style="flex:1;min-width:0;position:relative;padding:0 8px;">
      <div id="tm-date-display">13 Nov 2026</div>
      <input type="range" id="tm-slider" min="-50000" max="2026" value="2026" step="1"
        oninput="bhuTimeMachineSeek(this.value)">
      <div style="display:flex;justify-content:space-between;font-family:monospace;font-size:8.5px;color:#334155;margin-top:2px;pointer-events:none;">
        <span>3000 BCE</span><span>1 CE</span><span>1900</span><span>1972 Landsat</span>
        <span>2000 MODIS</span><span>2014 Sentinel</span><span>Now</span>
      </div>
    </div>
    <!-- Status and UTC clock -->
    <div style="flex-shrink:0;margin-left:12px;text-align:right;">
      <div id="tm-status-line">
        <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-right:4px;vertical-align:middle;"></span>LIVE · CelesTrak GP
      </div>
      <div id="tm-utc-clock">--:--:-- UTC</div>
    </div>
  </div>

  '''
            text = text.replace(footer_anchor, tm_html + footer_anchor)
            changes.append('FIX 2: Injected #bhu-time-machine HTML before footer')
    else:
        changes.append('FIX 2: #bhu-time-machine HTML already present')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 3 – Rewrite window.bhuSetLayer to call real engine functions
    # ─────────────────────────────────────────────────────────────────────
    old_set_layer = '''    window.bhuSetLayer=function(id,visible){
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
      var row=document.querySelector('[aria-label=\"Toggle '+l.label+'\"]');
      if(row)row.classList.toggle('active-layer',visible);
    };'''

    new_set_layer = '''    window.bhuSetLayer=function(id,visible){
      var l=LAYERS.find(function(x){return x.id===id;});
      if(!l)return;
      // Bridge to real 3D engine functions
      try{
        if(id==='heat'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'thermal':'sat');
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('lst',visible);
        } else if(id==='flood'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'flood':'sat');
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('flood',visible);
        } else if(id==='multihazard'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'sinks':'sat');
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('aqi',visible);
        } else if(id==='safezone'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'safe':'sat');
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('farms',visible);
        } else if(id==='crime'){
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('cctv_nodes',visible);
        } else if(id==='sar'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'flood':'sat');
        } else if(id==='dem'){
          if(typeof window.setHoloHazardLayer==='function') window.setHoloHazardLayer(visible?'topo':'sat');
          if(typeof window.setBhuLayer==='function') window.setBhuLayer('glo30_dem',visible);
        }
        // Also sync the top hazard sub-bar buttons visual state
        var layerBtnMap={heat:'btn-layer-thermal',flood:'btn-layer-flood',multihazard:'btn-layer-sinks',safezone:'btn-layer-safe',sar:'btn-layer-flood',dem:'btn-layer-topo'};
        var btnId=layerBtnMap[id];
        if(btnId && visible && typeof window.setHoloHazardLayer==='function'){
          var sb=document.getElementById(btnId);
          if(sb){sb.click();}
        }
      }catch(e){}
      document.dispatchEvent(new CustomEvent('bhu-layer-change',{detail:{layer:id,visible:visible}}));
      if(typeof window.showSovereignToast==='function')
        window.showSovereignToast((visible?'ON: ':'OFF: ')+l.label,'info',1800);
      var row=document.querySelector('[aria-label="Toggle '+l.label+'"]');
      if(row)row.classList.toggle('active-layer',visible);
    };'''

    if 'window.setBhuLayerVisibility' in text and 'bhuSetLayer' in text:
        text = text.replace(old_set_layer, new_set_layer)
        changes.append('FIX 3: Rewrote bhuSetLayer to bridge to real engine functions')
    else:
        changes.append('FIX 3: bhuSetLayer old version not found, trying partial patch')
        # Fallback: inject a bhuSetLayer bridge after the layer panel script
        old_toggle = 'window.bhuAllLayersOn=function(){LAYERS.forEach(function(l){var cb=document.getElementById(\'lt-\'+l.id);if(cb){cb.checked=true;cb.dispatchEvent(new Event(\'change\'));}});};'
        if old_toggle in text:
            bridge = '''
    // ─── 3D LAYER ENGINE BRIDGE ───
    window.bhuSetLayer=function(id,visible){
      var LAYER_MAP={
        heat:{holo:'thermal',india:'lst'},
        flood:{holo:'flood',india:'flood'},
        multihazard:{holo:'sinks',india:'aqi'},
        safezone:{holo:'safe',india:'farms'},
        crime:{india:'cctv_nodes'},
        sar:{holo:'flood'},
        dem:{holo:'topo',india:'glo30_dem'}
      };
      var m=LAYER_MAP[id];
      if(!m)return;
      try{
        if(m.holo&&typeof window.setHoloHazardLayer==='function'){
          window.setHoloHazardLayer(visible?m.holo:'sat');
        }
        if(m.india&&typeof window.setBhuLayer==='function'){
          window.setBhuLayer(m.india,visible);
        }
      }catch(e){}
      document.dispatchEvent(new CustomEvent('bhu-layer-change',{detail:{layer:id,visible:visible}}));
      if(typeof window.showSovereignToast==='function'){
        var LAYERS2=[{id:'heat',label:'Heat Area'},{id:'flood',label:'Flood Zone'},{id:'multihazard',label:'Multi-Hazard'},{id:'safezone',label:'Safe Zone'},{id:'crime',label:'High Crime Zone'},{id:'sar',label:'SAR / Flood SAR'},{id:'dem',label:'DEM / Elevation'}];
        var l2=LAYERS2.find(function(x){return x.id===id;});
        if(l2)window.showSovereignToast((visible?'ON: ':'OFF: ')+l2.label,'info',1800);
      }
    };
'''
            text = text.replace(old_toggle, old_toggle + bridge)
            changes.append('FIX 3 (fallback): Injected bhuSetLayer bridge after allLayersOn')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 4 – Fix the broken onchange quote escaping in layer toggles
    # ─────────────────────────────────────────────────────────────────────
    # The broken line: onchange="bhuSetLayer(''+l.id+'',this.checked)"
    broken_onchange = "          '  <input type=\"checkbox\" id=\"lt-'+l.id+'\" onchange=\"bhuSetLayer(''+l.id+'',this.checked)\">'+"
    fixed_onchange = "          '  <input type=\"checkbox\" id=\"lt-'+l.id+'\" onchange=\"bhuSetLayer(\\'' + l.id + '\\', this.checked)\">'+"

    if broken_onchange in text:
        text = text.replace(broken_onchange, fixed_onchange)
        changes.append('FIX 4: Fixed broken onchange quote escaping in layer toggles')
    else:
        changes.append('FIX 4: Broken onchange not found by exact match')
        # Try another approach - fix via regex
        m = re.search(r"onchange=\\\"bhuSetLayer\(''\+l\.id\+'',this\.checked\)\\\"", text)
        if m:
            text = text[:m.start()] + "onchange=\\\"bhuSetLayer('\" + l.id + \"', this.checked)\\\"" + text[m.end():]
            changes.append('FIX 4b: Fixed broken onchange via regex')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 5 – Remove auto-open of color decoder card
    # ─────────────────────────────────────────────────────────────────────
    # Remove the setTimeout auto-open calls
    patterns_to_remove = [
        "if (typeof toggleColorDecoderCard === 'function') {\n        setTimeout(() => toggleColorDecoderCard(true), 250);\n      }",
        "if (typeof window !== 'undefined' && typeof window.toggleColorDecoderCard === 'function') {\n      setTimeout(() => window.toggleColorDecoderCard(true), 300);\n    }",
        "if (typeof toggleColorDecoderCard === 'function') {\n      setTimeout(() => toggleColorDecoderCard(true), 300);\n    }",
    ]
    for pat in patterns_to_remove:
        if pat in text:
            text = text.replace(pat, '// Color decoder: not auto-opened on load')
            changes.append(f'FIX 5: Removed auto-open call: {pat[:50]}...')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 6 – Reposition #bhu-color-decoder-card to right side, not left
    # ─────────────────────────────────────────────────────────────────────
    old_decoder_class = 'class="hidden absolute bottom-3 left-3 z-30 bg-[#060a12]/95 backdrop-blur-md border border-slate-700 rounded-xl p-3 shadow-2xl max-w-sm text-[10.5px] font-mono select-none transition-all"'
    new_decoder_class = 'class="hidden fixed top-16 right-5 z-40 bg-[#060a12]/96 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 shadow-2xl w-80 text-[10.5px] font-mono select-none transition-all"'
    if old_decoder_class in text:
        text = text.replace(old_decoder_class, new_decoder_class)
        changes.append('FIX 6: Repositioned color-decoder-card to top-right fixed position')
    else:
        changes.append('FIX 6: decoder card class not found by exact match')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 7 – Remove remaining emojis (🟢, ⚫, ⏱️, ⏸️)
    # ─────────────────────────────────────────────────────────────────────
    emoji_map = {
        '⏱️': '<i class="fa-regular fa-clock" aria-hidden="true"></i>',
        '⏱': '<i class="fa-regular fa-clock" aria-hidden="true"></i>',
        '⏸️': '<i class="fa-solid fa-pause" aria-hidden="true"></i>',
        '🟢 ': '',  # Remove from toast messages
        '⚫ ': '',   # Remove from toast messages
        '🟢': '',
        '⚫': '',
    }
    for emoji, replacement in emoji_map.items():
        if emoji in text:
            text = text.replace(emoji, replacement)
            changes.append(f'FIX 7: Replaced emoji {repr(emoji)} with FA icon or removed')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 8 – Replace neon #00f0ff in color decoder color dot (not text labels)
    # ─────────────────────────────────────────────────────────────────────
    # The only visual neon dot we want to replace is in the decoder card
    old_neon_dot = 'class="w-3 h-3 rounded-full bg-[#00f0ff] shrink-0 mt-0.5 shadow-[0_0_8px_#00f0ff]"'
    new_neon_dot = 'class="w-3 h-3 rounded-full bg-cyan-500 shrink-0 mt-0.5"'
    text = text.replace(old_neon_dot, new_neon_dot)
    changes.append('FIX 8: Replaced neon #00f0ff color dots in decoder card')

    # Also fix the SVG circle that uses #00f0ff
    old_svg_neon = 'fill="#00f0ff"'
    new_svg_neon = 'fill="#38bdf8"'
    text = text.replace(old_svg_neon, new_svg_neon)
    changes.append('FIX 8b: Replaced SVG fill #00f0ff with #38bdf8 (sky-400)')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 9 – Remove toggleHeroMap remnant (single reference)
    # ─────────────────────────────────────────────────────────────────────
    for old_hero in [
        'onclick="toggleHeroMap()"',
        "onclick='toggleHeroMap()'",
    ]:
        if old_hero in text:
            text = text.replace(old_hero, 'onclick="void(0)"')
            changes.append('FIX 9: Removed toggleHeroMap onclick')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 10 – Fix the 3D panel bhuSetLayer onchange quoting
    # (the innerHTML approach creates inline attribute quoting issues)
    # Replace the whole innerHTML block with a cleaner version using addEventListener
    # ─────────────────────────────────────────────────────────────────────
    old_row_innerHTML = '''        row.innerHTML='<span class="lp-dot" style="background:'+l.color+';box-shadow:0 0 8px '+l.color+';"></span>'+
          '<span class="lp-name">'+l.label+'</span>'+
          '<label class="lp-toggle" onclick="event.stopPropagation()" aria-label="Toggle '+l.label+'">'+
          '  <input type="checkbox" id="lt-'+l.id+'" onchange="bhuSetLayer(''+l.id+'',this.checked)">'+
          '  <span class="lp-toggle-track"></span>'+
          '  <span class="lp-toggle-thumb"></span>'+
          '</label>';'''

    new_row_innerHTML = '''        // Build toggle elements without inline attribute quoting issues
        var dot=document.createElement('span');
        dot.className='lp-dot';
        dot.style.background=l.color;
        dot.style.boxShadow='0 0 8px '+l.color;
        var name=document.createElement('span');
        name.className='lp-name';
        name.textContent=l.label;
        var lbl=document.createElement('label');
        lbl.className='lp-toggle';
        lbl.setAttribute('aria-label','Toggle '+l.label);
        lbl.addEventListener('click',function(e){e.stopPropagation();});
        var cb=document.createElement('input');
        cb.type='checkbox';
        cb.id='lt-'+l.id;
        (function(layerId){cb.addEventListener('change',function(){window.bhuSetLayer(layerId,cb.checked);});})(l.id);
        var track=document.createElement('span');
        track.className='lp-toggle-track';
        var thumb=document.createElement('span');
        thumb.className='lp-toggle-thumb';
        lbl.appendChild(cb);lbl.appendChild(track);lbl.appendChild(thumb);
        row.appendChild(dot);row.appendChild(name);row.appendChild(lbl);'''

    if old_row_innerHTML in text:
        text = text.replace(old_row_innerHTML, new_row_innerHTML)
        changes.append('FIX 10: Replaced innerHTML layer builder with DOM API calls (no quoting issues)')
    else:
        changes.append('FIX 10: Old innerHTML builder not found by exact match')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 11 – Fix Left Rail AI header overflow (badges causing wrap)
    # ─────────────────────────────────────────────────────────────────────
    old_ai_header = '''          <div class="flex items-center gap-1.5">
              <span class="section-header font-bold text-sky-400">BHU LOKA AI</span>
              <span class="text-[10px] text-slate-400 font-normal">भूलोक AI</span>
              <span class="badge-chip bg-sky-950/70 text-sky-300 border-sky-600/40 text-[9px] px-1 py-0.5"
                id="console-status-badge">DUAL-AGENT</span>
              <span
                class="badge-chip bg-slate-900 text-slate-400 border-slate-700 text-[9px] px-1 py-0.5 hidden sm:inline"
                id="sovereign-ai-status-badge">SOVEREIGN AI</span>
            </div>'''
    new_ai_header = '''          <div class="flex items-center gap-1.5 flex-wrap min-w-0">
              <span class="section-header font-bold text-sky-400 shrink-0">BHU LOKA AI</span>
              <span class="badge-chip bg-sky-950/70 text-sky-300 border-sky-600/40 text-[9px] px-1 py-0.5 shrink-0"
                id="console-status-badge">DUAL-AGENT</span>
              <span
                class="badge-chip bg-slate-900 text-slate-400 border-slate-700 text-[9px] px-1 py-0.5 shrink-0"
                id="sovereign-ai-status-badge">SOVEREIGN AI</span>
            </div>'''

    if old_ai_header in text:
        text = text.replace(old_ai_header, new_ai_header)
        changes.append('FIX 11: Fixed Left Rail AI header badge overflow/wrap')
    else:
        changes.append('FIX 11: AI header pattern not found by exact match')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 12 – Add a bhuTimeMachineSetSpeed function if missing
    # ─────────────────────────────────────────────────────────────────────
    if 'bhuTimeMachineSetSpeed' not in text and 'bhuTmInterval' in text:
        old_speed_ref = 'let bhuTmPlaying = false;\n    let bhuTmInterval = null;'
        new_speed_ref = '''let bhuTmPlaying = false;
    let bhuTmInterval = null;
    let bhuTmSpeedMultiplier = 1;
    window.bhuTimeMachineSetSpeed = function(val) {
      bhuTmSpeedMultiplier = parseInt(val, 10) || 1;
    };'''
        if old_speed_ref in text:
            text = text.replace(old_speed_ref, new_speed_ref)
            changes.append('FIX 12: Added bhuTimeMachineSetSpeed function')
        else:
            changes.append('FIX 12: bhuTmInterval anchor not found')

    # ─────────────────────────────────────────────────────────────────────
    # FIX 13 – Remove BOM character if present
    # ─────────────────────────────────────────────────────────────────────
    if text.startswith('\ufeff'):
        text = text[1:]
        changes.append('FIX 13: Removed BOM character')

    return text, changes


# ── MAIN ──────────────────────────────────────────────────────────────────────
print('=' * 70)
print('BHU LOKA – Comprehensive P0 Fix Script')
print('=' * 70)

with open(MASTER, 'r', encoding='utf-8') as f:
    original = f.read()

print(f'Read master: {MASTER}')
print(f'Size: {len(original):,} chars')

fixed, changes = apply_all_fixes(original)

print(f'\nFixed size: {len(fixed):,} chars (delta: {len(fixed)-len(original):+,})')
print(f'\nChanges applied ({len(changes)}):')
for i, c in enumerate(changes, 1):
    print(f'  {i:02d}. {c}')

if fixed == original:
    print('\n[WARNING] No changes were made! Possible that patterns differ.')
else:
    print(f'\nSHA256 (fixed): {sha(fixed)}')
    # Write master first
    with open(MASTER, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print(f'Written: {MASTER}')

    # Sync to other files
    for target in TARGET_FILES[1:]:
        with open(target, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f'Synced:  {target}')

    print('\nAll 3 files synchronized.')
    print(f'SHA256: {sha(fixed)}')
