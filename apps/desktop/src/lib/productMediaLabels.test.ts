import { describe, expect, it } from "vitest";

import {
  productMediaAddAnotherLabel,
  productMediaEmptyHint,
  productMediaEmptyTitle,
  productMediaExternalBadgeLabel,
  productMediaUploadAriaLabel,
  productMediaUrlHint,
  productMediaUseExternalUrlLabel,
  productMediaVariantDescription,
  productMediaViewOriginLabel,
} from "./productMediaLabels";

describe("productMediaLabels", () => {
  it("productMediaUploadAriaLabel for master", () => {
    expect(productMediaUploadAriaLabel("master")).toBe("Subir imagen del producto");
  });

  it("productMediaUploadAriaLabel for variant with sku", () => {
    expect(productMediaUploadAriaLabel("variant", "CRO-SACO")).toBe(
      "Subir imagen de la variante CRO-SACO",
    );
  });

  it("productMediaEmptyTitle differs by scope", () => {
    expect(productMediaEmptyTitle("master")).toBe("Sin imágenes del producto");
    expect(productMediaEmptyTitle("variant")).toBe("Sin imagen de variante");
  });

  it("productMediaEmptyHint is actionable", () => {
    expect(productMediaEmptyHint()).toBe("Haz clic o arrastra una imagen");
  });

  it("productMediaVariantDescription references sku", () => {
    expect(productMediaVariantDescription("DOBHT")).toContain("DOBHT");
    expect(productMediaVariantDescription("DOBHT")).toContain("no al producto general");
  });

  it("productMediaAddAnotherLabel", () => {
    expect(productMediaAddAnotherLabel()).toBe("Añadir otra imagen");
  });

  it("external URL labels", () => {
    expect(productMediaUseExternalUrlLabel()).toBe("Usar URL externa");
    expect(productMediaUrlHint()).toBe("Pega una URL pública de imagen.");
    expect(productMediaExternalBadgeLabel()).toBe("URL externa");
    expect(productMediaViewOriginLabel()).toBe("Ver origen");
  });
});
