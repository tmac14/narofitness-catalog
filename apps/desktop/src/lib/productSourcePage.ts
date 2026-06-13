export type ProductSourcePageFields = {
  source_page: number | null;
  source_pages: number[];
};

/** Distinct ascending PDF page numbers; nulls, duplicates and non-finite values removed. */
export function normalizeSourcePages(
  pages: readonly (number | null | undefined)[] | null | undefined,
): number[] {
  if (!pages?.length) return [];

  const distinct = new Set<number>();
  for (const page of pages) {
    if (page != null && Number.isFinite(page)) {
      distinct.add(page);
    }
  }

  return [...distinct].sort((a, b) => a - b);
}

/** Canonical fields from a page list; mirrors backend `canonical_source_page_fields`. */
export function canonicalSourcePageFields(
  pages: readonly (number | null | undefined)[] | null | undefined,
): ProductSourcePageFields {
  const source_pages = normalizeSourcePages(pages);
  const source_page = source_pages.length === 1 ? source_pages[0] : null;
  return { source_page, source_pages };
}

/**
 * Defensive normalization for API responses and local fixtures.
 * Canonical `source_page` is always derived from normalized `source_pages`.
 */
export function normalizeProductSourcePageFields(fields: {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
}): ProductSourcePageFields {
  const fromPages = normalizeSourcePages(fields.source_pages);
  if (fromPages.length > 0) {
    return canonicalSourcePageFields(fromPages);
  }

  const lonePage = fields.source_page;
  if (lonePage != null && Number.isFinite(lonePage)) {
    return canonicalSourcePageFields([lonePage]);
  }

  return { source_page: null, source_pages: [] };
}

/** Single canonical page only when exactly one distinct page exists. */
export function getCanonicalSourcePage(
  fields:
    | ProductSourcePageFields
    | {
        source_page?: number | null;
        source_pages?: readonly (number | null | undefined)[] | null;
      },
): number | null {
  const normalized =
    "source_pages" in fields && Array.isArray(fields.source_pages) && fields.source_pages.length > 0
      ? canonicalSourcePageFields(fields.source_pages)
      : normalizeProductSourcePageFields(fields);
  return normalized.source_page;
}

function isContiguousAscending(pages: number[]): boolean {
  if (pages.length <= 1) return true;
  for (let i = 1; i < pages.length; i++) {
    if (pages[i] !== pages[i - 1] + 1) return false;
  }
  return true;
}

function formatPageNumberSegment(pages: number[]): string {
  if (pages.length === 0) return "";
  if (pages.length === 1) return String(pages[0]);
  if (isContiguousAscending(pages)) {
    return `${pages[0]}–${pages[pages.length - 1]}`;
  }
  return pages.join(", ");
}

/** Human-readable PDF page label; null when no pages exist. */
export function formatProductSourcePageLabel(
  pages: readonly (number | null | undefined)[] | null | undefined,
): string | null {
  const normalized = normalizeSourcePages(pages);
  if (normalized.length === 0) return null;
  return `PDF p.${formatPageNumberSegment(normalized)}`;
}

/** Label from API/fixture fields after defensive normalization. */
export function getProductSourcePageLabel(fields: {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
}): string | null {
  return formatProductSourcePageLabel(normalizeProductSourcePageFields(fields).source_pages);
}

/** Actions-menu label for PDF origin; null when no pages exist. */
export function formatProductSourcePageOriginMenuLabel(
  pages: readonly (number | null | undefined)[] | null | undefined,
): string | null {
  const normalized = normalizeSourcePages(pages);
  if (normalized.length === 0) return null;

  const segment = formatPageNumberSegment(normalized);
  if (normalized.length === 1) {
    return `Origen PDF: página ${segment}`;
  }
  return `Origen PDF: páginas ${segment}`;
}

/** Actions-menu label from API/fixture fields after defensive normalization. */
export function getProductSourcePageOriginMenuLabel(fields: {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
}): string | null {
  return formatProductSourcePageOriginMenuLabel(
    normalizeProductSourcePageFields(fields).source_pages,
  );
}

/** Popover body text for PDF origin; null when no pages exist. */
export function formatProductSourcePagePopoverBody(
  pages: readonly (number | null | undefined)[] | null | undefined,
): string | null {
  const normalized = normalizeSourcePages(pages);
  if (normalized.length === 0) return null;

  const segment = formatPageNumberSegment(normalized);
  if (normalized.length === 1) {
    return `Página ${segment}`;
  }
  return `Páginas ${segment}`;
}

/** Popover body from API/fixture fields after defensive normalization. */
export function getProductSourcePagePopoverBody(fields: {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
}): string | null {
  return formatProductSourcePagePopoverBody(normalizeProductSourcePageFields(fields).source_pages);
}
