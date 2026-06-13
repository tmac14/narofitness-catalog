import { describe, expect, it } from "vitest";

import { productMediaNotImageError, productMediaUrlInvalidError } from "./productMediaLabels";
import {
  isProductMediaImageFile,
  resolvePreviewProductImage,
  validateProductMediaFile,
  validateProductMediaUrl,
} from "./productMediaValidation";

describe("productMediaValidation", () => {
  it("isProductMediaImageFile accepts image mime types", () => {
    expect(isProductMediaImageFile(new File([], "a.png", { type: "image/png" }))).toBe(true);
    expect(isProductMediaImageFile(new File([], "a.pdf", { type: "application/pdf" }))).toBe(false);
  });

  it("validateProductMediaFile rejects non-image", () => {
    const result = validateProductMediaFile(new File([], "doc.txt", { type: "text/plain" }));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toBe(productMediaNotImageError());
    }
  });

  it("validateProductMediaFile accepts image", () => {
    expect(validateProductMediaFile(new File([], "photo.webp", { type: "image/webp" }))).toEqual({
      ok: true,
    });
  });

  it("resolvePreviewProductImage prefers primary", () => {
    expect(
      resolvePreviewProductImage([
        { is_primary: false },
        { is_primary: true },
        { is_primary: false },
      ]),
    ).toBe(1);
  });

  it("resolvePreviewProductImage falls back to first image", () => {
    expect(resolvePreviewProductImage([{ is_primary: false }, { is_primary: false }])).toBe(0);
  });

  it("resolvePreviewProductImage empty", () => {
    expect(resolvePreviewProductImage([])).toBe(-1);
  });

  it("validateProductMediaUrl rejects empty", () => {
    const result = validateProductMediaUrl("   ");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toBe(productMediaUrlInvalidError());
    }
  });

  it("validateProductMediaUrl rejects non-http schemes", () => {
    expect(validateProductMediaUrl("ftp://example.com/img.jpg").ok).toBe(false);
    expect(validateProductMediaUrl("example.com/img.jpg").ok).toBe(false);
  });

  it("validateProductMediaUrl accepts http and https", () => {
    expect(validateProductMediaUrl("http://example.com/a.jpg")).toEqual({
      ok: true,
      url: "http://example.com/a.jpg",
    });
    expect(validateProductMediaUrl("  https://example.com/a.jpg  ")).toEqual({
      ok: true,
      url: "https://example.com/a.jpg",
    });
  });
});
