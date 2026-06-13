import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CatalogDetail, CatalogListItem } from "./api";
import {
  deleteCatalogCoverImage,
  deleteCatalogSectionCover,
  uploadCatalogCoverImage,
  upsertCatalogSectionCover,
} from "./api";

function mockJsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
  } as Response;
}

function mockNoContentResponse(): Response {
  return {
    ok: true,
    status: 204,
    headers: new Headers(),
  } as Response;
}

describe("catalog cover API helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uploadCatalogCoverImage sends multipart FormData to cover-image endpoint", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        cover_image_path: "images/catalogs/cat-1/cover.png",
        cover_image_url: "/api/v1/media/images/catalogs/cat-1/cover.png",
      }),
    );

    const file = new File(["png"], "cover.png", { type: "image/png" });
    const result = await uploadCatalogCoverImage("cat-1", file);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/cat-1/cover-image");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBeInstanceOf(FormData);
    expect((init?.body as FormData).get("file")).toBe(file);
    expect(init?.headers).toBeUndefined();
    expect(result.cover_image_path).toContain("images/catalogs/cat-1/");
    expect(result.cover_image_url).toContain("/api/v1/media/");
  });

  it("deleteCatalogCoverImage calls DELETE on cover-image endpoint", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockNoContentResponse());

    await deleteCatalogCoverImage("cat-1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/cat-1/cover-image");
    expect(init?.method).toBe("DELETE");
  });

  it("upsertCatalogSectionCover includes description and file when provided", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        category_id: "cat-uuid",
        category_name: "Discos",
        cover_image_url: "/api/v1/media/section.png",
        description: "Con imagen",
      }),
    );

    const file = new File(["png"], "section.png", { type: "image/png" });
    const result = await upsertCatalogSectionCover("cat-1", "cat-uuid", {
      description: "Con imagen",
      file,
    });

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/cat-1/section-covers/cat-uuid");
    expect(init?.method).toBe("PUT");
    const fd = init?.body as FormData;
    expect(fd.get("description")).toBe("Con imagen");
    expect(fd.get("file")).toBe(file);
    expect(result.category_name).toBe("Discos");
  });

  it("upsertCatalogSectionCover supports description-only update", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        category_id: "cat-uuid",
        category_name: "Discos",
        cover_image_url: null,
        description: "Solo texto",
      }),
    );

    await upsertCatalogSectionCover("cat-1", "cat-uuid", {
      description: "Solo texto",
    });

    const fd = mockFetch.mock.calls[0][1]?.body as FormData;
    expect(fd.get("description")).toBe("Solo texto");
    expect(fd.get("file")).toBeNull();
  });

  it("deleteCatalogSectionCover calls DELETE on section-covers endpoint", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockNoContentResponse());

    await deleteCatalogSectionCover("cat-1", "cat-uuid");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/cat-1/section-covers/cat-uuid");
    expect(init?.method).toBe("DELETE");
  });

  it("CatalogDetail and CatalogListItem include cover fields", () => {
    const listItem: CatalogListItem = {
      id: "1",
      name: "Test",
      default_markup_percent: "10",
      cover_image_url: null,
      cover_subtitle: "Edición 2026",
    };
    const detail: CatalogDetail = {
      id: "1",
      name: "Test",
      default_markup_percent: "10",
      show_iva_column: false,
      show_description_column: true,
      cover_image_url: "/api/v1/media/cover.jpg",
      cover_subtitle: "Edición 2026",
      layout_mode: "automatic",
      uniform_layout_id: null,
      product_layouts: [],
      section_covers: [
        {
          category_id: "c1",
          category_name: "Discos",
          cover_image_url: null,
          description: "Sección",
        },
      ],
      items: [],
    };
    expect(listItem.cover_subtitle).toBe("Edición 2026");
    expect(detail.section_covers).toHaveLength(1);
    expect(detail.cover_image_url).toContain("cover.jpg");
  });
});
