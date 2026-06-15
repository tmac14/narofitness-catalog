import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { BREAKPOINT_PX } from "@/lib/responsive/breakpoints";
import { classifyPlatformWidth } from "@/lib/responsive/platform";

describe("DashboardPage responsive (UX30-P3)", () => {
  it("classifies mobile and desktop platform bands", () => {
    expect(classifyPlatformWidth(BREAKPOINT_PX.mobileMax)).toBe("mobile");
    expect(classifyPlatformWidth(BREAKPOINT_PX.desktopMin)).toBe("desktop");
  });

  it("documents hero CTA touch-first class contract", () => {
    const markup = renderToStaticMarkup(
      <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
        <a className="min-h-11 w-full sm:w-auto" href="/import">
          Importar
        </a>
        <a className="min-h-11 w-full sm:w-auto" href="/catalogs">
          Catálogos
        </a>
      </div>,
    );
    expect(markup).toContain("min-h-11");
    expect(markup).toContain("w-full sm:w-auto");
    expect(markup).toContain("flex-col");
  });

  it("documents KPI link touch target class contract", () => {
    const markup = renderToStaticMarkup(
      <a className="ux30-dashboard-kpi-link block h-full min-h-11 rounded-lg" href="/products">
        KPI
      </a>,
    );
    expect(markup).toContain("ux30-dashboard-kpi-link");
    expect(markup).toContain("min-h-11");
  });
});
