const fs = require('fs');
const path = require('path');

const files = [
  path.join(__dirname, '..', 'index.html'),
  path.join(__dirname, '..', 'bhu_loka_cyber_dashboard.html'),
  path.join(__dirname, '..', 'public', 'index.html'),
  path.join(__dirname, '..', 'public', 'bhu_loka_cyber_dashboard.html')
];

files.forEach(file => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');

  // 1. Bump cache buster for urban studio js to v=60
  content = content.replace(/bhu_loka_urban_studio\.js\?v=\d+/g, 'bhu_loka_urban_studio.js?v=60');

  // 2. Fix land-studio branch in bhuNavTo
  const oldLandBranch = `} else if (module === 'land-studio') {
          if (typeof openUrbanStudio === 'function') {
            openUrbanStudio();
          } else if (typeof open2DCropStudio === 'function') {
            open2DCropStudio();
          }
        }`;

  const newLandBranch = `} else if (module === 'land-studio') {
          // Explicitly close 2D crop modal if open
          const cropModal = document.getElementById('bhu-crop-3d-modal');
          if (cropModal) {
            cropModal.classList.add('hidden');
            cropModal.style.display = 'none';
          }
          if (typeof close2DCropStudio === 'function') close2DCropStudio();

          // Open the real Land Intelligence Studio modal
          if (typeof openUrbanStudio === 'function') {
            openUrbanStudio();
          } else {
            const urbanModal = document.getElementById('bhu-urban-studio-modal');
            if (urbanModal) {
              urbanModal.classList.remove('hidden');
              urbanModal.style.display = 'flex';
            }
          }
        }`;

  if (content.includes(oldLandBranch)) {
    content = content.replace(oldLandBranch, newLandBranch);
    console.log('Fixed land-studio branch in:', path.basename(file));
  } else {
    // Try regex replacement if whitespace differed slightly
    const landRegex = /\} else if \(module === ['"]land-studio['"]\) \{\s*if \(typeof openUrbanStudio === ['"]function['"]\) \{\s*openUrbanStudio\(\);\s*\} else if \(typeof open2DCropStudio === ['"]function['"]\) \{\s*open2DCropStudio\(\);\s*\}\s*\}/;
    if (landRegex.test(content)) {
      content = content.replace(landRegex, newLandBranch);
      console.log('Fixed land-studio branch via regex in:', path.basename(file));
    } else {
      console.warn('Target not matched in:', path.basename(file));
    }
  }

  fs.writeFileSync(file, content, 'utf8');
});
console.log('Done updating HTML files.');
