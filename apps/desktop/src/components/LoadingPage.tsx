import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

function BusyRegion({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div aria-busy="true" aria-label={label}>
      {children}
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <BusyRegion label="Cargando tabla">
      <div className="space-y-0 p-0 min-h-[var(--table-min-height,480px)]">
        <div className="border-b border-border px-3 py-2.5">
          <Skeleton className="h-4 w-full max-w-md" />
        </div>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="border-b border-border px-3 py-3">
            <Skeleton className="h-4 w-full" />
          </div>
        ))}
      </div>
    </BusyRegion>
  );
}

export function DashboardSkeleton() {
  return (
    <BusyRegion label="Cargando inicio">
      <Card className="dashboard-hero mb-6">
        <CardContent className="space-y-3 p-5 sm:p-6">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-7 w-40" />
          <Skeleton className="h-4 w-full max-w-xl" />
          <div className="flex gap-2 pt-1">
            <Skeleton className="h-8 w-28" />
            <Skeleton className="h-8 w-28" />
          </div>
        </CardContent>
      </Card>

      <div className="dashboard-kpi-grid mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="dashboard-kpi">
            <CardContent className="flex items-center gap-3 p-4">
              <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-7 w-12" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="dashboard-layout">
        <div className="dashboard-layout__main">
          <Card className="dashboard-overview">
            <CardContent className="space-y-6 p-5">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-5 w-36" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </BusyRegion>
  );
}

export function FormSkeleton() {
  return (
    <BusyRegion label="Cargando formulario">
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-36" />
        </CardHeader>
        <CardContent className="space-y-4 max-w-md">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-2/3" />
          <Skeleton className="h-9 w-24" />
        </CardContent>
      </Card>
    </BusyRegion>
  );
}

export function DetailSkeleton() {
  return <ProductDetailSkeleton />;
}

export function ProductDetailSkeleton() {
  return (
    <BusyRegion label="Cargando ficha de producto">
      <div className="space-y-6">
        <div className="rounded-lg border border-border bg-card p-5">
          <div className="flex gap-4">
            <Skeleton className="h-20 w-20 shrink-0 rounded-lg" />
            <div className="min-w-0 flex-1 space-y-3">
              <Skeleton className="h-7 w-2/3 max-w-md" />
              <div className="flex flex-wrap gap-2">
                <Skeleton className="h-6 w-16 rounded-md" />
                <Skeleton className="h-6 w-24 rounded-md" />
                <Skeleton className="h-6 w-20 rounded-md" />
              </div>
            </div>
            <div className="hidden shrink-0 gap-2 sm:flex">
              <Skeleton className="h-9 w-20" />
              <Skeleton className="h-9 w-32" />
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Skeleton className="h-9 w-32 rounded-md" />
          <Skeleton className="h-9 w-28 rounded-md" />
        </div>

        <div className="product-detail-grid">
          <div className="product-detail-grid__main space-y-6">
            <Card className="builder-panel">
              <CardHeader>
                <Skeleton className="h-5 w-36" />
                <Skeleton className="h-4 w-64" />
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <Skeleton className="h-9 w-full sm:col-span-2" />
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-24 w-full sm:col-span-2" />
              </CardContent>
            </Card>
            <Card className="builder-panel">
              <CardHeader>
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-lg" />
                ))}
              </CardContent>
            </Card>
          </div>
          <aside className="product-detail-grid__sidebar space-y-6">
            <Card className="builder-panel">
              <CardHeader>
                <Skeleton className="h-5 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-40 w-full rounded-lg" />
              </CardContent>
            </Card>
            <Card className="builder-panel">
              <CardHeader>
                <Skeleton className="h-5 w-20" />
              </CardHeader>
              <CardContent className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </BusyRegion>
  );
}

export function CatalogEditorSkeleton() {
  return (
    <BusyRegion label="Cargando editor de catálogo">
      <div className="space-y-4">
        <div className="flex gap-2">
          <Skeleton className="h-9 w-[5.5rem] rounded-md" />
          <Skeleton className="h-9 w-[6.5rem] rounded-md" />
          <Skeleton className="h-9 w-[5.5rem] rounded-md" />
        </div>
        <div className="editor-tab-panel">
          <Card className="builder-panel">
            <CardHeader>
              <Skeleton className="h-5 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-4">
                <Skeleton className="h-9 w-[240px]" />
                <Skeleton className="h-9 w-28" />
                <Skeleton className="h-5 w-48" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-9 w-32" />
                <Skeleton className="h-9 w-24" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </BusyRegion>
  );
}

export function TwoColumnSkeleton() {
  return (
    <BusyRegion label="Cargando contenido">
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <div className="space-y-0 p-0">
                {Array.from({ length: 4 }).map((_, j) => (
                  <div key={j} className="border-b border-border px-3 py-3">
                    <Skeleton className="h-4 w-full" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </BusyRegion>
  );
}
