import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function PresentationLoadingState() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando presentación del catálogo">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i} className="builder-stat-card">
            <CardContent className="pt-4 pb-4 space-y-2">
              <div className="h-3 w-20 rounded bg-muted animate-pulse" />
              <div className="h-8 w-14 rounded bg-muted animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="builder-panel min-h-[var(--table-min-height,480px)]">
        <CardContent className="py-16 flex flex-col items-center justify-center gap-4 text-center max-w-md mx-auto">
          <Loader2 className="h-7 w-7 animate-spin text-primary" aria-hidden="true" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground">
              Cargando asignaciones del catálogo…
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Este catálogo es grande; puede tardar unos segundos.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
