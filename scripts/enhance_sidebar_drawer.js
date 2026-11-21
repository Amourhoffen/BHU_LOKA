const fs = require('fs');
const path = require('path');

const files = [
  path.join(__dirname, '..', 'index.html'),
  path.join(__dirname, '..', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, '..', 'public', 'index.html'),
  path.join(__dirname, '..', 'public', 'bhu_loka_cyber_dashboard.html')
];

// 1. Replacement for the dangerous button[onclick*="close"] rule
const oldCloseBtnCSS = `    /* ═══ CLOSE BUTTONS – uniform ═══ */
    button[onclick*="close"],
    button[onclick*="Close"],
    button[aria-label*="close"],
    button[aria-label*="Close"] {
      width: 28px !important;
      height: 28px !important;
      border-radius: 8px !important;
      background: rgba(255,255,255,0.06) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      color: rgba(148,163,184,0.8) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: background 0.14s, color 0.14s !important;
      flex-shrink: 0 !important;
    }
    button[onclick*="close"]:hover,
    button[onclick*="Close"]:hover,
    button[aria-label*="close"]:hover,
    button[aria-label*="Close"]:hover {
      background: rgba(239,68,68,0.2) !important;
      color: rgb(248,113,113) !important;
      border-color: rgba(239,68,68,0.3) !important;
    }`;

const newCloseBtnCSS = `    /* ═══ CLOSE BUTTONS – uniform (scoped strictly to actual close icon buttons) ═══ */
    .bhu-close-btn,
    .modal-close-btn,
    button.bhu-top-icon-btn,
    button[aria-label="Close"],
    button[aria-label="Close menu"],
    button[aria-label="Close modal"] {
      width: 28px !important;
      height: 28px !important;
      border-radius: 8px !important;
      background: rgba(255,255,255,0.06) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      color: rgba(148,163,184,0.8) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: background 0.14s, color 0.14s !important;
      flex-shrink: 0 !important;
    }
    .bhu-close-btn:hover,
    .modal-close-btn:hover,
    button[aria-label="Close"]:hover,
    button[aria-label="Close menu"]:hover,
    button[aria-label="Close modal"]:hover {
      background: rgba(239,68,68,0.2) !important;
      color: rgb(248,113,113) !important;
      border-color: rgba(239,68,68,0.3) !important;
    }`;

