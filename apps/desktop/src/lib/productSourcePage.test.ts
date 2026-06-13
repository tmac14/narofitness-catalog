import { describe, expect, it } from "vitest";
import {
  canonicalSourcePageFields,
  formatProductSourcePageLabel,
  formatProductSourcePageOriginMenuLabel,
  formatProductSourcePagePopoverBody,
  getCanonicalSourcePage,
  getProductSourcePageLabel,
  getProductSourcePageOriginMenuLabel,
  getProductSourcePagePopoverBody,
  normalizeProductSourcePageFields,
  normalizeSourcePages,
} from "./productSourcePage";

describe("normalizeSourcePages", () => {
  it("returns empty for missing or empty input", () => {
    expect(normalizeSourcePages(undefined)).toEqual([]);
    expect(normalizeSourcePages(null)).toEqual([]);
    expect(normalizeSourcePages([])).toEqual([]);
  });

  it("deduplicates, sorts ascending and drops nulls", () => {
    expect(normalizeSourcePages([40, 38, 39, 38, null, undefined])).toEqual([38, 39, 40]);
  });
});

describe("canonicalSourcePageFields", () => {
  it("returns null canonical page for empty input", () => {
    expect(canonicalSourcePageFields([])).toEqual({
      source_page: null,
      source_pages: [],
    });
  });

  it("returns canonical page for a single page", () => {
    expect(canonicalSourcePageFields([38])).toEqual({
      source_page: 38,
      source_pages: [38],
    });
  });

  it("returns null canonical page for multiple pages", () => {
    expect(canonicalSourcePageFields([38, 39])).toEqual({
      source_page: null,
      source_pages: [38, 39],
    });
  });
});

describe("normalizeProductSourcePageFields", () => {
  it("derives canonical fields from source_pages and ignores stale source_page", () => {
    expect(
      normalizeProductSourcePageFields({
        source_page: 38,
        source_pages: [38, 40],
      }),
    ).toEqual({
      source_page: null,
      source_pages: [38, 40],
    });
  });

  it("falls back to lone source_page for fixture data without pages array", () => {
    expect(
      normalizeProductSourcePageFields({
        source_page: 38,
        source_pages: [],
      }),
    ).toEqual({
      source_page: 38,
      source_pages: [38],
    });
  });
});

describe("getCanonicalSourcePage", () => {
  it("returns null when no pages exist", () => {
    expect(getCanonicalSourcePage({ source_page: null, source_pages: [] })).toBeNull();
  });

  it("returns the page when exactly one exists", () => {
    expect(getCanonicalSourcePage({ source_page: 38, source_pages: [38] })).toBe(38);
  });

  it("returns null for multiple pages", () => {
    expect(getCanonicalSourcePage({ source_page: null, source_pages: [38, 40] })).toBeNull();
  });
});

describe("formatProductSourcePageLabel", () => {
  it("returns null for empty pages", () => {
    expect(formatProductSourcePageLabel([])).toBeNull();
    expect(formatProductSourcePageLabel(undefined)).toBeNull();
  });

  it("formats a single page", () => {
    expect(formatProductSourcePageLabel([38])).toBe("PDF p.38");
  });

  it("formats a contiguous range compactly", () => {
    expect(formatProductSourcePageLabel([38, 39, 40])).toBe("PDF p.38–40");
  });

  it("formats non-contiguous pages without implying a range", () => {
    expect(formatProductSourcePageLabel([38, 40])).toBe("PDF p.38, 40");
  });

  it("normalizes duplicates and order before formatting", () => {
    expect(formatProductSourcePageLabel([40, 38, 39, 38])).toBe("PDF p.38–40");
    expect(formatProductSourcePageLabel([40, 38, 40])).toBe("PDF p.38, 40");
  });
});

describe("getProductSourcePageLabel", () => {
  it("formats from normalized API fields", () => {
    expect(
      getProductSourcePageLabel({
        source_page: 38,
        source_pages: [38],
      }),
    ).toBe("PDF p.38");

    expect(
      getProductSourcePageLabel({
        source_page: null,
        source_pages: [38, 40],
      }),
    ).toBe("PDF p.38, 40");
  });
});

describe("formatProductSourcePageOriginMenuLabel", () => {
  it("returns null for empty pages", () => {
    expect(formatProductSourcePageOriginMenuLabel([])).toBeNull();
  });

  it("formats a single page for the actions menu", () => {
    expect(formatProductSourcePageOriginMenuLabel([30])).toBe("Origen PDF: página 30");
  });

  it("formats contiguous multi-page ranges", () => {
    expect(formatProductSourcePageOriginMenuLabel([38, 39, 40])).toBe("Origen PDF: páginas 38–40");
  });

  it("formats non-contiguous pages without implying a range", () => {
    expect(formatProductSourcePageOriginMenuLabel([38, 40])).toBe("Origen PDF: páginas 38, 40");
  });
});

describe("getProductSourcePageOriginMenuLabel", () => {
  it("formats from normalized API fields", () => {
    expect(
      getProductSourcePageOriginMenuLabel({
        source_page: 38,
        source_pages: [38],
      }),
    ).toBe("Origen PDF: página 38");
  });
});

describe("formatProductSourcePagePopoverBody", () => {
  it("returns null for empty pages", () => {
    expect(formatProductSourcePagePopoverBody([])).toBeNull();
    expect(formatProductSourcePagePopoverBody(undefined)).toBeNull();
  });

  it("formats a single page for the popover body", () => {
    expect(formatProductSourcePagePopoverBody([30])).toBe("Página 30");
  });

  it("formats contiguous multi-page ranges", () => {
    expect(formatProductSourcePagePopoverBody([38, 39, 40])).toBe("Páginas 38–40");
  });

  it("formats non-contiguous pages without implying a range", () => {
    expect(formatProductSourcePagePopoverBody([38, 40])).toBe("Páginas 38, 40");
  });
});

describe("getProductSourcePagePopoverBody", () => {
  it("formats from normalized API fields", () => {
    expect(
      getProductSourcePagePopoverBody({
        source_page: 38,
        source_pages: [38],
      }),
    ).toBe("Página 38");
  });
});
