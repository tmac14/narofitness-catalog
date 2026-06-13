import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Truck } from "lucide-react";
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

const PARSER_LABELS: Record<string, string> = {
  fdl_pdf: "PDF FDL",
  generic_pdf: "PDF genérico",
};

function parserLabel(key: string): string {
  return PARSER_LABELS[key] ?? key.replace(/_/g, " ");
}

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [profiles, setProfiles] = useState<ImportProfile[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [profilesError, setProfilesError] = useState(false);
  const showSkeleton = useDelayedLoading(loading);

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

  const selectedSupplier = suppliers.find((s) => s.id === selected);

  return (
    <div>
      <PageHeader
        title="Proveedores"
        description="Consulte los proveedores y sus perfiles de importación. Para importar una tarifa, vaya a Importar tarifa."
        icon={Truck}
      >
        <Button asChild size="sm">
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
            <Button type="button" size="sm" variant="secondary" onClick={loadSuppliers}>
              Reintentar
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
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
                      className="w-full justify-start"
                      onClick={() => setSelected(s.id)}
                    >
                      {s.name} ({s.code})
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card id="supplier-profiles-panel">
            <CardHeader>
              <CardTitle>
                {selectedSupplier
                  ? `Perfiles de ${selectedSupplier.name}`
                  : "Perfiles de importación"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {profilesError ? (
                <ErrorState
                  title="No se pudieron cargar los perfiles"
                  description="Compruebe la conexión e inténtelo de nuevo."
                  action={
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        setProfilesError(false);
                        void listImportProfiles(selected)
                          .then(setProfiles)
                          .catch(() => setProfilesError(true));
                      }}
                    >
                      Reintentar
                    </Button>
                  }
                  className="py-8"
                />
              ) : !selected ? (
                <EmptyState
                  icon={Truck}
                  title="Seleccione un proveedor"
                  description="Elija un proveedor de la lista de la izquierda para ver sus perfiles."
                  className="py-8"
                />
              ) : profiles.length === 0 ? (
                <EmptyState
                  icon={Truck}
                  title="Sin perfiles"
                  description={`El proveedor ${selectedSupplier?.name} no tiene perfiles de importación configurados.`}
                  action={
                    <Button asChild size="sm" variant="secondary">
                      <Link to="/import">Ir a importar tarifa</Link>
                    </Button>
                  }
                  className="py-8"
                />
              ) : (
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
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
