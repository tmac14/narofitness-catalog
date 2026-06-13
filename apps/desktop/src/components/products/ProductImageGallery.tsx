import type { ProductMasterDetail } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductMediaCard } from "./ProductMediaCard";

type ProductImageGalleryProps = {
  master: ProductMasterDetail;
  apiBase: string;
  productName: string;
  onUpload: (file: File) => Promise<void>;
  onAddFromUrl: (url: string) => Promise<void>;
  onDelete: (imageId: string) => Promise<void>;
  onSetPrimary: (imageId: string) => Promise<void>;
};

export function ProductImageGallery({
  master,
  apiBase,
  productName,
  onUpload,
  onAddFromUrl,
  onDelete,
  onSetPrimary,
}: ProductImageGalleryProps) {
  return (
    <Card className="builder-panel">
      <CardHeader>
        <CardTitle className="text-base">Imágenes</CardTitle>
        <CardDescription>Fotos del producto a nivel de familia.</CardDescription>
      </CardHeader>
      <CardContent>
        <ProductMediaCard
          scope="master"
          images={master.images}
          apiBase={apiBase}
          productName={productName}
          onUpload={onUpload}
          onAddFromUrl={onAddFromUrl}
          onDelete={onDelete}
          onSetPrimary={onSetPrimary}
        />
      </CardContent>
    </Card>
  );
}
