import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, Eye, FileDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CATALOG_PDF_EXPORT_PREPARING_LABEL } from "@/lib/catalogExportJob";
import { cn } from "@/lib/utils";

type Props = {
  catalogName: string;
  productCount: number;
  showPreview: boolean;
  exportingPdf: boolean;
  exportWarnings?: number;
  /** When true, Preview/Export are registered in the top bar — hide duplicates from tablet up. */
  hideInlineRouteActions?: boolean;
  onTogglePreview: () => void;
  onExportPdf: () => void;
};

export function CatalogEditorHeader({
  catalogName,
  productCount,
  showPreview,
  exportingPdf,
  exportWarnings = 0,
  hideInlineRouteActions = false,
  onTogglePreview,
  onExportPdf,
}: Props) {
  return (
    <div
      className={cn(
        "catalog-editor-header -mx-1 mb-6 rounded-lg border border-border bg-background/95 px-1 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80",
        !showPreview && "catalog-editor-header--sticky",
      )}
    >
      {!showPreview ? (
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2">
          <Link to="/catalogs">
            <ArrowLeft className="h-4 w-4" />
            Catálogos
          </Link>
        </Button>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <BookOpen className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold tracking-tight sm:text-2xl">
              {catalogName}
            </h1>
            <p className="text-sm text-muted-foreground">
              {showPreview ? "Modo vista previa" : "Builder de catálogo"} · {productCount} líneas
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {showPreview ? (
            <Button type="button" variant="secondary" asChild>
              <Link to="/catalogs">
                <ArrowLeft className="h-4 w-4" />
                Volver a catálogos
              </Link>
            </Button>
          ) : (
            <>
              {exportWarnings > 0 && (
                <Badge variant="warning" className="hidden sm:inline-flex">
                  {exportWarnings} avisos exportación
                </Badge>
              )}
              <div
                className={cn(
                  "flex flex-wrap items-center gap-2",
                  hideInlineRouteActions && "sm:hidden",
                )}
                data-testid="catalog-editor-header-route-actions"
              >
                <Button type="button" variant="secondary" onClick={onTogglePreview}>
                  <Eye className="h-4 w-4" />
                  Vista previa
                </Button>
                <Button type="button" disabled={exportingPdf} onClick={onExportPdf}>
                  <FileDown className="h-4 w-4" />
                  {exportingPdf ? CATALOG_PDF_EXPORT_PREPARING_LABEL : "Exportar PDF"}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
