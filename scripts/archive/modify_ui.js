// Node script to clean up UI in index.html and duplicate dashboard file
const fs = require('fs');
const path = require('path');

function cleanFile(filePath) {
  let html = fs.readFileSync(filePath, 'utf8');
  // 1. Remove red/pink/rose buttons (bg-rose, bg-pink, bg-rose-500 etc.)
  html = html.replace(/<button[^>]*\bbg-(rose|pink)[^>]*>.*?<\/button>/gis, '');
  // Also remove any button with class containing bg-rose-500 (covers other variants)
  html = html.replace(/<button[^>]*\bbg-rose-\d+[\w-]*[^>]*>.*?<\/button>/gis, '');

  // 2. Extract yellow (amber) buttons
  const yellowButtons = [];
  html = html.replace(/<button[^>]*\bbg-amber[^>]*>.*?<\/button>/gis, (match) => { yellowButtons.push(match); return ''; });

  // 3. Ensure side panel exists and insert yellow buttons
  if (!html.includes('id="side-panel"')) {
    // Insert side panel before closing of left rail or before </body>
    const sidePanelHtml = `<div id="side-panel" class="panel p-2">${yellowButtons.join('\n')}</div>`;
    // Try to insert after left rail div if exists
    if (html.includes('id="left-rail"')) {
      html = html.replace(/(<\/div>\s*<!--?\s*left-rail\s*--?>)/i, sidePanelHtml + '\n$1');
    } else {
      // fallback before </body>
      html = html.replace(/<\/body>/i, sidePanelHtml + '\n</body>');
    }
  } else {
    // Append yellow buttons to existing side panel content
    html = html.replace(/(<div id="side-panel"[^>]*>)(.*?)(<\/div>)/is, `$1$2\n${yellowButtons.join('\n')}$3`);
  }

  // 4. Enhance green (emerald) buttons – ensure they have hover/active classes if missing
  // Add hover:bg-emerald-600 and active scaling if not present
  html = html.replace(/(<button[^>]*\bbg-emerald[^>]*)(>)/gi, (m, pre, post) => {
    let classes = pre;
    if (!/hover:bg-emerald-600/.test(classes)) classes += ' hover:bg-emerald-600';
    if (!/active:/.test(classes)) classes += ' active:scale-95';
    return classes + post;
  });

  // 5. Add close button to GPS HUD if not present
  if (html.includes('id="holo-live-tracker-hud"')) {
    html = html.replace(/(<div id="holo-live-tracker-hud"[^>]*>)/i, `$1\n<button class=\"px-2 py-1 rounded bg-gray-800 text-white\" aria-label=\"Close GPS HUD\" onclick=\"this.parentElement.classList.add('hidden');\">×</button>`);
  }

  // 6. Clean mail panel – remove any button without an onclick or that is duplicate (simple heuristic)
  html = html.replace(/<button([^>]*?)>(.*?)<\/button>/gi, (full, attrs, inner) => {
    if (/\bmail-panel\b/.test(full) && (!/onclick/.test(attrs) || /duplicate/.test(inner))) {
      return '';
    }
    return full;
  });

  // 7. Improve left-side "?" help button – add tooltip and modal trigger
  html = html.replace(/(<button[^>]*\?[^>]*>)/i, (match) => {
    if (!/title=/.test(match)) {
      return match.replace('>', ' title="Open help" data-modal="help-modal">');
    }
    return match;
  });

  // 8. Remove neon colors (any class containing "neon" or bright gradient) – replace with muted equivalents
  html = html.replace(/bg-(amber|rose|rose-500|amber-500|rose-950|amber-950|rose-600|amber-600|rose-400|amber-400)(\/[^\s'">]*)?/gi, (m) => {
    // replace with softer gray variant
    return 'bg-gray-700';
  });

  // 9. Remove emojis – strip any unicode emoji characters from HTML text nodes
  // Simple regex removing characters in the emoji range
  html = html.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}]/gu, '');

  fs.writeFileSync(filePath, html, 'utf8');
  console.log('Cleaned', filePath);
}

const indexPath = path.join(__dirname, 'Bhu Loka - भूलोक', 'public', 'index.html');
const dashboardPath = path.join(__dirname, 'Bhu Loka - भूलोक', 'public', 'bhu_loka_cyber_dashboard.html');
cleanFile(indexPath);
cleanFile(dashboardPath);
