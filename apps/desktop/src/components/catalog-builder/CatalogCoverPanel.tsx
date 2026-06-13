import { useRef, useState } from "react";
import { ImageIcon, Loader2, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { deleteCatalogCoverImage, uploadCatalogCoverImage } from "@/lib/api";
import { resolveCatalogMediaUrl } from "@/lib/catalogCovers";
import { parseApiError } from "@/lib/catalogLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  catalogId: string;
  coverImageUrl: string | null;
  coverSubtitle: string;
  onCoverSubtitleChange: (value: string) => void;
  onCoverImageUpdated: (coverImageUrl: string | null) => void;
  onCoverMediaChanged: () => void;
};

export function CatalogCoverPanel({
  catalogId,
  coverImageUrl,
  coverSubtitle,
  onCoverSubtitleChange,
  onCoverImageUpdated,
  onCoverMediaChanged,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const previewSrc = resolveCatalogMediaUrl(coverImageUrl);
  const busy = uploading || deleting;

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      const result = await uploadCatalogCoverImage(catalogId, file);
      onCoverImageUpdated(result.cover_image_url);
      onCoverMediaChanged();
      toast.success("Portada del catálogo actualizada");
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete() {
    if (!coverImageUrl) return;
    setDeleting(true);
    try {
      await deleteCatalogCoverImage(catalogId);
      onCoverImageUpdated(null);
      onCoverMediaChanged();
      toast.success("Portada del catálogo eliminada");
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Card className="mb-6 builder-panel">
      <CardHeader>
        <CardTitle className="text-base">Portada del catálogo</CardTitle>
        <CardDescription>Imagen principal para la portada del PDF.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <div className="image-card flex h-[140px] w-full max-w-[220px] shrink-0 items-center justify-center bg-muted/30">
            {previewSrc ? (
              <img
                src={previewSrc}
                alt="Portada del catálogo"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 px-4 text-center text-muted-foreground">
                <ImageIcon className="h-8 w-8 opacity-60" aria-hidden="true" />
                <span className="text-xs">Sin imagen de portada</span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="sr-only"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleUpload(file);
              }}
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              {coverImageUrl ? "Reemplazar imagen" : "Subir imagen"}
            </Button>
            {coverImageUrl && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={busy}
                onClick={() => void handleDelete()}
              >
                {deleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Eliminar imagen
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-2 border-t border-border pt-4">
          <Label htmlFor="cover-subtitle">Subtítulo de portada</Label>
          <Input
            id="cover-subtitle"
            value={coverSubtitle}
            onChange={(e) => onCoverSubtitleChange(e.target.value)}
            placeholder="Texto opcional para la portada"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            Texto opcional que aparece en la portada del catálogo.
          </p>
          <p className="text-xs text-muted-foreground">
            Guarda las opciones del PDF para aplicar el subtítulo. La imagen se guarda al subirla o
            eliminarla.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
