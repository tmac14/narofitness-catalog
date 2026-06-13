export type PreviewState = "idle" | "loading" | "ready" | "stale" | "error";

export function previewStatusLabel(state: PreviewState): string {
  switch (state) {
    case "loading":
      return "Regenerando…";
    case "ready":
      return "Actualizada";
    case "stale":
      return "Desactualizada";
    case "error":
      return "Error al cargar";
    default:
      return "Sin preview";
  }
}

export function shouldShowPreviewErrorPanel(state: PreviewState): boolean {
  return state === "error";
}

export function isPreviewBusy(state: PreviewState): boolean {
  return state === "loading";
}