// 2. High-craft Apple-Inspired Sidebar CSS
const newDrawerCSS = `    /* ── APPLE-INSPIRED PREMIUM SIDEBAR DRAWER (UNSLOP + HIGH-CRAFT) ── */
    #bhu-side-drawer {
      position: fixed !important;
      top: 0 !important;
      bottom: 0 !important;
      left: 0 !important;
      width: 320px !important;
      max-width: 88vw !important;
      height: 100dvh !important;
      background: rgba(13, 15, 20, 0.96) !important;
      backdrop-filter: blur(28px) saturate(180%) !important;
      -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
      border-right: 1px solid rgba(255, 255, 255, 0.10) !important;
      z-index: 99999 !important;
      display: flex !important;
      flex-direction: column !important;
      box-sizing: border-box !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      transform: translateX(-100%) !important;
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
      box-shadow: 24px 0 72px rgba(0, 0, 0, 0.90) !important;
    }

    #bhu-side-drawer.drawer-open {
      transform: translateX(0) !important;
    }

    #bhu-drawer-backdrop {
      z-index: 99998 !important;
    }

    .bhu-drawer-nav-container {
      flex: 1 1 0% !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      padding: 8px 10px 16px 10px !important;
      display: flex !important;
      flex-direction: column !important;
      gap: 3px !important;
      -webkit-overflow-scrolling: touch !important;
    }

    /* Clean full-width flex row item */
    .bhu-drawer-item {
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      gap: 12px !important;
      padding: 9px 12px !important;
      width: 100% !important;
      min-height: 44px !important;
      max-height: 52px !important;
      border-radius: 10px !important;
      color: #E2E8F0 !important;
      background: transparent !important;
      border: 1px solid transparent !important;
      box-sizing: border-box !important;
      cursor: pointer !important;
      text-decoration: none !important;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif !important;
      font-size: 13.5px !important;
      font-weight: 500 !important;
      position: static !important;
      transform: none !important;
      margin: 1px 0 !important;
      transition: all 0.16s ease !important;
      text-align: left !important;
    }

    .bhu-drawer-item:hover {
      background: rgba(255, 255, 255, 0.055) !important;
      border-color: rgba(255, 255, 255, 0.08) !important;
      color: #FFFFFF !important;
      transform: translateX(3px) !important;
    }

    .bhu-drawer-item:active {
      transform: scale(0.99) !important;
    }

    .bhu-drawer-item.active {
      background: rgba(56, 189, 248, 0.12) !important;
      border-color: rgba(56, 189, 248, 0.35) !important;
      color: #38bdf8 !important;
    }

    .bhu-drawer-icon {
      width: 32px !important;
      height: 32px !important;
      min-width: 32px !important;
      border-radius: 8px !important;
      background: rgba(255, 255, 255, 0.04) !important;
      border: 1px solid rgba(255, 255, 255, 0.07) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 14px !important;
      text-align: center !important;
      flex-shrink: 0 !important;
      transition: background 0.16s ease, border-color 0.16s ease !important;
    }

    .bhu-drawer-item:hover .bhu-drawer-icon {
      background: rgba(255, 255, 255, 0.08) !important;
      border-color: rgba(255, 255, 255, 0.16) !important;
    }

    .bhu-drawer-label {
      flex: 1 1 auto !important;
      text-align: left !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      color: #F1F5F9 !important;
      font-size: 13.5px !important;
      font-weight: 500 !important;
      letter-spacing: -0.01em !important;
    }

    .bhu-drawer-item:hover .bhu-drawer-label {
      color: #FFFFFF !important;
    }

    .bhu-drawer-badge {
      margin-left: auto !important;
      flex-shrink: 0 !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 9px !important;
      font-weight: 600 !important;
      padding: 2px 7px !important;
      border-radius: 9999px !important;
      letter-spacing: 0.03em !important;
      white-space: nowrap !important;
    }`;

