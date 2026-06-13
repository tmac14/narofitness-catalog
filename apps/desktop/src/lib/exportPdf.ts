/** PDF export helpers — download trigger, filename sanitization, unsaved-state guards. */

export type UnsavedExportBlock = "order" | "presentation";

function isForbiddenPdfFilenameChar(char: string): boolean {
  const code = char.charCodeAt(0);
  return code <= 31 || '<>:"/\\|?*'.includes(char);
}

export function sanitizePdfFilename(catalogName: string): string {
  const base = catalogName.trim() || "catalogo";
  const safe = Array.from(base, (char) => (isForbiddenPdfFilenameChar(char) ? "_" : char))
    .join("")
    .replace(/\.+$/, "");
  return `${safe}.pdf`;
}

export function triggerPdfDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function getUnsavedExportBlock(
  orderDirty: boolean,
  pendingPreview: boolean,
): UnsavedExportBlock | null {
  if (orderDirty) return "order";
  if (pendingPreview) return "presentation";
  return null;
}

export function unsavedExportMessage(block: UnsavedExportBlock): string {
  if (block === "order") {
    return "Guarda el orden de las líneas en la pestaña Productos antes de exportar el PDF.";
  }
  return "Guarda la configuración de presentación antes de exportar el PDF.";
}

export function unsavedExportTab(block: UnsavedExportBlock): "products" | "presentation" {
  return block === "order" ? "products" : "presentation";
}

export type SaveCatalogOptionsConfig = {
  skipPreviewRefresh?: boolean;
};

/** Whether general-tab fields differ from persisted catalog values. */
export function isGeneralOptionsDirty(
  catalog: {
    name: string;
    default_markup_percent: number | string;
    show_iva_column: boolean;
    show_description_column: boolean;
    cover_subtitle: string | null;
  },
  draft: {
    name: string;
    markup: string;
    showIvaColumn: boolean;
    showDescriptionColumn: boolean;
    coverSubtitle: string;
  },
): boolean {
  const pct = parseFloat(draft.markup);
  const savedPct = parseFloat(String(catalog.default_markup_percent));
  if (Number.isNaN(pct)) return true;
  const draftSubtitle = draft.coverSubtitle.trim() || null;
  const savedSubtitle = catalog.cover_subtitle?.trim() || null;
  return (
    draft.name !== catalog.name ||
    pct !== savedPct ||
    draft.showIvaColumn !== catalog.show_iva_column ||
    draft.showDescriptionColumn !== catalog.show_description_column ||
    draftSubtitle !== savedSubtitle
  );
}
