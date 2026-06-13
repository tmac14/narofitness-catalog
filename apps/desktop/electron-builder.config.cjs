/** @type {import('electron-builder').Configuration} */
module.exports = {
  appId: "com.narofitness.narocatalog",
  productName: "NaroCatalog",
  directories: {
    output: "release",
    buildResources: "../../public/icons",
  },
  files: ["dist/**/*", "electron/**/*", "package.json"],
  // Phase 1b: add Playwright Chromium to extraResources and set PLAYWRIGHT_BROWSERS_PATH in runtime.cjs
  extraResources: [
    {
      from: "../../packaging/dist/catalog-api.exe",
      to: "engine/catalog-api.exe",
      filter: ["**/*"],
    },
    {
      from: "../../packaging/postgres",
      to: "postgres",
      filter: ["**/*"],
    },
  ],
  win: {
    icon: "../../public/icons/app-mark.png",
    target: [{ target: "nsis", arch: ["x64"] }],
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    installerLanguages: ["es"],
    language: "1034",
  },
  electronDownload: {
    cache: undefined,
  },
};
