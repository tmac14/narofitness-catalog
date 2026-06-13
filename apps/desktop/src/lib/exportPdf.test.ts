import { describe, expect, it, vi, afterEach } from "vitest";
import {
  getUnsavedExportBlock,
  isGeneralOptionsDirty,
  sanitizePdfFilename,
  triggerPdfDownload,
  unsavedExportMessage,
  unsavedExportTab,
  type SaveCatalogOptionsConfig,
} from "./exportPdf";

describe("exportPdf helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sanitizePdfFilename removes unsafe characters", () => {
    expect(sanitizePdfFilename('Catálogo "2024"')).toBe("Catálogo _2024_.pdf");
    expect(sanitizePdfFilename("")).toBe("catalogo.pdf");
  });

  it("getUnsavedExportBlock prioritizes order over presentation", () => {
    expect(getUnsavedExportBlock(true, true)).toBe("order");
    expect(getUnsavedExportBlock(false, true)).toBe("presentation");
    expect(getUnsavedExportBlock(false, false)).toBeNull();
  });

  it("unsavedExportMessage and tab map to the correct surface", () => {
    expect(unsavedExportMessage("order")).toContain("Productos");
    expect(unsavedExportMessage("presentation")).toContain("presentación");
    expect(unsavedExportTab("order")).toBe("products");
    expect(unsavedExportTab("presentation")).toBe("presentation");
  });

  it("SaveCatalogOptionsConfig supports skipPreviewRefresh flag", () => {
    const config: SaveCatalogOptionsConfig = { skipPreviewRefresh: true };
    expect(config.skipPreviewRefresh).toBe(true);
  });

  it("isGeneralOptionsDirty detects draft changes", () => {
    const catalog = {
      name: "Demo",
      default_markup_percent: 10,
      show_iva_column: false,
      show_description_column: true,
      cover_subtitle: null,
    };
    const draft = {
      name: "Demo",
      markup: "10",
      showIvaColumn: false,
      showDescriptionColumn: true,
      coverSubtitle: "",
    };
    expect(isGeneralOptionsDirty(catalog, draft)).toBe(false);
    expect(isGeneralOptionsDirty(catalog, { ...draft, name: "Nuevo" })).toBe(true);
    expect(isGeneralOptionsDirty(catalog, { ...draft, markup: "12" })).toBe(true);
    expect(isGeneralOptionsDirty(catalog, { ...draft, showIvaColumn: true })).toBe(true);
    expect(isGeneralOptionsDirty(catalog, { ...draft, showDescriptionColumn: false })).toBe(true);
    expect(isGeneralOptionsDirty(catalog, { ...draft, coverSubtitle: "Edición 2026" })).toBe(true);
  });

  it("triggerPdfDownload creates anchor with sanitized filename", () => {
    const click = vi.fn();
    const anchor = {
      href: "",
      download: "",
      style: { display: "" },
      click,
    };
    const appendChild = vi.fn((node: unknown) => node);
    const removeChild = vi.fn((node: unknown) => node);
    const revokeObjectURL = vi.fn();

    vi.stubGlobal("document", {
      createElement: () => anchor,
      body: { appendChild, removeChild },
    });
    vi.stubGlobal("URL", {
      createObjectURL: () => "blob:test",
      revokeObjectURL,
    });

    triggerPdfDownload(new Blob(["%PDF"]), "demo.pdf");

    expect(anchor.download).toBe("demo.pdf");
    expect(anchor.href).toBe("blob:test");
    expect(click).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test");
  });
});
