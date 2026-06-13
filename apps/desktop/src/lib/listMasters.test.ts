import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getMaster, listMasters } from "./api";

function mockJsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
  } as Response;
}

describe("listMasters", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("builds query string with q, page, and page_size", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        items: [
          {
            id: "1",
            name: "Test",
            brand: null,
            category_id: null,
            master_key: null,
            notes: null,
            variant_count: 1,
          },
        ],
        total: 1,
        page: 2,
        page_size: 25,
      }),
    );

    const result = await listMasters({ q: "foo", page: 2, page_size: 25 });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/product-masters?");
    expect(url).toContain("q=foo");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=25");
    expect(result.page).toBe(2);
    expect(result.page_size).toBe(25);
    expect(result.total).toBe(1);
    expect(result.items).toHaveLength(1);
  });

  it("omits empty q param", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({ items: [], total: 0, page: 1, page_size: 50 }),
    );

    await listMasters({ page: 1, page_size: 50 });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("page=1");
    expect(url).toContain("page_size=50");
    expect(url).not.toContain("q=");
  });

  it("calls endpoint without query when no params", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({ items: [], total: 0, page: 1, page_size: 50 }),
    );

    await listMasters();

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toMatch(/\/product-masters$/);
  });

  it("parses source_page and source_pages on master and list variants", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        items: [
          {
            id: "master-1",
            name: "Test",
            brand: null,
            category_id: null,
            master_key: null,
            notes: null,
            variant_count: 2,
            references: [],
            price: null,
            variant_columns: [],
            source_page: null,
            source_pages: [38, 40],
            variants: [
              {
                id: "v1",
                sku: "SKU-1",
                display_name: null,
                reference_label: null,
                price: null,
                image_url: null,
                brand: null,
                brand_display: null,
                variant_label: null,
                attributes: {},
                source_page: 38,
                source_pages: [38],
              },
              {
                id: "v2",
                sku: "SKU-2",
                display_name: null,
                reference_label: null,
                price: null,
                image_url: null,
                brand: null,
                brand_display: null,
                variant_label: null,
                attributes: {},
                source_page: null,
                source_pages: [40],
              },
            ],
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }),
    );

    const result = await listMasters();

    const master = result.items[0];
    expect(master.source_page).toBeNull();
    expect(master.source_pages).toEqual([38, 40]);
    expect(master.variants[0].source_page).toBe(38);
    expect(master.variants[0].source_pages).toEqual([38]);
    expect(master.variants[1].source_page).toBeNull();
    expect(master.variants[1].source_pages).toEqual([40]);
  });
});

describe("getMaster", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses source_page and source_pages on detail master and variants", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        id: "master-1",
        name: "Test",
        brand: null,
        category_id: null,
        master_key: null,
        notes: null,
        variant_count: 1,
        references: [],
        price: null,
        variant_columns: [],
        images: [],
        source_page: 38,
        source_pages: [38],
        variants: [
          {
            id: "v1",
            product_master_id: "master-1",
            supplier_id: "sup-1",
            sku: "SKU-1",
            ean: null,
            display_name: null,
            specs: [],
            latest_price: null,
            source_page: 38,
            source_pages: [38],
          },
        ],
      }),
    );

    const result = await getMaster("master-1");

    expect(result.source_page).toBe(38);
    expect(result.source_pages).toEqual([38]);
    expect(result.variants[0].source_page).toBe(38);
    expect(result.variants[0].source_pages).toEqual([38]);

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/product-masters/master-1");
  });
});
