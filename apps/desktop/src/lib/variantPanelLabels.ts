export function variantPriceEmptyLabel(): string {
  return "Sin precio registrado para esta variante.";
}

export function priceHistoryEmptyTitle(): string {
  return "Aún no hay histórico de precios para esta variante.";
}

export function priceHistoryEmptyDescription(): string {
  return "Se generará al importar nuevas listas de proveedor.";
}

export function priceHistorySingleTitle(): string {
  return "Primer precio registrado";
}

export function priceHistoryLoadError(): string {
  return "No se pudo cargar el histórico de precios.";
}

export function priceHistoryTableToggle(show: boolean): string {
  return show ? "Ocultar hitos" : "Ver hitos de importación";
}
