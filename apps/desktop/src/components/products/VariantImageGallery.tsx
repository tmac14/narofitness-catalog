import type { ProductImage } from "@/lib/api";
import { ProductMediaCard } from "./ProductMediaCard";

type VariantImageGalleryProps = {
  images: ProductImage[];
  apiBase: string;
  altLabel: string;
  sku: string;
  onUpload: (file: File) => Promise<void>;
  onAddFromUrl: (url: string) => Promise<void>;
  onDelete: (imageId: string) => Promise<void>;
  onSetPrimary?: (imageId: string) => Promise<void>;
};

export function VariantImageGallery({
  images,
  apiBase,
  altLabel,
  sku,
  onUpload,
  onAddFromUrl,
  onDelete,
  onSetPrimary,
}: VariantImageGalleryProps) {
  return (
    <ProductMediaCard
      scope="variant"
      images={images}
      apiBase={apiBase}
      sku={sku}
      altLabel={altLabel}
      onUpload={onUpload}
      onAddFromUrl={onAddFromUrl}
      onDelete={onDelete}
      onSetPrimary={onSetPrimary}
    />
  );
}
