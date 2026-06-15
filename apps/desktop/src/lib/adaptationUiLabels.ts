/** User-facing labels for adaptation studio screens. */

export function formatAdaptationProjectStatus(status: string | undefined): string {
  const labels: Record<string, string> = {
    draft: "Borrador",
    qa_required: "Pendiente de revisión",
    approved: "Aprobado",
    rendering: "Generando catálogo",
  };
  return labels[status ?? ""] ?? "En curso";
}

export function formatOutputProfile(profile: string | undefined): string {
  const labels: Record<string, string> = {
    email_optimized: "Catálogo para email",
    archive_quality: "Calidad de archivo",
  };
  return labels[profile ?? ""] ?? "Formato desconocido";
}

export function formatDeliveryMode(mode: string | undefined): string {
  const labels: Record<string, string> = {
    persist: "Guardado en el proyecto",
    ephemeral: "Descarga temporal",
  };
  return labels[mode ?? ""] ?? "Destino desconocido";
}

export function formatExportKind(kind: string | undefined): string {
  const labels: Record<string, string> = {
    preview: "Vista previa",
    final: "Exportación final",
  };
  return labels[kind ?? ""] ?? "Exportación";
}

export function formatExportStatus(status: string | undefined): string {
  const labels: Record<string, string> = {
    preview_pdf_ready: "PDF listo",
    final_pdf_ready: "PDF final listo",
    pending: "Pendiente",
    failed: "Error",
  };
  return labels[status ?? ""] ?? "Procesado";
}

export function formatCoverAssetStatus(status: string | undefined): string {
  const labels: Record<string, string> = {
    missing: "Sin imagen",
    resolved: "Imagen asignada",
    referenced_not_bundled: "Imagen pendiente de resolver",
  };
  return labels[status ?? ""] ?? "Sin imagen";
}

export function formatCoverRoleLabel(
  role: string,
  roleLabel?: string | null,
  sectionLabel?: string | null,
): string {
  if (roleLabel) return roleLabel;
  if (role === "main_cover") return "Portada principal";
  if (sectionLabel) return `Portada de categoría · ${sectionLabel}`;
  return "Portada de categoría";
}

export function formatParityScore(score: number): string {
  return `Calidad ${Math.round(score * 100)}%`;
}
