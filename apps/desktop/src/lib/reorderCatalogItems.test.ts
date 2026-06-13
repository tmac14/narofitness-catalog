import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { reorderCatalogItems } from "./api";

function mockJsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
  } as Response;
}

describe("reorderCatalogItems", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends PATCH with items payload", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse({ updated: 3 }));

    const items = [
      { id: "a", sort_order: 0 },
      { id: "b", sort_order: 1 },
      { id: "c", sort_order: 2 },
    ];
    const result = await reorderCatalogItems("catalog-1", items);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/catalog-1/items/reorder");
    expect(init?.method).toBe("PATCH");
    expect(JSON.parse(init?.body as string)).toEqual({ items });
    expect(result.updated).toBe(3);
  });

  it("handles empty items list", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse({ updated: 0 }));

    const result = await reorderCatalogItems("catalog-1", []);
    expect(result.updated).toBe(0);
    expect(JSON.parse(mockFetch.mock.calls[0][1]?.body as string)).toEqual({ items: [] });
  });
});
