/**
 * BHU LOKA (भूलोक) - Chromium Desktop Shell (VS Code / Electron Architecture)
 * Wraps the Sovereign Geospatial AI 3D Deck & All-India GIS Atlas inside
 * an isolated Chromium + V8 Desktop Runtime with IPC bridge to Python RAG/ML.
 */

const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
const { execFile } = require('child_process');

const WORKSPACE_ROOT = path.resolve(__dirname, '..');
const DASHBOARD_HTML = path.join(WORKSPACE_ROOT, 'bhu_loka_cyber_dashboard.html');
const LEAFMAP_HTML = path.join(WORKSPACE_ROOT, 'bhu_loka_leafmap_interactive.html');
const PYTHON_RAG_SCRIPT = path.join(WORKSPACE_ROOT, 'Models', '04_Hybrid_RAG', 'god_eye_hybrid_rag.py');

// Enable GPU WebGL2 rendering in Chromium
app.commandLine.appendSwitch('enable-webgl2-compute-context');
app.commandLine.appendSwitch('ignore-gpu-blocklist');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1580,
    height: 940,
    minWidth: 1200,
    minHeight: 760,
    backgroundColor: '#04060a',
    title: 'BHU LOKA (भूलोक) — Chromium Sovereign Geospatial AI',
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webgl: true
    }
  });

  mainWindow.loadFile(DASHBOARD_HTML);

  const template = [
    {
      label: 'BHU LOKA Views',
      submenu: [
        {
          label: '3D God\'s Eye Command Deck',
          accelerator: 'Ctrl+1',
          click: () => mainWindow.loadFile(DASHBOARD_HTML)
        },
        {
          label: 'All-India & Patna Real Satellite GIS',
          accelerator: 'Ctrl+2',
          click: () => mainWindow.loadFile(LEAFMAP_HTML)
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'toggleDevTools', accelerator: 'F12' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// IPC handler connecting Chromium renderer directly to local Python Hybrid RAG Engine
ipcMain.handle('bhuLoka:queryPythonRag', async (_event, queryText) => {
  return new Promise((resolve) => {
    execFile('python', [PYTHON_RAG_SCRIPT, String(queryText)], { cwd: WORKSPACE_ROOT, timeout: 15000 }, (err, stdout, stderr) => {
      if (err) {
        resolve({ ok: false, error: stderr || err.message });
      } else {
        resolve({ ok: true, output: stdout });
      }
    });
  });
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

