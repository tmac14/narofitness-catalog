import { productMediaNotImageError, productMediaUrlInvalidError } from "./productMediaLabels";

export type ProductMediaValidationResult = { ok: true } | { ok: false; message: string };

export type ProductMediaUrlValidationResult =
  | { ok: true; url: string }
  | { ok: false; message: string };

export function isProductMediaImageFile(file: File): boolean {
  return file.type.startsWith("image/");
}

export function validateProductMediaFile(file: File): ProductMediaValidationResult {
  if (!isProductMediaImageFile(file)) {
    return { ok: false, message: productMediaNotImageError() };
  }
  return { ok: true };
}

export function validateProductMediaUrl(url: string): ProductMediaUrlValidationResult {
  const trimmed = url.trim();
  if (!trimmed || !/^https?:\/\//i.test(trimmed)) {
    return { ok: false, message: productMediaUrlInvalidError() };
  }
  return { ok: true, url: trimmed };
}

export function resolvePreviewProductImage(images: { is_primary: boolean }[]): number {
  const primaryIndex = images.findIndex((img) => img.is_primary);
  if (primaryIndex >= 0) return primaryIndex;
  return images.length > 0 ? 0 : -1;
}
