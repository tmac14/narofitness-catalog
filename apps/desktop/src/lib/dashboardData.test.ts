import { describe, expect, it } from "vitest";
import type { CatalogListItem, JobOut } from "./api";
import {
  buildKpiSnapshot,
  buildRecentMovements,
  catalogsWithoutCover,
  formatDashboardGreeting,
  formatDashboardTimestamp,
  generalStatusSummary,
  getActionableRecommendations,
  getDashboardEmptyState,
  getPrimaryDashboardAction,
  recentCatalogs,
  recentPriceLists,
  shouldShowDashboardSidebar,
  shouldShowProcessModule,
  shouldShowSystemAlert,
} from "./dashboardData";

function makeCatalog(overrides: Partial<CatalogListItem> = {}): CatalogListItem {
  return {
    id: "cat-1",
    name: "Catálogo verano",
    default_markup_percent: "20",
    cover_image_url: "https://example.com/cover.jpg",
    ...overrides,
  };
}

function makeJob(overrides: Partial<JobOut> = {}): JobOut {
  return {
    id: "job-1",
    job_type: "catalog_export_pdf",
    status: "succeeded",
    progress_percent: null,
    message: null,
    error_message: null,
    catalog_id: "cat-1",
    catalog_name: "Catálogo verano",
    created_at: "2026-06-01T10:00:00Z",
    started_at: null,
    finished_at: null,
    download_available: false,
    can_cancel: false,
    metadata: {},
    ...overrides,
  };
}

describe("catalogsWithoutCover", () => {
  it("returns catalogs missing cover_image_url", () => {
    const catalogs = [
      makeCatalog({ id: "1", cover_image_url: "https://x.test/a.jpg" }),
      makeCatalog({ id: "2", cover_image_url: null }),
      makeCatalog({ id: "3", cover_image_url: "   " }),
    ];
    expect(catalogsWithoutCover(catalogs).map((c) => c.id)).toEqual(["2", "3"]);
  });
});

describe("buildKpiSnapshot", () => {
  it("maps four operational counts", () => {
    expect(
      buildKpiSnapshot({
        productsTotal: 120,
        catalogsCount: 4,
        priceListsCount: 2,
        categoriesCount: 18,
      }),
    ).toEqual({
      products: 120,
      catalogs: 4,
      priceLists: 2,
      categories: 18,
    });
  });
});

describe("formatDashboardGreeting", () => {
  it("returns morning greeting before noon", () => {
    expect(formatDashboardGreeting(new Date("2026-06-07T08:00:00"))).toBe("Buenos días");
  });

  it("returns evening greeting after 20h", () => {
    expect(formatDashboardGreeting(new Date("2026-06-07T21:00:00"))).toBe("Buenas noches");
  });
});

describe("getPrimaryDashboardAction", () => {
  it("prioritizes catalog creation when empty", () => {
    const actions = getPrimaryDashboardAction({ hasCatalogs: false });
    expect(actions.primary).toMatchObject({ label: "Crear catálogo", to: "/catalogs" });
    expect(actions.secondary).toMatchObject({ label: "Importar tarifa", to: "/import" });
  });

  it("opens catalogs when they exist", () => {
    const actions = getPrimaryDashboardAction({ hasCatalogs: true });
    expect(actions.primary).toMatchObject({ label: "Abrir catálogos", to: "/catalogs" });
  });
});

describe("getDashboardEmptyState", () => {
  it("returns onboarding state without catalogs", () => {
    expect(getDashboardEmptyState({ hasCatalogs: false })?.title).toBe("Cree su primer catálogo");
  });

  it("returns null when catalogs exist", () => {
    expect(getDashboardEmptyState({ hasCatalogs: true })).toBeNull();
  });

  it("returns null on catalog load error", () => {
    expect(getDashboardEmptyState({ hasCatalogs: false, catalogsError: true })).toBeNull();
  });
});

describe("shouldShowSystemAlert", () => {
  it("is false when system is healthy", () => {
    expect(
      shouldShowSystemAlert({
        connected: true,
        pdfEngine: "playwright",
        pdfEngineError: null,
        jobsError: null,
      }),
    ).toBe(false);
  });

  it("is true when disconnected", () => {
    expect(
      shouldShowSystemAlert({
        connected: false,
        pdfEngine: null,
        pdfEngineError: null,
        jobsError: null,
      }),
    ).toBe(true);
  });

  it("is true when PDF engine is missing", () => {
    expect(
      shouldShowSystemAlert({
        connected: true,
        pdfEngine: null,
        pdfEngineError: null,
        jobsError: null,
      }),
    ).toBe(true);
  });
});

