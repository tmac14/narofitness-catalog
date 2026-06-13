import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createMasterImageFromUrl,
  createVariantImageFromUrl,
  isExternalProductImage,
  type ProductImage,
} from "./api";

function mockJsonResponse(body: unknown): Response {
  return {
    ok: true,
    status: 201,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
  } as Response;
}

function externalUrlImage(overrides: Partial<ProductImage> = {}): ProductImage {
  return {
    id: "img-ext-1",
    url: "/api/v1/media/images/master-1/abc.jpg",
    is_primary: true,
    status: "confirmed",
    variant_id: null,
    source_type: "external_url",
    external_url: "https://example.com/product.jpg",
    ...overrides,
  };
}

describe("createMasterImageFromUrl", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs url body to master from-url endpoint", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse(externalUrlImage()));

    const result = await createMasterImageFromUrl(
      "master-1",
      "  https://example.com/product.jpg  ",
    );

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/product-masters/master-1/images/from-url");
    expect(init?.method).toBe("POST");
    expect(init?.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(typeof init?.body).toBe("string");
    expect(JSON.parse(init?.body as string)).toEqual({ url: "https://example.com/product.jpg" });
    expect(result.source_type).toBe("external_url");
    expect(result.external_url).toBe("https://example.com/product.jpg");
    expect(isExternalProductImage(result)).toBe(true);
  });
});

describe("createVariantImageFromUrl", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("defaults to backend set_primary=true without query param", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse(
        externalUrlImage({
          variant_id: "variant-1",
          url: "/api/v1/media/images/master-1/var.jpg",
        }),
      ),
    );

    await createVariantImageFromUrl("variant-1", "https://example.com/product.jpg");

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/product-variants/variant-1/images/from-url");
    expect(url).not.toContain("set_primary");
  });

  it("passes set_primary=false when setPrimary option is false", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse(
        externalUrlImage({
          variant_id: "variant-1",
          is_primary: false,
        }),
      ),
    );

    await createVariantImageFromUrl("variant-1", "https://example.com/product.jpg", {
      setPrimary: false,
    });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("set_primary=false");
  });

  it("returns external_url contract fields", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse(externalUrlImage({ variant_id: "variant-1" })),
    );

    const result = await createVariantImageFromUrl("variant-1", "https://example.com/product.jpg");

    expect(result).toMatchObject({
      source_type: "external_url",
      external_url: "https://example.com/product.jpg",
      status: "confirmed",
    });
  });
});

describe("isExternalProductImage", () => {
  it("distinguishes upload images", () => {
    const upload: ProductImage = {
      ...externalUrlImage(),
      source_type: "upload",
      external_url: null,
    };
    expect(isExternalProductImage(upload)).toBe(false);
  });
});
