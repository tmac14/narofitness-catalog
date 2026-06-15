import type { Category } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

export function CategoryFormCard({
  editingId,
  name,
  parentId,
  allCats,
  onNameChange,
  onParentIdChange,
  onSubmit,
  onCancelEdit,
}: {
  editingId: string | null;
  name: string;
  parentId: string;
  allCats: { id: string; name: string; depth: number }[];
  onNameChange: (value: string) => void;
  onParentIdChange: (value: string) => void;
  onSubmit: (event: React.FormEvent) => void;
  onCancelEdit: () => void;
}) {
  return (
    <Card className="ux30-categories-form-card mb-6">
      <CardHeader>
        <CardTitle>{editingId ? "Editar categoría" : "Nueva categoría"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="ux30-categories-form w-full max-w-md space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cat-name">Nombre *</Label>
            <Input
              id="cat-name"
              required
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              className="min-h-11 w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cat-parent">Categoría padre (opcional)</Label>
            <Select
              id="cat-parent"
              value={parentId}
              onChange={(e) => onParentIdChange(e.target.value)}
              className="min-h-11 w-full"
            >
              <option value="">— Raíz —</option>
              {allCats
                .filter((c) => c.id !== editingId)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {`${"— ".repeat(c.depth)}${c.name}`}
                  </option>
                ))}
            </Select>
          </div>
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap">
            <Button type="submit" className="min-h-11 w-full sm:w-auto">
              {editingId ? "Guardar" : "Crear"}
            </Button>
            {editingId ? (
              <Button
                type="button"
                variant="secondary"
                className="min-h-11 w-full sm:w-auto"
                onClick={onCancelEdit}
              >
                Cancelar
              </Button>
            ) : null}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export function flatCategories(
  nodes: Category[],
  depth = 0,
  acc: { id: string; name: string; depth: number }[] = [],
) {
  for (const n of nodes) {
    acc.push({ id: n.id, name: n.name, depth });
    if (n.children?.length) flatCategories(n.children, depth + 1, acc);
  }
  return acc;
}
