/** Spanish display labels for import review codes (UI only — API values unchanged). */

export const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  needs_review: "Revisar",
  ok: "Correcto",
  revisar: "Revisar",
  duplicado: "Duplicado",
  confirmed: "Confirmado",
  imported: "Importado",
};

export const ACTION_LABELS: Record<string, string> = {
  price_update: "Actualizar precio",
  new_variant: "Nueva variante",
  revisar: "Revisar",
};

export const REASON_LABELS: Record<string, string> = {
  missing_sku: "Sin referencia (SKU)",
  missing_price: "Sin precio",
  missing_name: "Sin nombre",
  duplicate_sku: "Referencia duplicada",
  regex_fallback_1_1: "Un producto por fila",
  db_missing_sku: "Referencia vacía",
  false_family_pattern: "Familia incorrecta",
  low_grouping_confidence: "Agrupación poco segura",
  unmapped_category: "Sin categoría asignada",
  unknown_spec_key: "Atributo desconocido",
  spec_validation_failed: "Atributo no válido",
};

export function labelStatus(code: string | undefined | null): string {
  if (!code) return "—";
  return STATUS_LABELS[code] ?? code;
}

export function labelAction(code: string | undefined | null): string {
  if (!code) return "—";
  return ACTION_LABELS[code] ?? code;
}

export function labelReason(code: string): string {
  if (code.startsWith("unknown_color_value:")) {
    const value = code.slice("unknown_color_value:".length);
    return `Color no reconocido: ${value}`;
  }
  return REASON_LABELS[code] ?? code;
}
