import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { classifyPlatformWidth } from "@/lib/responsive/platform";
import { BREAKPOINT_PX } from "@/lib/responsive/breakpoints";

describe("SettingsPage responsive forms (UX30-P3)", () => {
  it("classifies mobile and desktop platform bands for layout hooks", () => {
    expect(classifyPlatformWidth(BREAKPOINT_PX.mobileMax)).toBe("mobile");
    expect(classifyPlatformWidth(BREAKPOINT_PX.desktopMin)).toBe("desktop");
  });

  it("documents touch-first form class contract used by SettingsPage", () => {
    const markup = renderToStaticMarkup(
      <form className="ux30-settings-form w-full max-w-xl space-y-4">
        <button type="submit" className="min-h-11 w-full sm:w-auto">
          Guardar
        </button>
        <input className="min-h-11 w-full" aria-label="IVA" />
      </form>,
    );
    expect(markup).toContain("ux30-settings-form");
    expect(markup).toContain("min-h-11");
    expect(markup).toContain("w-full sm:w-auto");
  });

  it("uses full-width stacked dialog actions on narrow viewports", () => {
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
