import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Truck } from "lucide-react";
import { listImportProfiles, listSuppliers, type ImportProfile, type Supplier } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { TwoColumnSkeleton } from "@/components/LoadingPage";
import { Badge } from "@/components/ui/badge";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import {
  SUPPLIERS_PROFILES_VIEW_POLICY,
  useDataViewMode,
} from "@/hooks/useDataViewMode";
import { ImportProfileCardList } from "@/components/suppliers/ImportProfileCardList";
import { parserLabel } from "@/components/suppliers/parserLabels";
import { cn } from "@/lib/utils";

type DetailView = "list" | "profiles";

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [profiles, setProfiles] = useState<ImportProfile[]>([]);
  const [selected, setSelected] = useState("");
  const [detailView, setDetailView] = useState<DetailView>("list");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [profilesError, setProfilesError] = useState(false);
  const showSkeleton = useDelayedLoading(loading);
  const { showTable } = useDataViewMode(SUPPLIERS_PROFILES_VIEW_POLICY);

  const loadSuppliers = useCallback(() => {
    setLoading(true);
    setFetchError(false);
    listSuppliers()
      .then(setSuppliers)
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadSuppliers();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadSuppliers]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!selected) {
        setProfiles([]);
        setProfilesError(false);
        return;
      }
      setProfilesError(false);
      void listImportProfiles(selected)
        .then(setProfiles)
        .catch(() => {
          setProfiles([]);
          setProfilesError(true);
        });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [selected]);

  useEffect(() => {
    if (showTable) {
      setDetailView("list");
    }
  }, [showTable]);

  const selectedSupplier = suppliers.find((s) => s.id === selected);

  const showMasterPanel = showTable || detailView === "list";
  const showProfilesPanel = showTable || detailView === "profiles";

  function handleSelectSupplier(id: string) {
    setSelected(id);
    if (!showTable) {
      setDetailView("profiles");
    }
  }

  function retryLoadProfiles() {
    setProfilesError(false);
    void listImportProfiles(selected)
      .then(setProfiles)
      .catch(() => setProfilesError(true));
  }

  function renderProfilesContent() {
    if (profilesError) {
      return (
        <ErrorState
          title="No se pudieron cargar los perfiles"
          description="Compruebe la conexión e inténtelo de nuevo."
          action={
            <Button
              type="button"
              variant="secondary"
              className="min-h-11"
              onClick={retryLoadProfiles}
            >
              Reintentar
            </Button>
          }
          className="py-8"
        />
      );
    }

    if (!selected) {
      return (
        <EmptyState
          icon={Truck}
          title="Seleccione un proveedor"
          description="Elija un proveedor de la lista para ver sus perfiles."
          className="py-8"
        />
      );
    }

    if (profiles.length === 0) {
      return (
        <EmptyState
          icon={Truck}
          title="Sin perfiles"
          description={`El proveedor ${selectedSupplier?.name} no tiene perfiles de importación configurados.`}
          action={
            <Button asChild variant="secondary" className="min-h-11">
              <Link to="/import">Ir a importar tarifa</Link>
            </Button>
          }
          className="py-8"
        />
      );
    }

    if (showTable) {
      return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Formato</TableHead>
              <TableHead>Por defecto</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {profiles.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.name}</TableCell>
                <TableCell>{parserLabel(p.parser_key)}</TableCell>
                <TableCell>{p.is_default && <Badge variant="success">Sí</Badge>}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    }

    return <ImportProfileCardList profiles={profiles} />;
  }

  return (
    <div>
      <PageHeader
        title="Proveedores"
        description="Consulte los proveedores y sus perfiles de importación. Para importar una tarifa, vaya a Importar tarifa."
        icon={Truck}
      >
        <Button asChild className="min-h-11">
          <Link to="/import">Importar tarifa</Link>
        </Button>
      </PageHeader>

      {showSkeleton ? (
        <TwoColumnSkeleton />
      ) : fetchError ? (
        <ErrorState
          title="No se pudieron cargar los proveedores"
          description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
          action={
            <Button type="button" variant="secondary" className="min-h-11" onClick={loadSuppliers}>
              Reintentar
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {showMasterPanel ? (
            <Card className={cn(!showTable && detailView === "list" && "col-span-full")}>
              <CardHeader>
                <CardTitle>Proveedores</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {suppliers.length === 0 ? (
                  <EmptyState
                    icon={Truck}
                    title="Sin proveedores"
                    description="No hay proveedores configurados en el sistema."
                    className="py-8"
                  />
                ) : (
                  <div className="space-y-2" role="group" aria-label="Lista de proveedores">
                    {suppliers.map((s) => (
                      <Button
                        key={s.id}
                        type="button"
                        aria-pressed={selected === s.id}
                        aria-controls="supplier-profiles-panel"
                        variant={selected === s.id ? "default" : "secondary"}
                        className="min-h-11 w-full justify-start"
                        onClick={() => handleSelectSupplier(s.id)}
                      >
                        {s.name} ({s.code})
                      </Button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}

          {showProfilesPanel ? (
            <Card
              id="supplier-profiles-panel"
              className={cn(!showTable && detailView === "profiles" && "col-span-full")}
            >
              <CardHeader className="space-y-3">
                {!showTable && detailView === "profiles" ? (
                  <Button
                    type="button"
                    variant="secondary"
                    className="min-h-11 w-fit gap-2"
                    onClick={() => setDetailView("list")}
                  >
                    <ArrowLeft className="h-4 w-4 shrink-0" aria-hidden="true" />
                    Proveedores
                  </Button>
                ) : null}
                <CardTitle>
                  {selectedSupplier
                    ? `Perfiles de ${selectedSupplier.name}`
                    : "Perfiles de importación"}
                </CardTitle>
              </CardHeader>
              <CardContent>{renderProfilesContent()}</CardContent>
            </Card>
          ) : null}
        </div>
      )}
    </div>
  );
}
