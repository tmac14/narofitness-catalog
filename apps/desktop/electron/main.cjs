const { app, BrowserWindow, shell, ipcMain } = require("electron");
const path = require("path");

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;
let API_BASE = process.env.API_BASE || "http://127.0.0.1:8000";
let shutdownRuntime = null;

ipcMain.on("window-minimize", (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (win && !win.isDestroyed()) win.minimize();
});

ipcMain.on("window-close", (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (win && !win.isDestroyed()) win.close();
});

function createWindow() {
  const win = new BrowserWindow({
    frame: false,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    win.loadURL("http://127.0.0.1:5173");
    if (process.env.OPEN_DEVTOOLS === "1") {
      win.webContents.openDevTools({ mode: "detach" });
    }
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  win.once("ready-to-show", () => {
    win.maximize();
    win.show();
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(async () => {
  if (!isDev) {
    try {
      const { startRuntime } = require("./runtime.cjs");
      const rt = await startRuntime(app);
      API_BASE = rt.apiBase;
      shutdownRuntime = rt.shutdown;
      process.env.DATA_DIR = rt.dataDir;
    } catch (err) {
      console.error("Runtime start failed:", err);
    }
  }
  process.env.NAROCATALOG_API_BASE = API_BASE;
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (shutdownRuntime) shutdownRuntime();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (shutdownRuntime) shutdownRuntime();
});
