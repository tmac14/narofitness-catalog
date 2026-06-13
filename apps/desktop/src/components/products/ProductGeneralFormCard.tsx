import type { ProductMasterDetail } from "@/lib/api";
import { isMixedBrandMaster, masterBrandDisplay } from "@/lib/variantRepresentation";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

type ProductGeneralFormCardProps = {
  master: ProductMasterDetail;
  categories: { id: string; label: string }[];
  formId: string;
  onChange: (master: ProductMasterDetail) => void;
  onSubmit: (e: React.FormEvent) => void;
  saving?: boolean;
};

export function ProductGeneralFormCard({
  master,
  categories,
  formId,
  onChange,
  onSubmit,
  saving,
}: ProductGeneralFormCardProps) {
  const mixedBrand = isMixedBrandMaster(master);
  const brandDisplay = masterBrandDisplay(master);

  return (
    <Card className="builder-panel">
      <CardHeader>
        <CardTitle>Datos generales</CardTitle>
        <CardDescription>Información principal del producto y su clasificación.</CardDescription>
      </CardHeader>
      <CardContent>
        <form id={formId} onSubmit={onSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="master-name">Nombre</Label>
              <Input
                id="master-name"
                value={master.name}
                onChange={(e) => onChange({ ...master, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="master-brand">Marca</Label>
              {mixedBrand ? (
                <>
                  <Input
                    id="master-brand"
                    value={brandDisplay ?? "Varias marcas"}
                    readOnly
                    className="bg-muted/30"
                  />
                  <p className="text-xs text-muted-foreground">
                    Este producto tiene marcas distintas por variante. Edita la marca en cada
                    variante.
                  </p>
                </>
              ) : (
                <Input
                  id="master-brand"
                  value={master.brand ?? ""}
                  onChange={(e) => onChange({ ...master, brand: e.target.value })}
                />
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="master-category">Categoría</Label>
              <Select
                id="master-category"
                value={master.category_id ?? ""}
                onChange={(e) => onChange({ ...master, category_id: e.target.value || null })}
              >
                <option value="">—</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="master-notes">Notas internas</Label>
              <Textarea
                id="master-notes"
                value={master.notes ?? ""}
                onChange={(e) => onChange({ ...master, notes: e.target.value })}
                rows={4}
              />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="justify-end border-t border-border pt-4">
        <Button type="submit" form={formId} disabled={saving}>
          {saving ? "Guardando…" : "Guardar cambios"}
        </Button>
      </CardFooter>
    </Card>
  );
}
