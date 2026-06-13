import { describe, expect, it } from "vitest";
import { centerStatusLabel } from "./jobLabels";
import {
  connectionStatusLabel,
  formatPdfEnginesAvailable,
  pdfEngineDetailMessage,
  pdfEngineDisplayName,
  pdfEngineUserLabel,
  rightWarningSummary,
} from "./statusBarLabels";

describe("statusBarLabels", () => {
  it("maps connection states to Spanish labels", () => {
    expect(connectionStatusLabel(null)).toBe("Conectando…");
    expect(connectionStatusLabel(true)).toBe("Conexión activa");
    expect(connectionStatusLabel(false)).toBe("Sin conexión");
  });

  it("returns idle center label via job center helper", () => {
    expect(centerStatusLabel([], null)).toBe("Sin tareas activas");
  });

  it("describes active PDF engine by name", () => {
    expect(pdfEngineDisplayName("playwright")).toBe("Playwright (Chromium)");
    expect(pdfEngineDisplayName("weasyprint")).toBe("WeasyPrint");
    expect(pdfEngineUserLabel("weasyprint", true)).toBe("Activo: WeasyPrint");
    expect(pdfEngineUserLabel("playwright", true)).toBe("Activo: Playwright (Chromium)");
    expect(pdfEngineUserLabel(null, true)).toBe("No disponible");
    expect(pdfEngineUserLabel(null, false)).toBe("No comprobado (sin conexión)");
  });

  it("lists available engines in detail message", () => {
    const detail = pdfEngineDetailMessage("weasyprint", null, true, {
      available: ["weasyprint"],
      fallback: null,
    });
    expect(detail).toContain("Motor en uso: WeasyPrint");
    expect(detail).toContain("Motores disponibles: WeasyPrint");
    expect(detail).toContain("Playwright");
  });

  it("formats available engine list", () => {
    expect(formatPdfEnginesAvailable(["playwright", "weasyprint"])).toBe(
      "Playwright (Chromium), WeasyPrint",
    );
    expect(formatPdfEnginesAvailable([])).toBe("Ninguno detectado");
  });

  it("shows right warning only when PDF degraded online", () => {
    expect(rightWarningSummary(true, true)).toBe("PDF no disponible");
    expect(rightWarningSummary(true, false)).toBeNull();
    expect(rightWarningSummary(false, true)).toBeNull();
  });
});
