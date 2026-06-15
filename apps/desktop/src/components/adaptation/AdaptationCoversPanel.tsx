import { useEffect, useRef, useState } from "react";
import { ImagePlus, Loader2 } from "lucide-react";
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
import { resolveCatalogMediaUrl } from "@/lib/catalogCovers";

type Props = {
  projectId: string;
};

export function AdaptationCoversPanel({ projectId }: Props) {
  const [slots, setSlots] = useState<AdaptationCoverSlot[]>([]);
  const [prependMain, setPrependMain] = useState(false);
  const [busySlot, setBusySlot] = useState<string | null>(null);
  const [libraryOpenFor, setLibraryOpenFor] = useState<string | null>(null);
  const [libraryItems, setLibraryItems] = useState<{ relative_path: string; url: string; filename: string }[]>([]);
  const fileInputs = useRef<Record<string, HTMLInputElement | null>>({});

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
      toast.success("Portada asignada");
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
      toast.error(error instanceof Error ? error.message : "No se pudo cargar la biblioteca");
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
      toast.success("Imagen de biblioteca asignada");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo asignar la imagen");
    } finally {
      setBusySlot(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Portadas detectadas</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {prependMain && (
          <p className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs">
            La página 1 del PDF tiene contenido útil. Se insertará una página previa para la
            portada principal al generar el catálogo.
          </p>
        )}
        {slots.length === 0 && <p className="text-muted-foreground">Sin slots de portada detectados.</p>}
        {slots.map((slot) => {
          const preview = resolveCatalogMediaUrl(slot.asset_url);
          const label =
            slot.role === "main_cover"
              ? "Portada principal"
              : slot.section_label || slot.section_key || "Categoría";
          return (
            <div key={slot.slot_id} className="space-y-2 rounded-md border p-3">
              <div className="flex flex-wrap items-center gap-2">
                <strong>{label}</strong>
                <Badge variant="outline">PDF pág. {slot.target_page_number}</Badge>
                <Badge variant="secondary">{slot.asset_status}</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Origen detectado: página {slot.source_page_number}
                {slot.detection_note ? ` · ${slot.detection_note}` : ""}
              </p>
              {preview ? (
                <img src={preview} alt={label} className="max-h-40 rounded-md border object-contain" />
              ) : (
                <div className="flex h-28 items-center justify-center rounded-md border border-dashed text-xs text-muted-foreground">
                  Sin imagen asignada
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
                    if (file) void handleUpload(slot.slot_id, file);
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
                  onClick={() => void openLibrary(slot.slot_id)}
                >
                  Biblioteca de medios
                </Button>
              </div>
              {libraryOpenFor === slot.slot_id && (
                <div className="space-y-2 rounded-md border bg-muted/30 p-2">
                  <Label className="text-xs">Selecciona de la biblioteca</Label>
                  {libraryItems.length === 0 && (
                    <p className="text-xs text-muted-foreground">No hay imágenes en la biblioteca.</p>
                  )}
                  <div className="grid max-h-48 grid-cols-3 gap-2 overflow-y-auto">
                    {libraryItems.map((item) => (
                      <button
                        key={item.relative_path}
                        type="button"
                        className="overflow-hidden rounded border bg-background p-1 text-left hover:ring-2 hover:ring-primary"
                        onClick={() => void pickFromLibrary(slot.slot_id, item.relative_path)}
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
                  <Button size="sm" variant="ghost" onClick={() => setLibraryOpenFor(null)}>
                    Cerrar
                  </Button>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
