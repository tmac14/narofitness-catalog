import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import { BookMarked, ImagePlus, Layers, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  assignAdaptationCoverFromLibrary,
  getAdaptationCoverSlots,
  listAdaptationMediaLibrary,
  uploadAdaptationCoverSlot,
  type AdaptationCoverSlot,
} from "@/lib/api";
import {
  formatCoverAssetStatus,
  formatCoverRoleLabel,
} from "@/lib/adaptationUiLabels";
import { resolveCatalogMediaUrl } from "@/lib/catalogCovers";

type Props = {
  projectId: string;
};

function CoverSlotCard({
  slot,
  busySlot,
  libraryOpenFor,
  libraryItems,
  fileInputs,
  onUpload,
  onOpenLibrary,
  onPickFromLibrary,
  onCloseLibrary,
}: {
  slot: AdaptationCoverSlot;
  busySlot: string | null;
  libraryOpenFor: string | null;
  libraryItems: { relative_path: string; url: string; filename: string }[];
  fileInputs: MutableRefObject<Record<string, HTMLInputElement | null>>;
  onUpload: (slotId: string, file: File) => void;
  onOpenLibrary: (slotId: string) => void;
  onPickFromLibrary: (slotId: string, relativePath: string) => void;
  onCloseLibrary: () => void;
}) {
  const preview = resolveCatalogMediaUrl(slot.asset_url);
  const isMain = slot.cover_type === "main" || slot.role === "main_cover";
  const title = formatCoverRoleLabel(slot.role, slot.role_label, slot.section_label);
  const categoryName = !isMain ? slot.section_label || slot.section_key : null;

  return (
    <div
      className={`space-y-2 rounded-md border p-3 ${
        isMain ? "border-primary/40 bg-primary/5" : "border-muted"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        {isMain ? (
          <BookMarked className="h-4 w-4 text-primary" aria-hidden="true" />
        ) : (
          <Layers className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        )}
        <strong>{title}</strong>
        <Badge variant={isMain ? "default" : "secondary"}>
          {isMain ? "Portada principal" : "Portada de categoría"}
        </Badge>
        <Badge variant="outline">Página {slot.target_page_number} del PDF</Badge>
        <Badge variant="outline">{formatCoverAssetStatus(slot.asset_status)}</Badge>
      </div>
      {!isMain && categoryName && (
        <p className="text-xs font-medium text-foreground">Categoría: {categoryName}</p>
      )}
      <p className="text-xs text-muted-foreground">
        Detectada en la página {slot.source_page_number} del documento original.
        {slot.detection_note ? ` ${slot.detection_note}` : ""}
      </p>
      {preview ? (
        <img src={preview} alt={title} className="max-h-40 rounded-md border object-contain" />
      ) : (
        <div className="flex h-28 items-center justify-center rounded-md border border-dashed text-xs text-muted-foreground">
          Todavía no hay imagen para esta portada
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <input
          ref={(node) => {
            fileInputs.current[slot.slot_id] = node;
          }}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onUpload(slot.slot_id, file);
            event.target.value = "";
          }}
        />
        <Button
          size="sm"
          variant="outline"
          disabled={busySlot === slot.slot_id}
          onClick={() => fileInputs.current[slot.slot_id]?.click()}
        >
          {busySlot === slot.slot_id ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <ImagePlus className="mr-2 h-4 w-4" />
          )}
          Subir imagen
        </Button>
        <Button
          size="sm"
          variant="secondary"
          disabled={busySlot === slot.slot_id}
          onClick={() => onOpenLibrary(slot.slot_id)}
        >
          Elegir de la biblioteca
        </Button>
      </div>
      {libraryOpenFor === slot.slot_id && (
        <div className="space-y-2 rounded-md border bg-muted/30 p-2">
          <Label className="text-xs">Imágenes disponibles</Label>
          {libraryItems.length === 0 && (
            <p className="text-xs text-muted-foreground">No hay imágenes guardadas todavía.</p>
          )}
          <div className="grid max-h-48 grid-cols-3 gap-2 overflow-y-auto">
            {libraryItems.map((item) => (
              <button
                key={item.relative_path}
                type="button"
                className="overflow-hidden rounded border bg-background p-1 text-left hover:ring-2 hover:ring-primary"
                onClick={() => onPickFromLibrary(slot.slot_id, item.relative_path)}
              >
                <img
                  src={resolveCatalogMediaUrl(item.url) ?? item.url}
                  alt={item.filename}
                  className="h-16 w-full object-cover"
                />
                <span className="mt-1 block truncate text-[10px]">{item.filename}</span>
              </button>
            ))}
          </div>
          <Button size="sm" variant="ghost" onClick={onCloseLibrary}>
            Cerrar
          </Button>
        </div>
      )}
    </div>
  );
}

export function AdaptationCoversPanel({ projectId }: Props) {
  const [slots, setSlots] = useState<AdaptationCoverSlot[]>([]);
  const [prependMain, setPrependMain] = useState(false);
  const [busySlot, setBusySlot] = useState<string | null>(null);
  const [libraryOpenFor, setLibraryOpenFor] = useState<string | null>(null);
  const [libraryItems, setLibraryItems] = useState<{ relative_path: string; url: string; filename: string }[]>([]);
  const fileInputs = useRef<Record<string, HTMLInputElement | null>>({});

  const mainSlot = useMemo(
    () => slots.find((slot) => slot.cover_type === "main" || slot.role === "main_cover") ?? null,
    [slots],
  );
  const categorySlots = useMemo(
    () => slots.filter((slot) => slot.cover_type === "category" || slot.role === "section_cover"),
    [slots],
  );

  useEffect(() => {
    let cancelled = false;
    void getAdaptationCoverSlots(projectId)
      .then((payload) => {
        if (cancelled) return;
        setSlots(payload.slots);
        setPrependMain(payload.prepend_main_cover);
      })
      .catch((error) => {
        if (cancelled) return;
        toast.error(error instanceof Error ? error.message : "No se pudieron cargar las portadas");
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const handleUpload = async (slotId: string, file: File) => {
    setBusySlot(slotId);
    try {
      const payload = await uploadAdaptationCoverSlot(projectId, slotId, file);
      setSlots(payload.slots);
      setPrependMain(payload.prepend_main_cover);
      toast.success("Imagen asignada correctamente");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo subir la imagen");
    } finally {
      setBusySlot(null);
    }
  };

  const openLibrary = async (slotId: string) => {
    setLibraryOpenFor(slotId);
    try {
      const payload = await listAdaptationMediaLibrary();
      setLibraryItems(payload.items);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo abrir la biblioteca");
      setLibraryOpenFor(null);
    }
  };

  const pickFromLibrary = async (slotId: string, relativePath: string) => {
    setBusySlot(slotId);
    try {
      const payload = await assignAdaptationCoverFromLibrary(projectId, slotId, relativePath);
      setSlots(payload.slots);
      setPrependMain(payload.prepend_main_cover);
      setLibraryOpenFor(null);
      toast.success("Imagen asignada desde la biblioteca");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo asignar la imagen");
    } finally {
      setBusySlot(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Portadas del catálogo</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 text-sm">
        <p className="text-xs text-muted-foreground">
          Hemos detectado qué páginas del PDF original son portadas. Asigna una imagen para la
          portada principal y para cada categoría antes de generar la vista previa.
        </p>
        {prependMain && (
          <p className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs">
            La primera página del PDF ya tiene contenido de productos. Crearemos una página
            adicional al inicio solo para la portada principal.
          </p>
        )}
        {slots.length === 0 && (
          <p className="text-muted-foreground">No hemos detectado portadas en este documento.</p>
        )}
        {mainSlot && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Portada principal</h3>
            <CoverSlotCard
              slot={mainSlot}
              busySlot={busySlot}
              libraryOpenFor={libraryOpenFor}
              libraryItems={libraryItems}
              fileInputs={fileInputs}
              onUpload={(slotId, file) => void handleUpload(slotId, file)}
              onOpenLibrary={(slotId) => void openLibrary(slotId)}
              onPickFromLibrary={(slotId, path) => void pickFromLibrary(slotId, path)}
              onCloseLibrary={() => setLibraryOpenFor(null)}
            />
          </div>
        )}
        {categorySlots.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">
              Portadas de categoría ({categorySlots.length})
            </h3>
            <div className="space-y-3">
              {categorySlots.map((slot) => (
                <CoverSlotCard
                  key={slot.slot_id}
                  slot={slot}
                  busySlot={busySlot}
                  libraryOpenFor={libraryOpenFor}
                  libraryItems={libraryItems}
                  fileInputs={fileInputs}
                  onUpload={(slotId, file) => void handleUpload(slotId, file)}
                  onOpenLibrary={(slotId) => void openLibrary(slotId)}
                  onPickFromLibrary={(slotId, path) => void pickFromLibrary(slotId, path)}
                  onCloseLibrary={() => setLibraryOpenFor(null)}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