// 3. New Drawer HTML Markup
const newDrawerHTML = `  <aside id="bhu-side-drawer" class="select-none" role="dialog" aria-label="Navigation Menu">
    <!-- USER AVATAR & HEADER (60px) -->
    <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between shrink-0 bg-white/[0.02]" style="height: 60px; box-sizing: border-box;">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-9 h-9 rounded-full bg-gradient-to-tr from-[#0056D2] to-[#38bdf8] flex items-center justify-center text-white text-sm font-bold border border-white/20 shadow-[0_0_12px_rgba(56,189,248,0.35)] shrink-0">
          <i class="fa-solid fa-user-shield"></i>
        </div>
        <div class="min-w-0">
          <div class="text-[13px] font-bold text-slate-100 flex items-center gap-1.5 truncate">
            <span>Sovereign User</span>
            <span class="w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-emerald-950" title="Operational Status"></span>
          </div>
          <div class="text-[9.5px] mono text-slate-400 tracking-tight truncate">BHU LOKA · PAN-INDIA</div>
        </div>
      </div>
      <button type="button" onclick="bhuCloseDrawer()" class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center transition border border-white/10 shrink-0" aria-label="Close menu">
        <i class="fa-solid fa-xmark text-sm"></i>
      </button>
    </div>

    <!-- SCROLLABLE DRAWER NAV ITEMS -->
    <div class="bhu-drawer-nav-container">
      
      <!-- CHALLENGE 03 HERO CARD: TELANGANA LAKE & FTL PROTECTION (JAL RAKSHA) -->
      <div class="mx-1 my-1.5 p-3 rounded-xl bg-gradient-to-br from-[#0a1a30] via-[#071324] to-[#040b15] border border-sky-500/35 shadow-[0_4px_20px_rgba(2,132,199,0.18)] flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-[9px] font-bold tracking-wider mono text-sky-300 bg-sky-950/90 px-2 py-0.5 rounded border border-sky-700/80">CHALLENGE 03 · TELANGANA</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Sentinel-1 SAR & Sentinel-2 L2A Active"></span>
        </div>
        <div>
          <div class="text-[12px] font-bold text-slate-100 flex items-center gap-1.5">
            <i class="fa-solid fa-water text-sky-400 text-xs"></i>
            <span>JAL RAKSHA · Lake &amp; FTL Protection</span>
          </div>
          <div class="text-[9.5px] text-slate-400 leading-snug mt-1">
            Monthly satellite change detection linked to cadastral land records &amp; Full Tank Level boundaries for Hyderabad lakes.
          </div>
        </div>
        <div class="grid grid-cols-2 gap-1.5 pt-1.5 border-t border-sky-500/20">
          <button type="button" onclick="openUrbanStudio('hussain_sagar'); bhuCloseDrawer();" class="text-[9.5px] font-semibold text-sky-200 hover:text-white bg-sky-900/40 hover:bg-sky-800/60 border border-sky-600/40 rounded-lg py-1 px-1.5 text-center transition flex items-center justify-center gap-1">
            <i class="fa-solid fa-crosshairs text-[8.5px]"></i> Hussain Sagar
          </button>
          <button type="button" onclick="openUrbanStudio('osman_sagar'); bhuCloseDrawer();" class="text-[9.5px] font-semibold text-sky-200 hover:text-white bg-sky-900/40 hover:bg-sky-800/60 border border-sky-600/40 rounded-lg py-1 px-1.5 text-center transition flex items-center justify-center gap-1">
            <i class="fa-solid fa-crosshairs text-[8.5px]"></i> Osman Sagar
          </button>
        </div>
      </div>

      <div class="text-[10px] font-semibold tracking-wider text-slate-500 uppercase px-3 pt-2 pb-0.5 mono">Core Workstations</div>

      <!-- Chat History -->
      <button type="button" onclick="bhuOpenChatHistory(); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-sky-400"><i class="fa-solid fa-clock-rotate-left"></i></span>
        <span class="bhu-drawer-label">Chat History</span>
        <span class="bhu-drawer-badge bg-sky-500/20 text-sky-300 border border-sky-500/30">LOCAL</span>
      </button>

      <!-- Home -->
      <button type="button" onclick="bhuNavTo('home'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-blue-400"><i class="fa-solid fa-house"></i></span>
        <span class="bhu-drawer-label">Home</span>
      </button>

      <!-- 2D Earth -->
      <a href="bhu_loka_leafmap_interactive.html" target="_blank" onclick="bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-emerald-400"><i class="fa-solid fa-globe"></i></span>
        <span class="bhu-drawer-label">2D Earth Map</span>
        <i class="fa-solid fa-arrow-up-right-from-square text-[10.5px] text-slate-400 ml-auto shrink-0"></i>
      </a>

      <!-- Hazard Analysis -->
      <button type="button" onclick="bhuNavTo('hazard'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-amber-400"><i class="fa-solid fa-triangle-exclamation"></i></span>
        <span class="bhu-drawer-label">Hazard Analysis</span>
      </button>

      <!-- Land Studio -->
      <button type="button" onclick="bhuNavTo('land-studio'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-cyan-400"><i class="fa-solid fa-layer-group"></i></span>
        <span class="bhu-drawer-label">Land Intelligence Studio</span>
        <span class="bhu-drawer-badge bg-blue-600/25 text-sky-300 border border-sky-400/35">JAL RAKSHA</span>
      </button>

      <!-- AI Assistant -->
      <button type="button" onclick="bhuNavTo('ai'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-indigo-400"><i class="fa-solid fa-microchip"></i></span>
        <span class="bhu-drawer-label">Cyber AI Assistant</span>
      </button>

      <!-- Farmer -->
      <button type="button" onclick="bhuNavTo('farmer'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-emerald-400"><i class="fa-solid fa-seedling"></i></span>
        <span class="bhu-drawer-label">Farmer Intelligence (Kisan)</span>
      </button>

      <!-- Health -->
      <button type="button" onclick="bhuNavTo('health'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-rose-400"><i class="fa-solid fa-heart-pulse"></i></span>
        <span class="bhu-drawer-label">Health &amp; Worker Suite</span>
      </button>

      <!-- Research Report -->
      <button type="button" onclick="if(typeof openModelIntelModal==='function')openModelIntelModal('overview'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-teal-400"><i class="fa-solid fa-file-lines"></i></span>
        <span class="bhu-drawer-label">NASA 2026 Research Report</span>
        <span class="bhu-drawer-badge bg-teal-500/20 text-teal-300 border border-teal-500/30">EMPIRICAL</span>
      </button>

      <div class="h-px bg-white/10 my-2 mx-2"></div>
      <div class="text-[10px] font-semibold tracking-wider text-slate-500 uppercase px-3 pt-1 pb-0.5 mono">Governance &amp; Platform</div>

      <!-- Privacy Policy -->
      <button type="button" onclick="bhuOpenInfoModal('privacy'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-slate-400"><i class="fa-solid fa-file-shield"></i></span>
        <span class="bhu-drawer-label">Privacy Policy</span>
      </button>

      <!-- Security -->
      <button type="button" onclick="bhuOpenInfoModal('security'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-slate-400"><i class="fa-solid fa-shield-halved"></i></span>
        <span class="bhu-drawer-label">Security &amp; Compliance</span>
      </button>

      <!-- About BHU LOKA -->
      <button type="button" onclick="bhuOpenInfoModal('about'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-sky-400"><i class="fa-solid fa-circle-info"></i></span>
        <span class="bhu-drawer-label">About BHU LOKA</span>
      </button>

      <!-- Settings -->
      <button type="button" onclick="bhuOpenInfoModal('settings'); bhuCloseDrawer();" class="bhu-drawer-item">
        <span class="bhu-drawer-icon text-slate-400"><i class="fa-solid fa-gear"></i></span>
        <span class="bhu-drawer-label">Settings</span>
      </button>
    </div>

    <!-- DRAWER FOOTER (44px) -->
    <div class="px-4 py-2.5 border-t border-white/10 bg-black/60 text-[10px] mono text-slate-400 flex items-center justify-between shrink-0">
      <span class="text-slate-300 font-semibold">BHU LOKA v6.8</span>
      <span class="text-sky-400 flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>SOVEREIGN AI</span>
    </div>
  </aside>`;

