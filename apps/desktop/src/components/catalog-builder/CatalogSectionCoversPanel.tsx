import { useEffect, useMemo, useRef, useState } from "react";
import { ImageIcon, Loader2, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import type { CatalogSectionCover, Category } from "@/lib/api";
import { deleteCatalogSectionCover, upsertCatalogSectionCover } from "@/lib/api";
import {
  buildSectionCoverEditorRows,
  indexCategoriesByName,
  resolveCatalogMediaUrl,
} from "@/lib/catalogCovers";
import { parseApiError } from "@/lib/catalogLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  catalogId: string;
  sectionCovers: CatalogSectionCover[];
  bySection: Record<string, number> | null;
  categories: Category[];
  onSectionCoversUpdated: () => void;
  onCoverMediaChanged: () => void;
};

type RowBusyState = {
  upload?: boolean;
  saveDescription?: boolean;
  delete?: boolean;
};

function SectionCoverRowEditor({
  catalogId,
  row,
  onUpdated,
  onCoverMediaChanged,
}: {
  catalogId: string;
  row: ReturnType<typeof buildSectionCoverEditorRows>[number];
  onUpdated: () => void;
  onCoverMediaChanged: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [description, setDescription] = useState(row.description ?? "");
  const [busy, setBusy] = useState<RowBusyState>({});

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDescription(row.description ?? "");
    }, 0);
    return () => window.clearTimeout(timer);
  }, [row.description, row.categoryId]);

  const previewSrc = resolveCatalogMediaUrl(row.coverImageUrl);
  const isBusy = Boolean(busy.upload || busy.saveDescription || busy.delete);
  const descriptionDirty = description !== (row.description ?? "");

  if (!row.canEdit || !row.categoryId) {
    return (
      <div className="rounded-lg border border-border bg-muted/20 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="font-medium">{row.sectionName}</p>
            <p className="text-xs text-muted-foreground">{row.productCount} productos</p>
          </div>
          <Badge variant="secondary">Sin categoría asignada</Badge>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Los productos sin categoría no admiten portada de sección. Asigna una categoría para
          habilitar esta opción.
        </p>
      </div>
    );
  }

  async function handleUpload(file: File) {
    setBusy((s) => ({ ...s, upload: true }));
    try {
      await upsertCatalogSectionCover(catalogId, row.categoryId!, {
        file,
        description: description.trim() || null,
      });
      onUpdated();
      onCoverMediaChanged();
      toast.success(`Portada de «${row.sectionName}» actualizada`);
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setBusy((s) => ({ ...s, upload: false }));
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleSaveDescription() {
    setBusy((s) => ({ ...s, saveDescription: true }));
    try {
      await upsertCatalogSectionCover(catalogId, row.categoryId!, {
        description: description.trim() || null,
      });
      onUpdated();
      onCoverMediaChanged();
      toast.success(`Descripción de «${row.sectionName}» guardada`);
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setBusy((s) => ({ ...s, saveDescription: false }));
    }
  }

  async function handleDelete() {
    setBusy((s) => ({ ...s, delete: true }));
    try {
      await deleteCatalogSectionCover(catalogId, row.categoryId!);
      setDescription("");
      onUpdated();
      onCoverMediaChanged();
      toast.success(`Portada de «${row.sectionName}» eliminada`);
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setBusy((s) => ({ ...s, delete: false }));
    }
  }

  const hasCover = Boolean(row.coverImageUrl || row.description);

  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">{row.sectionName}</p>
          <p className="text-xs text-muted-foreground">{row.productCount} productos</p>
        </div>
        {hasCover ? (
          <Badge variant="success">Portada configurada</Badge>
        ) : (
          <Badge variant="outline">Sin portada</Badge>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="image-card flex h-[100px] w-full max-w-[160px] shrink-0 items-center justify-center bg-muted/30">
          {previewSrc ? (
            <img
              src={previewSrc}
              alt={`Portada ${row.sectionName}`}
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="flex flex-col items-center gap-1 px-2 text-center text-muted-foreground">
              <ImageIcon className="h-6 w-6 opacity-60" aria-hidden="true" />
              <span className="text-[10px]">Sin imagen</span>
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="sr-only"
            disabled={isBusy}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleUpload(file);
            }}
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={isBusy}
            onClick={() => fileInputRef.current?.click()}
          >
            {busy.upload ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {row.coverImageUrl ? "Reemplazar" : "Subir imagen"}
          </Button>
          {hasCover && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isBusy}
              onClick={() => void handleDelete()}
            >
              {busy.delete ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Eliminar portada
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor={`section-cover-desc-${row.categoryId}`}>Descripción de sección</Label>
        <Input
          id={`section-cover-desc-${row.categoryId}`}
          value={description}
          disabled={isBusy}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Texto para la portada de esta categoría"
        />
        <p className="text-xs text-muted-foreground">
          Se mostrará en la página de portada de esta categoría.
        </p>
        {!row.coverImageUrl && !row.description && (
          <p className="text-xs text-muted-foreground">
            Añade una imagen o descripción para crear una portada de categoría en el PDF.
          </p>
        )}
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={isBusy || !descriptionDirty}
          onClick={() => void handleSaveDescription()}
        >
          {busy.saveDescription ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Guardando…
            </>
          ) : (
            "Guardar descripción"
          )}
        </Button>
      </div>
    </div>
  );
}

export function CatalogSectionCoversPanel({
  catalogId,
  sectionCovers,
  bySection,
  categories,
  onSectionCoversUpdated,
  onCoverMediaChanged,
}: Props) {
  const rows = useMemo(() => {
    if (!bySection) return [];
    return buildSectionCoverEditorRows(bySection, sectionCovers, indexCategoriesByName(categories));
  }, [bySection, sectionCovers, categories]);

  if (!bySection || rows.length === 0) {
    return null;
  }

  return (
    <Card className="builder-panel">
      <CardHeader>
        <CardTitle className="text-base">Portadas de categoría</CardTitle>
        <CardDescription>
          Imagen o descripción opcional para la portada de cada categoría en el PDF. No afecta a las
          tablas de productos.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map((row) => (
          <SectionCoverRowEditor
            key={row.sectionName}
            catalogId={catalogId}
            row={row}
            onUpdated={onSectionCoversUpdated}
            onCoverMediaChanged={onCoverMediaChanged}
          />
        ))}
      </CardContent>
    </Card>
  );
}
