const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("narocatalog", {
  apiBase: process.env.NAROCATALOG_API_BASE || "http://127.0.0.1:8000",
  isElectron: true,
  windowControls: {
    minimize: () => ipcRenderer.send("window-minimize"),
    close: () => ipcRenderer.send("window-close"),
  },
});
