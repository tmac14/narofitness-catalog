import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { ImportProfile } from "@/lib/api";
import { ImportProfileCard } from "@/components/suppliers/ImportProfileCard";
import { ImportProfileCardList } from "@/components/suppliers/ImportProfileCardList";
import {
  SUPPLIERS_PROFILES_VIEW_POLICY,
  computeDataViewModeFromWidth,
} from "@/hooks/useDataViewMode";

function makeProfile(overrides: Partial<ImportProfile> = {}): ImportProfile {
  return {
    id: "profile-1",
    supplier_id: "supplier-1",
    slug: "fdl-default",
    name: "Perfil FDL",
    parser_key: "fdl_pdf",
    is_default: true,
    ...overrides,
  };
}

describe("SuppliersPage responsive cards", () => {
  it("renders ImportProfileCard with BEM classes and no table markup", () => {
    const html = renderToStaticMarkup(
      <ImportProfileCard profile={makeProfile()} index={0} />,
    );
    expect(html).toContain("responsive-data-card");
    expect(html).toContain("Perfil FDL");
    expect(html).toContain("PDF FDL");
    expect(html).not.toContain("<table");
  });

  it("renders ImportProfileCardList with name, formato, and default badge", () => {
    const html = renderToStaticMarkup(
      <ImportProfileCardList
        profiles={[
          makeProfile(),
          makeProfile({
            id: "profile-2",
            name: "Perfil genérico",
            parser_key: "generic_pdf",
            is_default: false,
          }),
        ]}
      />,
    );
    expect(html).toContain("responsive-data-card-list__items");
    expect(html).toContain("Perfil FDL");
    expect(html).toContain("PDF genérico");
    expect(html).toContain("Sí");
    expect(html).not.toContain("<table");
  });

  it("maps suppliers profiles policy to cards below desktop and table at desktop+", () => {
    for (const width of [360, 640, 1023]) {
      expect(computeDataViewModeFromWidth(width, SUPPLIERS_PROFILES_VIEW_POLICY).showCards).toBe(
        true,
      );
    }
    expect(computeDataViewModeFromWidth(1024, SUPPLIERS_PROFILES_VIEW_POLICY).showTable).toBe(
      true,
    );
  });
});
