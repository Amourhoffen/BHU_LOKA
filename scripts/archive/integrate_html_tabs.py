import re
import os
import shutil

BASE_DIR = r"c:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक"

def update_html_files():
    html_files = [
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(BASE_DIR, "bhu_loka_cyber_dashboard.html")
    ]
    
    tab_html = '''              <button type="button" id="urban-tab-site-ai" class="us3-tab" onclick="switchUrbanTab('site-ai')" style="border-color:rgba(14,165,233,0.5);color:#38bdf8;background:rgba(14,165,233,0.08);">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                <span>🛰️ AI SITE ANALYTICS</span>
              </button>'''

    panel_html = '''          <div id="urban-site-ai-panel" style="flex:1 1 auto;min-height:0;display:none;flex-direction:column;background:#050811;overflow-y:auto;padding:12px;">
            <div id="urban-site-ai-panel-content" style="display:flex;flex-direction:column;gap:12px;width:100%;"></div>
          </div>'''

    for path in html_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add 5th tab if not present
        if 'id="urban-tab-site-ai"' not in content:
            target = '''              <button type="button" id="urban-tab-ml" class="us3-tab" onclick="switchUrbanTab('ml')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/></svg>
                <span>ML &amp; MODEL CARD</span>
              </button>'''
            replacement = target + "\n" + tab_html
            if target in content:
                content = content.replace(target, replacement)
                print(f"[OK] Added urban-tab-site-ai to {os.path.basename(path)}")
            else:
                print(f"[WARN] Target tab not found in {os.path.basename(path)}")

        # Add urban-site-ai-panel if not present
        if 'id="urban-site-ai-panel"' not in content:
            target_panel = '''          <div id="urban-ml-panel" style="flex:1 1 auto;min-height:0;display:none;flex-direction:column;background:#050811;">
            <div id="urban-ml-panel-content" style="display:flex;flex-direction:column;flex:1;min-height:0;overflow-y:auto;"></div>
          </div>'''
            replacement_panel = target_panel + "\n" + panel_html
            if target_panel in content:
                content = content.replace(target_panel, replacement_panel)
                print(f"[OK] Added urban-site-ai-panel to {os.path.basename(path)}")
            else:
                print(f"[WARN] Target panel not found in {os.path.basename(path)}")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

update_html_files()