describe("shouldShowProcessModule", () => {
  it("is false without active or failed terminal jobs", () => {
    expect(
      shouldShowProcessModule({
        activeJobsCount: 0,
        recentTerminalFailed: false,
      }),
    ).toBe(false);
  });

  it("is true with active jobs", () => {
    expect(
      shouldShowProcessModule({
        activeJobsCount: 1,
        recentTerminalFailed: false,
      }),
    ).toBe(true);
  });

  it("is true with failed terminal job", () => {
    expect(
      shouldShowProcessModule({
        activeJobsCount: 0,
        recentTerminalFailed: true,
      }),
    ).toBe(true);
  });
});

describe("shouldShowDashboardSidebar", () => {
  it("is false when nothing actionable exists", () => {
    expect(
      shouldShowDashboardSidebar({
        recommendations: [],
        showSystemAlert: false,
        showProcessModule: false,
      }),
    ).toBe(false);
  });

  it("is true when process module is visible", () => {
    expect(
      shouldShowDashboardSidebar({
        recommendations: [],
        showSystemAlert: false,
        showProcessModule: true,
      }),
    ).toBe(true);
  });
});

describe("getActionableRecommendations", () => {
  it("returns empty list without catalogs", () => {
    expect(
      getActionableRecommendations({
        catalogs: [],
        hasCatalogs: false,
        priceListsCount: 0,
      }),
    ).toEqual([]);
  });

  it("warns about catalogs without cover", () => {
    const items = getActionableRecommendations({
      catalogs: [makeCatalog({ cover_image_url: null })],
      hasCatalogs: true,
      priceListsCount: 1,
    });
    expect(items.some((item) => item.id === "catalogs-no-cover")).toBe(true);
  });

  it("does not repeat empty catalog onboarding", () => {
    const items = getActionableRecommendations({
      catalogs: [],
      hasCatalogs: false,
      priceListsCount: 0,
    });
    expect(items).toHaveLength(0);
  });
});

describe("buildRecentMovements", () => {
  it("builds compact movement rows from latest sources", () => {
    const movements = buildRecentMovements({
      priceLists: [
        {
          id: "pl-1",
          source_filename: "tarifa.pdf",
          imported_at: "2026-06-01T10:00:00Z",
        },
      ],
      jobs: [makeJob({ status: "running", progress_percent: 40 })],
      catalogs: [makeCatalog({ id: "cat-1", name: "Verano" })],
    });
    expect(movements.map((m) => m.kind)).toEqual(["price_list", "job", "catalog"]);
    expect(movements[2].href).toBe("/catalogs/cat-1");
  });
});

describe("recentPriceLists", () => {
  it("sorts by imported_at descending and limits", () => {
    const lists = [
      { id: "a", imported_at: "2026-01-01T00:00:00Z", source_filename: "a.pdf" },
      { id: "b", imported_at: "2026-03-01T00:00:00Z", source_filename: "b.pdf" },
    ];
    expect(recentPriceLists(lists, 1).map((l) => l.id)).toEqual(["b"]);
  });
});

describe("recentCatalogs", () => {
  it("returns first N catalogs from API order", () => {
    const catalogs = [makeCatalog({ id: "1" }), makeCatalog({ id: "2" }), makeCatalog({ id: "3" })];
    expect(recentCatalogs(catalogs, 2).map((c) => c.id)).toEqual(["1", "2"]);
  });
});

describe("formatDashboardTimestamp", () => {
  it("returns dash for invalid dates", () => {
    expect(formatDashboardTimestamp("not-a-date")).toBe("—");
  });
});

describe("generalStatusSummary", () => {
  it("prioritizes disconnected state", () => {
    expect(
      generalStatusSummary({
        connected: false,
        hasPriceLists: true,
        hasCatalogs: true,
      }),
    ).toContain("Sin conexión");
  });

  it("guides catalog creation when empty", () => {
    expect(
      generalStatusSummary({
        connected: true,
        hasPriceLists: false,
        hasCatalogs: false,
      }),
    ).toContain("catálogo");
  });
});
