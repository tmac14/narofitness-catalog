import { useEffect, useState } from "react";
import { toast } from "sonner";
import { FolderTree } from "lucide-react";
import {
  createCategory,
  deleteCategory,
  listCategories,
  updateCategory,
  type Category,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FormSkeleton } from "@/components/LoadingPage";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function CategoryNode({
  node,
  onEdit,
  onDelete,
  onAddChild,
}: {
  node: Category;
  onEdit: (c: Category) => void;
  onDelete: (id: string, name: string) => void;
  onAddChild: (parentId: string) => void;
}) {
  return (
    <li className="ml-4 mb-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">{node.name}</span>
        <Button type="button" variant="secondary" size="sm" onClick={() => onEdit(node)}>
          Editar
        </Button>
        <Button type="button" variant="secondary" size="sm" onClick={() => onAddChild(node.id)}>
          + Hijo
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="text-destructive border-destructive/30 hover:bg-destructive/10"
          onClick={() => onDelete(node.id, node.name)}
        >
          Eliminar
        </Button>
      </div>
      {node.children?.length > 0 && (
        <ul className="list-none pl-0 mt-2 border-l border-border ml-2">
          {node.children.map((ch) => (
            <CategoryNode
              key={ch.id}
              node={ch}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddChild={onAddChild}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function CategoriesPage() {
  const [tree, setTree] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState<string>("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const showSkeleton = useDelayedLoading(loading);

  function refresh(): void {
    setFetchError(false);
    void listCategories()
      .then(setTree)
      .catch(() => {
        setTree([]);
        setFetchError(true);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  function flat(
    nodes: Category[],
    depth = 0,
    acc: { id: string; name: string; depth: number }[] = [],
  ) {
    for (const n of nodes) {
      acc.push({ id: n.id, name: n.name, depth });
      if (n.children?.length) flat(n.children, depth + 1, acc);
    }
    return acc;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      if (editingId) {
        await updateCategory(editingId, {
          name: name.trim(),
          parent_id: parentId || null,
        });
        toast.success("Categoría actualizada.");
      } else {
        await createCategory(name.trim(), parentId || null);
        toast.success("Categoría creada.");
      }
      setName("");
      setParentId("");
      setEditingId(null);
      refresh();
    } catch (err) {
      toast.error(String(err));
    }
  }

  function onEdit(c: Category) {
    setEditingId(c.id);
    setName(c.name);
    setParentId(c.parent_id ?? "");
  }

  function onAddChild(pid: string) {
    setEditingId(null);
    setName("");
    setParentId(pid);
  }

  function requestDelete(id: string, categoryName: string) {
    setDeleteTarget({ id, name: categoryName });
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteCategory(deleteTarget.id);
      toast.success("Categoría eliminada.");
      setDeleteTarget(null);
      refresh();
    } catch (err) {
      toast.error(String(err));
    } finally {
      setDeleting(false);
    }
  }

  const allCats = flat(tree);

  return (
    <div>
      <PageHeader
        title="Categorías"
        description="Organice productos en un árbol jerárquico."
        icon={FolderTree}
      />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{editingId ? "Editar categoría" : "Nueva categoría"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(event) => {
              void onSubmit(event);
            }}
            className="max-w-md space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="cat-name">Nombre *</Label>
              <Input
                id="cat-name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat-parent">Categoría padre (opcional)</Label>
              <Select
                id="cat-parent"
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
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
            <div className="flex gap-2">
              <Button type="submit">{editingId ? "Guardar" : "Crear"}</Button>
              {editingId && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    setEditingId(null);
                    setName("");
                    setParentId("");
                  }}
                >
                  Cancelar
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {showSkeleton ? (
        <FormSkeleton />
      ) : fetchError ? (
        <ErrorState
          title="No se pudieron cargar las categorías"
          description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
          action={
            <Button type="button" size="sm" variant="secondary" onClick={refresh}>
              Reintentar
            </Button>
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Árbol de categorías</CardTitle>
          </CardHeader>
          <CardContent>
            {tree.length === 0 ? (
              <EmptyState
                icon={FolderTree}
                title="Sin categorías"
                description="Créelas aquí o impórtelas desde un PDF."
              />
            ) : (
              <ul className="list-none pl-0">
                {tree.map((n) => (
                  <CategoryNode
                    key={n.id}
                    node={n}
                    onEdit={onEdit}
                    onDelete={requestDelete}
                    onAddChild={onAddChild}
                  />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}

      <Dialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Eliminar categoría?</DialogTitle>
            <DialogDescription>
              Se eliminará «{deleteTarget?.name}». Solo es posible si no tiene productos ni
              subcategorías.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleting}
              onClick={() => {
                void confirmDelete();
              }}
            >
              {deleting ? "Eliminando…" : "Eliminar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
