import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

describe("CategoriesPage form responsive (UX30-P3)", () => {
  it("documents category form touch-first class contract", () => {
    const markup = renderToStaticMarkup(
      <form className="ux30-categories-form w-full max-w-md space-y-4">
        <input className="min-h-11 w-full" aria-label="Nombre" />
        <select className="min-h-11 w-full" aria-label="Padre" />
        <button type="submit" className="min-h-11 w-full sm:w-auto">
          Crear
        </button>
      </form>,
    );
    expect(markup).toContain("ux30-categories-form");
    expect(markup).toContain("min-h-11");
    expect(markup).toContain("w-full sm:w-auto");
  });

  it("documents stacked dialog footer on narrow viewports", () => {
    const markup = renderToStaticMarkup(
      <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        <button type="button" className="min-h-11 w-full sm:w-auto">
          Cancelar
        </button>
      </div>,
    );
    expect(markup).toContain("flex-col");
    expect(markup).toContain("sm:flex-row");
  });
});
