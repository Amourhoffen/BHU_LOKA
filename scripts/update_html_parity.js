const fs = require('fs');
const path = require('path');

const files = [
  path.join(__dirname, '..', 'index.html'),
  path.join(__dirname, '..', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, '..', 'public', 'index.html'),
  path.join(__dirname, '..', 'public', 'bhu_loka_cyber_dashboard.html')
];

files.forEach(file => {
  if (!fs.existsSync(file)) {
    console.error('File not found:', file);
    return;
  }
  let content = fs.readFileSync(file, 'utf8');

  // 1. Fix OSM tile URL 403
  content = content.replace(
    /`https:\/\/tile\.openstreetmap\.org\/\$\{zoom\}\/\$\{tx\}\/\$\{ty\}\.png`/g,
    '`https://basemaps.cartocdn.com/rastertiles/voyager/${zoom}/${tx}/${ty}.png`'
  );

  // 2. Update Density Mode button text
  const targetStrict = 'onclick="setUrbanVisionMode(\'strict\')" style="font-size:8.5px;padding:3px 4px;" title="High precision — ideal for campuses &amp; rural towns">Strict</button>';
  const replacementStrict = 'onclick="setUrbanVisionMode(\'strict\')" style="font-size:8.5px;padding:3px 4px;" title="High precision — ideal for campuses &amp; rural towns (OSM baseline)">Strict (OSM)</button>';
  if (content.includes(targetStrict)) {
    content = content.replace(targetStrict, replacementStrict);
  }

  const targetBalanced = 'onclick="setUrbanVisionMode(\'balanced\')" style="font-size:8.5px;padding:3px 4px;" title="Shadow-verified balanced Indian urban detector">Balanced</button>';
  const replacementBalanced = 'onclick="setUrbanVisionMode(\'balanced\')" style="font-size:8.5px;padding:3px 4px;" title="Shadow-verified balanced Indian urban detector (OSM + Google Open Buildings + Microsoft ML)">Balanced (+Open/MSFT)</button>';
  if (content.includes(targetBalanced)) {
    content = content.replace(targetBalanced, replacementBalanced);
  }

  const targetDense = 'onclick="setUrbanVisionMode(\'dense\')" style="font-size:8.5px;padding:3px 4px;" title="Dense mohallas &amp; tight row-houses">Dense</button>';
  const replacementDense = 'onclick="setUrbanVisionMode(\'dense\')" style="font-size:8.5px;padding:3px 4px;" title="Dense mohallas &amp; tight row-houses (OSM + Open Buildings + Microsoft ML + Vision ML)">Dense (+Vision ML)</button>';
  if (content.includes(targetDense)) {
    content = content.replace(targetDense, replacementDense);
  }

  // 3. Add urban-stat-bfr-breakdown under urban-stat-bfr
  const targetBfr = '<div id="urban-stat-bfr" style="color:#f1f5f9;font-weight:700;margin-top:2px;">--</div>';
  const replacementBfr = '<div id="urban-stat-bfr" style="color:#f1f5f9;font-weight:700;margin-top:2px;">--</div>\n                <div id="urban-stat-bfr-breakdown" style="font-size:7.5px;color:#94a3b8;font-family:monospace;margin-top:1px;">OSM: -- &middot; GOB: -- &middot; MSFT: --</div>';
  if (!content.includes('id="urban-stat-bfr-breakdown"') && content.includes(targetBfr)) {
    content = content.replace(targetBfr, replacementBfr);
  }

  fs.writeFileSync(file, content, 'utf8');
  console.log('Successfully updated:', path.basename(file), 'in', path.dirname(file));
});
