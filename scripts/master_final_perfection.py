#!/usr/bin/env python3
import os, re, shutil

BASE_DIR = r"C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"
PRIMARY_FILE = os.path.join(BASE_DIR, "public", "index.html")

TARGETS = [
    os.path.join(BASE_DIR, "public", "index.html"),
    os.path.join(BASE_DIR, "public", "bhu_loka_cyber_dashboard.html"),
    os.path.join(BASE_DIR, "bhu_loka_cyber_dashboard.html"),
]

with open(PRIMARY_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add cache-busting meta tags in <head>
cache_meta = """  <!-- Cache Busting Headers -->
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
"""
if '<meta http-equiv="Cache-Control"' not in html:
    html = html.replace('<head>', '<head>\n' + cache_meta, 1)

# 2. Fix the extra </div> in header right section
# Locate:
#   <input id="global-location-search" ...>
# </div>
# \s*</div>\s*</div>\s*</header>
pattern_header_close = r'(<input id="global-location-search"[^>]*>\s*</div>)\s*</div>\s*</div>\s*</header>'
replacement_header_close = r'\1\n    </div>\n  </header>'
html = re.sub(pattern_header_close, replacement_header_close, html)

# Also check for any loose </div></div></header>
html = re.sub(r'(\s*</div>\s*)</div>\s*</div>\s*</header>', r'\1</div>\n  </header>', html)

# 3. Clean up the close button on #holo-live-tracker-hud
# Ensure there is only ONE clean close button:
hud_clean = """          <div id="holo-live-tracker-hud"
            class="hidden absolute top-12 right-3 z-20 bg-[#060a12]/95 backdrop-blur-md border border-cyan-500/40 rounded-xl p-3 shadow-[0_10px_30px_rgba(0,0,0,0.85)] w-72 text-[10.5px] font-mono select-none">
            <button class="hud-close-btn" aria-label="Close GPS Stream HUD" onclick="document.getElementById('holo-live-tracker-hud').classList.add('hidden')">&times;</button>
            <div class="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <span class="text-emerald-300 font-bold uppercase tracking-wider text-[10px]">Real-Time GPS Stream</span>
              </div>
              <span id="holo-track-rate"
                class="px-1.5 py-0.2 rounded text-[9px] bg-cyan-950 text-cyan-300 border border-cyan-500/30">1 Hz
                FIX</span>
            </div>"""

html = re.sub(
    r'<div id="holo-live-tracker-hud"[^>]*>.*?<div class="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">.*?<span id="holo-track-rate"[^>]*>1 Hz\s*FIX</span>\s*</div>',
    hud_clean,
    html,
    flags=re.DOTALL
)

# 4. Write to ALL target files
for target in TARGETS:
    with open(target, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Updated {os.path.basename(target)}: {len(html):,} bytes")

print("All targets written successfully.")
