export type ProductMediaScope = "master" | "variant";

export function productMediaUploadAriaLabel(scope: ProductMediaScope, sku?: string): string {
  if (scope === "variant" && sku?.trim()) {
    return `Subir imagen de la variante ${sku.trim()}`;
  }
  return "Subir imagen del producto";
}

export function productMediaInstructionsId(scope: ProductMediaScope): string {
  return scope === "variant"
    ? "product-media-instructions-variant"
    : "product-media-instructions-master";
}

export function productMediaEmptyTitle(scope: ProductMediaScope): string {
  return scope === "variant" ? "Sin imagen de variante" : "Sin imágenes del producto";
}

export function productMediaEmptyHint(): string {
  return "Haz clic o arrastra una imagen";
}

export function productMediaReplaceHint(): string {
  return "Cambiar imagen";
}

export function productMediaAddAnotherLabel(): string {
  return "Añadir otra imagen";
}

export function productMediaUploadingLabel(): string {
  return "Subiendo imagen…";
}

export function productMediaNotImageError(): string {
  return "El archivo debe ser una imagen.";
}

export function productMediaUploadFailedError(): string {
  return "No se pudo subir la imagen.";
}

export function productMediaVariantHeading(): string {
  return "Imagen de variante";
}

export function productMediaVariantDescription(sku: string): string {
  return `Fotos asociadas a la referencia ${sku}, no al producto general.`;
}

export function productMediaUseExternalUrlLabel(): string {
  return "Usar URL externa";
}

export function productMediaUrlFieldLabel(): string {
  return "URL de la imagen";
}

export function productMediaUrlHint(): string {
  return "Pega una URL pública de imagen.";
}

export function productMediaUrlStorageHint(): string {
  return "La imagen se guardará en la app para poder usarla en catálogos.";
}

export function productMediaUrlSchemeHint(): string {
  return "La URL debe empezar por http:// o https://.";
}

export function productMediaUrlInvalidError(): string {
  return "Introduce una URL válida que empiece por http:// o https://.";
}

export function productMediaUrlSubmitLabel(): string {
  return "Añadir imagen";
}

export function productMediaUrlCancelLabel(): string {
  return "Cancelar";
}

export function productMediaUrlSubmittingLabel(): string {
  return "Añadiendo imagen…";
}

export function productMediaUrlFailedError(): string {
  return "No se pudo añadir la imagen desde la URL.";
}

export function productMediaExternalBadgeLabel(): string {
  return "URL externa";
}

export function productMediaViewOriginLabel(): string {
  return "Ver origen";
}