files.forEach(file => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');

  // 1. Fix the close button CSS rule that was squishing drawer buttons
  if (content.includes(oldCloseBtnCSS)) {
    content = content.replace(oldCloseBtnCSS, newCloseBtnCSS);
    console.log('Fixed close button CSS in:', path.basename(file));
  } else {
    // Regex fallback
    const r = /\/\* ═══ CLOSE BUTTONS – uniform ═══ \*\/[\s\S]*?button\[aria-label\*="Close"\]:hover \{[\s\S]*?\}/;
    if (r.test(content)) {
      content = content.replace(r, newCloseBtnCSS);
      console.log('Fixed close button CSS via regex in:', path.basename(file));
    }
  }

  // 2. Replace drawer CSS block (lines 2435 to 2515)
  const drawerCssRegex = /\/\* ── SIDEBAR DRAWER[\s\S]*?\.bhu-drawer-label \{[\s\S]*?text-overflow: ellipsis !important;\s*\}/;
  if (drawerCssRegex.test(content)) {
    content = content.replace(drawerCssRegex, newDrawerCSS);
    console.log('Replaced drawer CSS in:', path.basename(file));
  }

  // 3. Replace the entire <aside id="bhu-side-drawer"> ... </aside> HTML markup
  const drawerHtmlRegex = /<aside id="bhu-side-drawer"[\s\S]*?<\/aside>/;
  if (drawerHtmlRegex.test(content)) {
    content = content.replace(drawerHtmlRegex, newDrawerHTML);
    console.log('Replaced drawer HTML in:', path.basename(file));
  }

  fs.writeFileSync(file, content, 'utf8');
});

console.log('Sidebar enhancement complete across all files!');
