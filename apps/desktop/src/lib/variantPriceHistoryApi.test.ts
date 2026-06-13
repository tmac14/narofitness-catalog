import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getVariantPriceHistory } from "./api";

function mockJsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
  } as Response;
}

describe("getVariantPriceHistory", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses full current contract fields from API response", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        items: [
          {
            list_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            imported_at: "2026-03-15T10:30:00Z",
            effective_date: "2026-02-01",
            price_amount: "60.00",
            source_filename: "FDL_page14.pdf",
            delta_pct_vs_previous: "2.50",
          },
        ],
      }),
    );

    const result = await getVariantPriceHistory("variant-1");

    expect(result.items).toHaveLength(1);
    expect(result.items[0]).toEqual({
      list_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      imported_at: "2026-03-15T10:30:00Z",
      effective_date: "2026-02-01",
      price_amount: "60.00",
      source_filename: "FDL_page14.pdf",
      delta_pct_vs_previous: "2.50",
    });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/product-variants/variant-1/price-history");
  });
});
