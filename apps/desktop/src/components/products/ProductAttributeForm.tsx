import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type ProductAttributeFormProps = {
  attrKey: string;
  attrVal: string;
  onAttrKeyChange: (value: string) => void;
  onAttrValChange: (value: string) => void;
  onSaveAttribute: () => void;
  defaultOpen?: boolean;
};

export function ProductAttributeForm({
  attrKey,
  attrVal,
  onAttrKeyChange,
  onAttrValChange,
  onSaveAttribute,
  defaultOpen = false,
}: ProductAttributeFormProps) {
  return (
    <details
      className="product-attribute-form rounded-lg border border-border bg-muted/10"
      open={defaultOpen}
    >
      <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background [&::-webkit-details-marker]:hidden">
        <span className="text-muted-foreground">+</span> Añadir atributo manual
      </summary>
      <div className="border-t border-border px-4 py-4">
        <p className="mb-3 text-xs text-muted-foreground">
          Atributo común a todas las variantes de este producto.
        </p>
        <div className="flex flex-wrap gap-3">
          <div className="space-y-1">
            <Label htmlFor="attr-key" className="text-xs">
              Nombre del atributo
            </Label>
            <Input
              id="attr-key"
              placeholder="Ej. material"
              value={attrKey}
              onChange={(e) => onAttrKeyChange(e.target.value)}
              className="w-[160px]"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="attr-val" className="text-xs">
              Valor
            </Label>
            <Input
              id="attr-val"
              placeholder="Ej. acero"
              value={attrVal}
              onChange={(e) => onAttrValChange(e.target.value)}
              className="w-[160px]"
            />
          </div>
          <div className="flex items-end">
            <Button type="button" variant="secondary" size="sm" onClick={onSaveAttribute}>
              Guardar atributo
            </Button>
          </div>
        </div>
      </div>
    </details>
  );
}
