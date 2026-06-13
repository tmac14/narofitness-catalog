/** Plain Spanish labels for App Status Bar (Phase 1 — system health only). */

const PDF_ENGINE_LABELS: Record<string, string> = {
  playwright: "Playwright (Chromium)",
  weasyprint: "WeasyPrint",
  princexml: "PrinceXML",
  docraptor: "DocRaptor",
};

export function pdfEngineDisplayName(engine: string): string {
  return PDF_ENGINE_LABELS[engine] ?? engine;
}

export function connectionStatusLabel(connected: boolean | null): string {
  if (connected === null) return "Conectando…";
  if (connected) return "Conexión activa";
  return "Sin conexión";
}

export function pdfEngineUserLabel(engine: string | null, connected: boolean | null): string {
  if (connected !== true) return "No comprobado (sin conexión)";
  if (!engine) return "No disponible";
  return `Activo: ${pdfEngineDisplayName(engine)}`;
}

export function formatPdfEnginesAvailable(engines: string[]): string {
  if (engines.length === 0) return "Ninguno detectado";
  return engines.map(pdfEngineDisplayName).join(", ");
}

export type PdfEngineDetailOptions = {
  available?: string[];
  fallback?: string | null;
};

export function pdfEngineDetailMessage(
  engine: string | null,
  error: string | null,
  connected: boolean | null,
  options?: PdfEngineDetailOptions,
): string {
  if (connected !== true) {
    return "Conecte la aplicación al servicio para comprobar la exportación PDF.";
  }
  if (!engine) {
    return error
      ? "La exportación a PDF no está disponible en este momento. Puede seguir trabajando con el resto de la aplicación."
      : "La exportación a PDF no está disponible.";
  }

  const parts: string[] = [
    `Motor en uso: ${pdfEngineDisplayName(engine)}.`,
    `Motores disponibles: ${formatPdfEnginesAvailable(options?.available ?? (engine ? [engine] : []))}.`,
  ];

  if (options?.fallback) {
    parts.push(`Reserva automática: ${pdfEngineDisplayName(options.fallback)}.`);
  }

  if (engine === "weasyprint" && !(options?.available ?? []).includes("playwright")) {
    parts.push(
      "Solo WeasyPrint está operativo; la vista previa y la exportación pueden tardar más. Reconstruya la imagen Docker para habilitar Playwright.",
    );
  } else {
    parts.push("Puede generar catálogos en PDF desde el editor de catálogos.");
  }

  return parts.join(" ");
}

export function rightWarningSummary(
  connected: boolean | null,
  pdfDegraded: boolean,
): string | null {
  if (connected === false) return null;
  if (pdfDegraded) return "PDF no disponible";
  return null;
}

export function formatLastHealthCheck(date: Date | null): string {
  if (!date) return "—";
  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
