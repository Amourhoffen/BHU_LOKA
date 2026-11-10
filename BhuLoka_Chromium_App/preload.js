const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bhuLokaDesktop', {
  runtime: 'Chromium + Electron + V8',
  chromiumVersion: process.versions.chrome || 'embedded',
  nodeVersion: process.versions.node || 'embedded',
  queryPythonRag: (queryText) => ipcRenderer.invoke('bhuLoka:queryPythonRag', queryText)
});

