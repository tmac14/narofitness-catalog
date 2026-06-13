import { describe, expect, it } from "vitest";

import {
  priceHistoryEmptyDescription,
  priceHistoryEmptyTitle,
  priceHistoryLoadError,
  priceHistorySingleTitle,
  variantPriceEmptyLabel,
} from "./variantPanelLabels";

describe("variantPanelLabels", () => {
  it("variantPriceEmptyLabel returns stable copy", () => {
    expect(variantPriceEmptyLabel()).toBe("Sin precio registrado para esta variante.");
  });

  it("priceHistoryEmptyTitle and description", () => {
    expect(priceHistoryEmptyTitle()).toBe("Aún no hay histórico de precios para esta variante.");
    expect(priceHistoryEmptyDescription()).toBe(
      "Se generará al importar nuevas listas de proveedor.",
    );
  });

  it("priceHistorySingleTitle", () => {
    expect(priceHistorySingleTitle()).toBe("Primer precio registrado");
  });

  it("priceHistoryLoadError", () => {
    expect(priceHistoryLoadError()).toBe("No se pudo cargar el histórico de precios.");
  });
});
