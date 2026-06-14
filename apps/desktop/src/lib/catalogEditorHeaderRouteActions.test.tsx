import type { ComponentProps } from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router-dom/server";
import { CatalogEditorHeader } from "@/components/catalog-builder/CatalogEditorHeader";

const baseProps = {
  catalogName: "Catálogo demo",
  productCount: 12,
  showPreview: false,
  exportingPdf: false,
  onTogglePreview: () => {},
  onExportPdf: () => {},
};

function renderHeader(props: ComponentProps<typeof CatalogEditorHeader>) {
  return renderToStaticMarkup(
    <StaticRouter location="/catalogs/demo">
      <CatalogEditorHeader {...props} />
    </StaticRouter>,
  );
}

describe("CatalogEditorHeader route action dedupe", () => {
  it("shows inline Preview and Export when top-bar dedupe is off", () => {
    const html = renderHeader({ ...baseProps, hideInlineRouteActions: false });
    expect(html).toContain("Vista previa");
    expect(html).toContain("Exportar PDF");
    expect(html).not.toContain("sm:hidden");
  });

  it("hides inline Preview and Export from tablet up when top-bar actions are active", () => {
    const html = renderHeader({ ...baseProps, hideInlineRouteActions: true });
    expect(html).toContain("Vista previa");
    expect(html).toContain("Exportar PDF");
    expect(html).toContain("sm:hidden");
    expect(html).toContain('data-testid="catalog-editor-header-route-actions"');
  });

  it("keeps export warnings badge visible when inline route actions are deduped", () => {
    const html = renderHeader({
      ...baseProps,
      hideInlineRouteActions: true,
      exportWarnings: 3,
    });
    expect(html).toContain("3 avisos exportación");
  });

  it("shows back navigation in preview mode instead of builder route actions", () => {
    const html = renderHeader({
      ...baseProps,
      showPreview: true,
      hideInlineRouteActions: false,
    });
    expect(html).toContain("Volver a catálogos");
    expect(html).not.toContain("Exportar PDF");
    expect(html).toContain("Modo vista previa");
  });
});
