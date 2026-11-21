import os
import re

JS_PATH = r"c:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक\Assets\vendor\bhu_loka_urban_studio.js"

with open(JS_PATH, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update switchTab to support 'site-ai'
old_switch = '''    switchTab(tab) {
      this.activeTab = tab;
      const p2d = document.getElementById('urban-2d-panel');
      const p3d = document.getElementById('urban-3d-panel');
      const pBd = document.getElementById('urban-board-panel');
      const pMl = document.getElementById('urban-ml-panel');
      const c2d = document.getElementById('urban-2d-controls');
      const c3d = document.getElementById('urban-3d-controls');

      // CRITICAL: Overcome any CSS !important rule so panels hide/show cleanly
      if (p2d) p2d.style.setProperty('display', tab === '2d' ? 'flex' : 'none', 'important');
      if (p3d) p3d.style.setProperty('display', tab === '3d' ? 'flex' : 'none', 'important');
      if (pBd) pBd.style.setProperty('display', tab === 'board' ? 'flex' : 'none', 'important');
      if (pMl) pMl.style.setProperty('display', tab === 'ml' ? 'flex' : 'none', 'important');
      if (c2d) c2d.style.setProperty('display', tab === '2d' ? 'flex' : 'none', 'important');
      if (c3d) c3d.style.setProperty('display', tab === '3d' ? 'flex' : 'none', 'important');

      ['2d', '3d', 'board', 'ml'].forEach((t) => {
        const btn = document.getElementById(`urban-tab-${t}`);
        if (btn) btn.classList.toggle('active', t === tab);
      });'''

new_switch = '''    switchTab(tab) {
      this.activeTab = tab;
      const p2d = document.getElementById('urban-2d-panel');
      const p3d = document.getElementById('urban-3d-panel');
      const pBd = document.getElementById('urban-board-panel');
      const pMl = document.getElementById('urban-ml-panel');
      const pAi = document.getElementById('urban-site-ai-panel');
      const c2d = document.getElementById('urban-2d-controls');
      const c3d = document.getElementById('urban-3d-controls');

      // CRITICAL: Overcome any CSS !important rule so panels hide/show cleanly
      if (p2d) p2d.style.setProperty('display', tab === '2d' ? 'flex' : 'none', 'important');
      if (p3d) p3d.style.setProperty('display', tab === '3d' ? 'flex' : 'none', 'important');
      if (pBd) pBd.style.setProperty('display', tab === 'board' ? 'flex' : 'none', 'important');
      if (pMl) pMl.style.setProperty('display', tab === 'ml' ? 'flex' : 'none', 'important');
      if (pAi) pAi.style.setProperty('display', tab === 'site-ai' ? 'flex' : 'none', 'important');
      if (c2d) c2d.style.setProperty('display', tab === '2d' ? 'flex' : 'none', 'important');
      if (c3d) c3d.style.setProperty('display', tab === '3d' ? 'flex' : 'none', 'important');

      ['2d', '3d', 'board', 'ml', 'site-ai'].forEach((t) => {
        const btn = document.getElementById(`urban-tab-${t}`);
        if (btn) btn.classList.toggle('active', t === tab);
      });'''

if old_switch in code:
    code = code.replace(old_switch, new_switch)
    print("[OK] switchTab panel display updated.")
else:
    print("[WARN] old_switch not found.")

# Update switchTab branch for site-ai
tab_branch_target = '''      } else if (tab === 'ml' && window.BhuLokaSpatialML) {
        window.BhuLokaSpatialML.renderMLTab();
      }'''

tab_branch_replacement = '''      } else if (tab === 'ml' && window.BhuLokaSpatialML) {
        window.BhuLokaSpatialML.renderMLTab();
      } else if (tab === 'site-ai') {
        this.renderSiteAnalyticsPanel();
      }'''

if tab_branch_target in code:
    code = code.replace(tab_branch_target, tab_branch_replacement)
    print("[OK] switchTab site-ai execution branch added.")
else:
    print("[WARN] tab_branch_target not found.")

# 2. Add robust close handlers to init()
init_target = '''    init() {
      const navBtn = document.getElementById('btn-open-urban-studio');
      if (navBtn) navBtn.onclick = () => this.openStudio();
      const tbBtn = document.getElementById('btn-toggle-exploded-3d');
      if (tbBtn) tbBtn.onclick = () => this.openStudio();
    }'''

init_replacement = '''    init() {
      const navBtn = document.getElementById('btn-open-urban-studio');
      if (navBtn) navBtn.onclick = () => this.openStudio();
      const tbBtn = document.getElementById('btn-toggle-exploded-3d');
      if (tbBtn) tbBtn.onclick = () => this.openStudio();

      // Robust Close Button & Escape Handler
      const closeBtn = document.getElementById('urban-studio-close-btn');
      if (closeBtn) closeBtn.onclick = () => this.closeStudio();

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen) this.closeStudio();
      });

      const modal = document.getElementById('bhu-urban-studio-modal');
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) this.closeStudio();
        });
      }
    }'''

if init_target in code:
    code = code.replace(init_target, init_replacement)
    print("[OK] init() robust close handlers added.")
else:
    print("[WARN] init_target not found.")

with open(JS_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("[DONE] Step 1 of urban studio update completed.")
