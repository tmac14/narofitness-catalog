import { useEffect, useState, useSyncExternalStore } from "react";
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
import {
  CategoryFormCard,
  flatCategories,
} from "@/components/categories/CategoryFormCard";
import { CategoryTree } from "@/components/categories/CategoryTree";
import { BREAKPOINT_PX } from "@/lib/responsive/breakpoints";
import { classifyPlatformWidth } from "@/lib/responsive/platform";

function getViewportWidth(): number {
  if (typeof window === "undefined") return BREAKPOINT_PX.desktopMin;
  return window.innerWidth;
}

function getServerViewportWidth(): number {
  return BREAKPOINT_PX.desktopMin;
}

function subscribeViewport(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("resize", onStoreChange);
  return () => window.removeEventListener("resize", onStoreChange);
}

function useDefaultTreeExpanded(): boolean {
  const width = useSyncExternalStore(subscribeViewport, getViewportWidth, getServerViewportWidth);
  return classifyPlatformWidth(width) !== "mobile";
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
  const defaultTreeExpanded = useDefaultTreeExpanded();

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
    window.setTimeout(() => {
      document.getElementById("cat-name")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
  }

  function onAddChild(pid: string) {
    setEditingId(null);
    setName("");
    setParentId(pid);
    window.setTimeout(() => {
      document.getElementById("cat-name")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
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

  const allCats = flatCategories(tree);

  return (
    <div>
      <PageHeader
        title="Categorías"
        description="Organice productos en un árbol jerárquico."
        icon={FolderTree}
      />

      <CategoryFormCard
        editingId={editingId}
        name={name}
        parentId={parentId}
        allCats={allCats}
        onNameChange={setName}
        onParentIdChange={setParentId}
        onSubmit={(event) => {
          void onSubmit(event);
        }}
        onCancelEdit={() => {
          setEditingId(null);
          setName("");
          setParentId("");
        }}
      />

      {showSkeleton ? (
        <FormSkeleton />
      ) : fetchError ? (
        <ErrorState
          title="No se pudieron cargar las categorías"
          description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
          action={
            <Button type="button" variant="secondary" className="min-h-11" onClick={refresh}>
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
              <CategoryTree
                nodes={tree}
                defaultExpanded={defaultTreeExpanded}
                onEdit={onEdit}
                onDelete={requestDelete}
                onAddChild={onAddChild}
              />
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
            <Button
              type="button"
              variant="secondary"
              className="min-h-11"
              onClick={() => setDeleteTarget(null)}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="min-h-11"
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
