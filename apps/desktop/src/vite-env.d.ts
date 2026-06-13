/// <reference types="vite/client" />

interface NarocatalogBridge {
  apiBase: string;
  isElectron: boolean;
  windowControls: {
    minimize: () => void;
    close: () => void;
  };
}

declare global {
  interface Window {
    narocatalog?: NarocatalogBridge;
  }
}

export {};
