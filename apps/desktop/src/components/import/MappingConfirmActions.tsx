import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { labelMappingStatus } from "@/lib/importMappingLabels";
import type { CanonicalCategoryNode, SourceCategoryDiscovery } from "@/lib/api";

type Props = {
  selectedSource: SourceCategoryDiscovery | null;
  selectedTarget: CanonicalCategoryNode | null;
  loading: boolean;
  onConfirm: (notes: string) => void;
  onIgnore: (notes: string) => void;
  onRemap: () => void;
};

export function MappingConfirmActions({
  selectedSource,
  selectedTarget,
  loading,
  onConfirm,
  onIgnore,
  onRemap,
}: Props) {
  if (!selectedSource) {
    return (
      <p className="text-sm text-muted-foreground">
        Seleccione una categoría del PDF en la lista de la izquierda.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-medium">Categoría en el PDF</p>
        <p className="text-sm">{selectedSource.source_category_path_raw}</p>
        <p className="text-xs text-muted-foreground mt-1">
          Estado: {labelMappingStatus(selectedSource.mapping_status)} · {selectedSource.row_count}{" "}
          filas afectadas
        </p>
        {selectedSource.proposal_reason && (
          <p className="text-xs text-muted-foreground mt-1">{selectedSource.proposal_reason}</p>
        )}
      </div>

      <div>
        <p className="text-sm font-medium">Categoría de destino en su catálogo</p>
        {selectedTarget ? (
          <p className="text-sm">{selectedTarget.full_path}</p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Seleccione una categoría en el árbol de arriba.
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="mapping-notes">Notas (opcional)</Label>
        <Input
          id="mapping-notes"
          placeholder="Notas de revisión"
          defaultValue={selectedSource.notes ?? ""}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          disabled={loading || !selectedTarget}
          onClick={() => {
            const notes =
              (document.getElementById("mapping-notes") as HTMLInputElement | null)?.value ?? "";
            onConfirm(notes);
          }}
        >
          Confirmar asignación
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={loading}
          onClick={() => {
            const notes =
              (document.getElementById("mapping-notes") as HTMLInputElement | null)?.value ?? "";
            onIgnore(notes);
          }}
        >
          Ignorar esta categoría
        </Button>
        <Button type="button" variant="outline" disabled={loading} onClick={onRemap}>
          Aplicar cambios de categorías
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Si ignora una categoría del PDF, las filas pueden seguir marcadas como «sin categoría» hasta
        que confirme una asignación y pulse <strong>Re-aplicar al lote</strong>.
      </p>
    </div>
  );
}
