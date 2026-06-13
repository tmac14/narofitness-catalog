import { describe, expect, it } from "vitest";
import { isPreviewBusy, previewStatusLabel, shouldShowPreviewErrorPanel } from "@/lib/previewState";

describe("previewState helpers", () => {
  it("previewStatusLabel returns Spanish labels", () => {
    expect(previewStatusLabel("ready")).toBe("Actualizada");
    expect(previewStatusLabel("stale")).toBe("Desactualizada");
    expect(previewStatusLabel("error")).toBe("Error al cargar");
  });

  it("shouldShowPreviewErrorPanel only for error", () => {
    expect(shouldShowPreviewErrorPanel("error")).toBe(true);
    expect(shouldShowPreviewErrorPanel("ready")).toBe(false);
  });

  it("isPreviewBusy is true when loading", () => {
    expect(isPreviewBusy("loading")).toBe(true);
    expect(isPreviewBusy("ready")).toBe(false);
  });
});
