function readWindowApiBase(): string | undefined {
  if (typeof window === "undefined") return undefined;
  return window.narocatalog?.apiBase;
}

function readEnvApiBase(): string | undefined {
  return typeof import.meta.env.VITE_API_BASE === "string"
    ? import.meta.env.VITE_API_BASE
    : undefined;
}

const API_BASE = readWindowApiBase() ?? readEnvApiBase() ?? "http://127.0.0.1:8000";

const V1 = `${API_BASE}/api/v1`;

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  if (!text) return res.statusText;
  try {
    const parsed = JSON.parse(text) as { detail?: string };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // plain text
  }
  return text;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${V1}${path}`, init);
  if (!res.ok) throw new Error(await readErrorMessage(res));
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const data: unknown = await res.json();
    return data as T;
  }
  return res as unknown as T;
}

export async function health() {
  return request<{
    status: string;
    version: string;
    pdf_engine?: string | null;
    pdf_engine_error?: string | null;
    pdf_engine_fallback?: string | null;
    pdf_engines_available?: string[];
  }>("/health");
}

// Suppliers
export type Supplier = {
  id: string;
  code: string;
  name: string;
  notes: string | null;
  is_active: boolean;
};
export type ImportProfile = {
  id: string;
  supplier_id: string;
  slug: string;
  name: string;
  parser_key: string;
  is_default: boolean;
};

export async function listSuppliers() {
  return request<Supplier[]>("/suppliers");
}

export async function listImportProfiles(supplierId: string) {
  return request<ImportProfile[]>(`/suppliers/${supplierId}/import-profiles`);
}

// Import
export type SpecValue = {
  id?: string | null;
  spec_definition_id: string;
  key: string;
  label: string;
  data_type: string;
  role?: string | null;
  value?: string | null;
  sort_order?: number;
};

export type ImportRow = {
  id: string;
  batch_id: string;
  source_row_index: number;
  row_index?: number;
  status: string | null;
  review_status: string;
  sku: string | null;
  name: string | null;
  raw_name?: string | null;
  normalized_name?: string | null;
  brand: string | null;
  ean: string | null;
  category_path: string | null;
  detected_category_path_raw?: string | null;
  mapped_category_id?: string | null;
  mapped_category_slug?: string | null;
  mapped_category_confidence?: number | null;
  price_amount: string | null;
  master_key?: string | null;
  master_name?: string | null;
  display_name?: string | null;
  reference_label?: string | null;
  grouping_confidence?: number | null;
  grouping_reason?: string | null;
  parsed_variant_specs_raw?: Record<string, unknown>;
  parsed_common_specs_raw?: Record<string, unknown>;
  import_action?: string;
  review_reasons?: string[];
  grouping_locked?: boolean;
};

export async function previewImport(file: File, supplierId: string, importProfileId: string) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("supplier_id", supplierId);
  fd.append("import_profile_id", importProfileId);
  return request<{
    batch_id: string;
    filename: string;
    total_rows: number;
    stats: Record<string, number>;
    action_stats: Record<string, number>;
    rows: ImportRow[];
  }>("/import/pdf/preview", { method: "POST", body: fd });
}

export async function confirmImport(body: {
  batch_id: string;
  supplier_id: string;
  import_profile_id: string;
  row_ids?: string[];
  effective_date?: string;
  allow_needs_review?: boolean;
}) {
  return request<{
    price_list_id: string;
    batch_id?: string;
    masters_created: number;
    variants_created: number;
    variants_updated: number;
    entries_created: number;
    rows_skipped?: number;
    rows_blocked?: number;
  }>("/import/pdf/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export type CanonicalCategoryNode = {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  full_path: string;
  level: number;
  children: CanonicalCategoryNode[];
};

export type SourceCategoryExampleRow = {
  sku: string | null;
  normalized_name: string | null;
  source_row_index: number;
};

export type SourceCategoryDiscovery = {
  source_category_path_raw: string;
  normalized_source_category_key: string;
  row_count: number;
  example_rows: SourceCategoryExampleRow[];
  currently_mapped_category_id: string | null;
  currently_mapped_category_slug: string | null;
  mapped_category_confidence: number | null;
  mapping_rule_id: string | null;
  mapping_status: "mapped" | "unmapped" | "ambiguous" | "ignored";
  requires_review: boolean;
  notes: string | null;
  proposed_category_id: string | null;
  proposed_category_slug: string | null;
  proposal_confidence: number;
  proposal_reason: string;
  proposal_source: string;
};

export async function getCanonicalCategoryTree() {
  return request<CanonicalCategoryNode[]>("/categories/canonical-tree");
}

export async function getBatchSourceCategories(batchId: string) {
  return request<{
    batch_id: string;
    supplier_id: string;
    import_profile_id: string | null;
    source_categories: SourceCategoryDiscovery[];
  }>(`/import/batches/${batchId}/source-categories`);
}

export async function confirmTaxonomyMapping(body: {
  supplier_id?: string;
  import_profile_id?: string;
  source_category_path_raw?: string;
  normalized_source_category_key?: string;
  target_category_id: string;
  confidence?: number;
  requires_review?: boolean;
  priority?: number;
  notes?: string;
}) {
  return request<{
    id: string;
    match_type: string;
    match_value: string;
    target_category_id: string | null;
    target_subcategory_id: string | null;
    confidence: number;
    requires_review: boolean;
    priority: number;
    notes: string | null;
  }>("/taxonomy-mapping-rules/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function ignoreSourceCategory(body: {
  supplier_id?: string;
  import_profile_id?: string;
  source_category_path_raw?: string;
  normalized_source_category_key?: string;
  notes?: string;
  priority?: number;
}) {
  return request<{
    id: string;
    match_type: string;
    match_value: string;
    notes: string | null;
  }>("/taxonomy-mapping-rules/ignore", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function remapBatchTaxonomy(batchId: string, includeRows = true) {
  return request<{
    batch_id: string;
    rows_updated: number;
    mapped_count: number;
    unmapped_count: number;
    ignored_count: number;
    rows: ImportRow[];
  }>(`/import/batches/${batchId}/remap-taxonomy?include_rows=${includeRows}`, {
    method: "POST",
  });
}

// Masters
export type BrandMode = "none" | "uniform" | "mixed";

export type VariantAttributeColumn = {
  key: string;
  label: string;
};

export type ProductMasterListVariant = {
  id: string;
  sku: string;
  display_name: string | null;
  reference_label: string | null;
  price: string | null;
  image_url: string | null;
  brand: string | null;
  brand_display: string | null;
  variant_label: string | null;
  attributes: Record<string, string | null>;
  source_page: number | null;
  source_pages: number[];
};

export type ProductMaster = {
  id: string;
  name: string;
  brand: string | null;
  brand_mode?: BrandMode;
  brand_display?: string | null;
  show_brand_column?: boolean;
  show_variant_name_column?: boolean;
  category_id: string | null;
  category_name?: string | null;
  category_parent_name?: string | null;
  category_sub_name?: string | null;
  image_url?: string | null;
  master_key: string | null;
  notes: string | null;
  variant_count: number;
  references: string[];
  price: string | null;
  variant_columns: VariantAttributeColumn[];
  variants: ProductMasterListVariant[];
  source_page: number | null;
  source_pages: number[];
};

export type ProductVariant = {
  id: string;
  product_master_id: string;
  supplier_id: string;
  supplier_code?: string | null;
  sku: string;
  ean: string | null;
  display_name: string | null;
  brand?: string | null;
  brand_display?: string | null;
  variant_label?: string | null;
  specs: SpecValue[];
  latest_price: string | null;
  master_name?: string | null;
  source_page: number | null;
  source_pages: number[];
};

export type ProductImageSourceType = "upload" | "external_url";

export type ProductImage = {
  id: string;
  url: string;
  is_primary: boolean;
  status: string;
  variant_id: string | null;
  source_type: ProductImageSourceType;
  external_url: string | null;
};

export function isExternalProductImage(image: ProductImage): boolean {
  return image.source_type === "external_url";
}

export type ProductMasterDetail = Omit<ProductMaster, "variants"> & {
  images: ProductImage[];
  specs?: SpecValue[];
  variants: (ProductVariant & { images?: ProductImage[] })[];
};

export type MasterSortKey = "name" | "reference" | "brand" | "category" | "price" | "variant_count";
export type SortDirection = "asc" | "desc";

export type MastersListParams = {
  q?: string;
  page?: number;
  page_size?: number;
  sort_by?: MasterSortKey;
  sort_dir?: SortDirection;
};

export type MastersListResponse = {
  items: ProductMaster[];
  total: number;
  page: number;
  page_size: number;
};

export async function listMasters(params?: MastersListParams) {
  const qs = new URLSearchParams();
  if (params?.q) qs.set("q", params.q);
  if (params?.page != null) qs.set("page", String(params.page));
  if (params?.page_size != null) qs.set("page_size", String(params.page_size));
  if (params?.sort_by) qs.set("sort_by", params.sort_by);
  if (params?.sort_dir) qs.set("sort_dir", params.sort_dir);
  const q = qs.toString();
  return request<MastersListResponse>(`/product-masters${q ? `?${q}` : ""}`);
}

export async function getMaster(id: string) {
  return request<ProductMasterDetail>(`/product-masters/${id}`);
}

export async function updateMaster(id: string, body: Partial<ProductMaster>) {
  return request<ProductMaster>(`/product-masters/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function uploadMasterImage(masterId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request(`/product-masters/${masterId}/images`, { method: "POST", body: fd });
}

export async function uploadVariantImage(variantId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request(`/product-variants/${variantId}/images`, { method: "POST", body: fd });
}

export async function createMasterImageFromUrl(masterId: string, url: string) {
  return request<ProductImage>(`/product-masters/${masterId}/images/from-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url.trim() }),
  });
}

export async function createVariantImageFromUrl(
  variantId: string,
  url: string,
  options?: { setPrimary?: boolean },
) {
  const setPrimary = options?.setPrimary ?? true;
  const query = setPrimary ? "" : "?set_primary=false";
  return request<ProductImage>(`/product-variants/${variantId}/images/from-url${query}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url.trim() }),
  });
}

export async function deleteProductImage(imageId: string) {
  return request<void>(`/product-images/${imageId}`, { method: "DELETE" });
}

export async function setImagePrimary(imageId: string) {
  return request<ProductImage>(`/product-images/${imageId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_primary: true }),
  });
}

export async function getMasterSpecs(masterId: string) {
  return request<SpecValue[]>(`/product-masters/${masterId}/specs`);
}

export async function updateMasterSpecs(
  masterId: string,
  specs: { key: string; value: string | null }[],
) {
  return request<SpecValue[]>(`/product-masters/${masterId}/specs`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ specs }),
  });
}

export async function searchVariants(params?: {
  q?: string;
  supplier_id?: string;
  category_id?: string;
  exclude_catalog_id?: string;
}) {
  const qs = new URLSearchParams();
  if (params?.q) qs.set("q", params.q);
  if (params?.supplier_id) qs.set("supplier_id", params.supplier_id);
  if (params?.category_id) qs.set("category_id", params.category_id);
  if (params?.exclude_catalog_id) qs.set("exclude_catalog_id", params.exclude_catalog_id);
  const q = qs.toString();
  return request<{ items: ProductVariant[]; total: number }>(
    `/product-variants${q ? `?${q}` : ""}`,
  );
}

/** Single price observation from GET /product-variants/{id}/price-history */
export type VariantPriceHistoryItem = {
  list_id: string;
  imported_at: string;
  effective_date: string | null;
  price_amount: string;
  source_filename: string | null;
  delta_pct_vs_previous: string | null;
};

export type VariantPriceHistoryResponse = {
  items: VariantPriceHistoryItem[];
};

export async function getVariantPriceHistory(variantId: string) {
  return request<VariantPriceHistoryResponse>(`/product-variants/${variantId}/price-history`);
}

// Categories
export type Category = { id: string; name: string; parent_id: string | null; children: Category[] };

export async function listCategories() {
  return request<Category[]>("/categories");
}

export async function createCategory(name: string, parent_id?: string | null) {
  return request<Category>("/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, parent_id: parent_id || null }),
  });
}

export async function updateCategory(
  id: string,
  body: { name?: string; parent_id?: string | null },
) {
  return request<Category>(`/categories/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteCategory(id: string) {
  return request<void>(`/categories/${id}`, { method: "DELETE" });
}

export function flattenCategories(nodes: Category[], prefix = ""): { id: string; label: string }[] {
  const out: { id: string; label: string }[] = [];
  for (const n of nodes) {
    const label = prefix ? `${prefix} > ${n.name}` : n.name;
    out.push({ id: n.id, label });
    if (n.children?.length) out.push(...flattenCategories(n.children, label));
  }
  return out;
}

// Catalogs
export type LayoutMode = "automatic" | "uniform" | "manual";

export type ProductLayoutDefinition = {
  id: string;
  name: string;
  description: string;
  compatible_with: "single" | "variants" | "both";
  recommended_variant_attributes: [number, number] | null;
  recommended_image_aspect: string[];
  use_cases: string[];
  limitations: string[];
  auto_priority: number;
  auto_enabled: boolean;
  manual_only: boolean;
};

export type CatalogProductLayout = {
  master_id: string;
  layout_id: string;
};

export type CatalogSectionCover = {
  category_id: string;
  category_name: string;
  cover_image_url: string | null;
  description: string | null;
};

export type CatalogCoverImageResult = {
  cover_image_path: string;
  cover_image_url: string | null;
};

export type CatalogDetailItem = {
  id: string;
  variant_id: string;
  master_id: string;
  sku: string;
  name: string;
  base_price: string | null;
  markup_percent: string | null;
  final_price_override: string | null;
  final_price: string | null;
  sort_order: number;
};

export type CatalogDetail = {
  id: string;
  name: string;
  default_markup_percent: string;
  show_iva_column: boolean;
  show_description_column: boolean;
  cover_image_url: string | null;
  cover_subtitle: string | null;
  layout_mode: LayoutMode;
  uniform_layout_id: string | null;
  product_layouts: CatalogProductLayout[];
  section_covers: CatalogSectionCover[];
  items: CatalogDetailItem[];
};

export type CatalogListItem = {
  id: string;
  name: string;
  default_markup_percent: string;
  show_iva_column?: boolean;
  show_description_column?: boolean;
  layout_mode?: LayoutMode;
  uniform_layout_id?: string | null;
  cover_image_url?: string | null;
  cover_subtitle?: string | null;
};

export type CatalogPatch = {
  name?: string;
  default_markup_percent?: number;
  show_iva_column?: boolean;
  show_description_column?: boolean;
  cover_subtitle?: string | null;
  layout_mode?: LayoutMode;
  uniform_layout_id?: string | null;
};

export type CatalogLayoutSelection = {
  layout_id: string;
  selection_mode: LayoutMode;
  requested_layout_id?: string | null;
  fallback_used?: boolean;
  fallback_reason?: string | null;
};

export type CatalogLayoutStatus = {
  product_layout_mode: LayoutMode;
  uniform_layout_id: string | null;
  summary: {
    total_products: number;
    manual_overrides: number;
    fallback_count: number;
    warning_count: number;
    diagnostics_count: number;
    diagnostics_by_severity?: { critical: number; warning: number; info: number };
    by_layout: Record<string, number>;
    by_section: Record<string, number>;
  };
  layout_warnings: {
    master_id: string;
    master_name: string;
    layout_id: string;
    fallback_reason?: string | null;
    requested_layout_id?: string | null;
  }[];
  diagnostics: {
    type: string;
    severity: string;
    master_id: string;
    master_name: string;
    message: string;
  }[];
  products: {
    master_id: string;
    master_name: string;
    section_name: string;
    layout_id: string;
    has_variants: boolean;
    variant_attribute_count: number;
    image_url?: string | null;
    manual_layout_id?: string | null;
    layout_selection?: CatalogLayoutSelection;
  }[];
};

export async function listCatalogs() {
  return request<{ items: CatalogListItem[] }>("/catalogs");
}

export async function createCatalog(
  name: string,
  default_markup_percent: number,
  show_iva_column = false,
  show_description_column = true,
) {
  return request<{ id: string }>("/catalogs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      default_markup_percent,
      show_iva_column,
      show_description_column,
    }),
  });
}

export async function getCatalog(id: string) {
  return request<CatalogDetail>(`/catalogs/${id}`);
}

export async function listCatalogLayouts() {
  return request<{ items: ProductLayoutDefinition[] }>("/catalogs/layouts");
}

export async function getCatalogLayoutStatus(catalogId: string) {
  return request<CatalogLayoutStatus>(`/catalogs/${catalogId}/layout-status`);
}

export async function updateCatalog(id: string, body: CatalogPatch) {
  return request<CatalogDetail>(`/catalogs/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function uploadCatalogCoverImage(catalogId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<CatalogCoverImageResult>(`/catalogs/${catalogId}/cover-image`, {
    method: "POST",
    body: fd,
  });
}

export async function deleteCatalogCoverImage(catalogId: string) {
  return request<void>(`/catalogs/${catalogId}/cover-image`, { method: "DELETE" });
}

export async function upsertCatalogSectionCover(
  catalogId: string,
  categoryId: string,
  payload: { description?: string | null; file?: File | null },
) {
  const fd = new FormData();
  if (payload.description !== undefined) {
    fd.append("description", payload.description ?? "");
  }
  if (payload.file) {
    fd.append("file", payload.file);
  }
  return request<CatalogSectionCover>(`/catalogs/${catalogId}/section-covers/${categoryId}`, {
    method: "PUT",
    body: fd,
  });
}

export async function deleteCatalogSectionCover(catalogId: string, categoryId: string) {
  return request<void>(`/catalogs/${catalogId}/section-covers/${categoryId}`, {
    method: "DELETE",
  });
}

export async function upsertProductLayout(catalogId: string, masterId: string, layoutId: string) {
  return request(`/catalogs/${catalogId}/product-layouts/${masterId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ layout_id: layoutId }),
  });
}

export async function deleteProductLayout(catalogId: string, masterId: string) {
  return request<void>(`/catalogs/${catalogId}/product-layouts/${masterId}`, {
    method: "DELETE",
  });
}

export type BulkLayoutSkipped = { master_id: string; reason: string };

export type BulkLayoutResult = {
  applied: number;
  cleared: number;
  skipped: BulkLayoutSkipped[];
};

export async function bulkProductLayouts(
  catalogId: string,
  body: { layout_id: string | null; master_ids: string[] },
) {
  return request<BulkLayoutResult>(`/catalogs/${catalogId}/product-layouts/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteCatalog(id: string) {
  return request<void>(`/catalogs/${id}`, { method: "DELETE" });
}

export async function addCatalogItem(catalogId: string, variantId: string, sort_order = 0) {
  return request(`/catalogs/${catalogId}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variant_id: variantId, sort_order }),
  });
}

export async function removeCatalogItem(catalogId: string, itemId: string) {
  return request<void>(`/catalogs/${catalogId}/items/${itemId}`, { method: "DELETE" });
}

export async function patchCatalogItem(
  catalogId: string,
  itemId: string,
  body: {
    markup_percent?: number | null;
    final_price_override?: number | null;
    sort_order?: number;
  },
) {
  return request(`/catalogs/${catalogId}/items/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export type CatalogItemReorderEntry = { id: string; sort_order: number };

export type CatalogItemsReorderResult = { updated: number };

export async function reorderCatalogItems(
  catalogId: string,
  items: CatalogItemReorderEntry[],
): Promise<CatalogItemsReorderResult> {
  return request<CatalogItemsReorderResult>(`/catalogs/${catalogId}/items/reorder`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
}

export async function bulkAddCatalogItems(catalogId: string, categoryId: string) {
  return request<{ created: number }>(`/catalogs/${catalogId}/items/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category_id: categoryId }),
  });
}

export async function listCatalogExports(catalogId: string) {
  return request<{ items: { id: string; filename: string; exported_at: string }[] }>(
    `/catalogs/${catalogId}/exports`,
  );
}

export async function exportCatalogPdf(catalogId: string) {
  const res = await fetch(`${V1}/catalogs/${catalogId}/export/pdf`, { method: "POST" });
  if (!res.ok) {
    const msg = await readErrorMessage(res);
    if (res.status === 503) {
      throw new Error(`Motor PDF no disponible. ${msg}`);
    }
    throw new Error(msg);
  }
  return res.blob();
}

export type CatalogPreviewPdfResult = {
  blob: Blob;
  totalPages: number;
  pdfEngine: string | null;
  generatedAt: string | null;
};

function parsePreviewTotalPages(header: string | null): number {
  if (!header) return 1;
  const n = parseInt(header, 10);
  if (!Number.isFinite(n) || n < 1) return 1;
  return n;
}

export const PREVIEW_PDF_FETCH_TIMEOUT_MS = 180_000;

export type FetchCatalogPreviewPdfOptions = {
  signal?: AbortSignal;
};

export async function fetchCatalogPreviewPdf(
  catalogId: string,
  cacheBust?: string | number,
  options?: FetchCatalogPreviewPdfOptions,
): Promise<CatalogPreviewPdfResult> {
  const qs = cacheBust != null ? `?cache_bust=${encodeURIComponent(String(cacheBust))}` : "";
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort(new DOMException("Preview PDF timeout", "TimeoutError"));
  }, PREVIEW_PDF_FETCH_TIMEOUT_MS);

  const onExternalAbort = () => controller.abort();
  options?.signal?.addEventListener("abort", onExternalAbort, { once: true });
  if (options?.signal?.aborted) controller.abort();

  let res: Response;
  try {
    res = await fetch(`${V1}/catalogs/${catalogId}/preview/pdf${qs}`, {
      method: "POST",
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error("La generación de vista previa PDF tardó demasiado. Inténtalo de nuevo.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    options?.signal?.removeEventListener("abort", onExternalAbort);
  }
  if (!res.ok) {
    const msg = await readErrorMessage(res);
    if (res.status === 503) {
      throw new Error(`Motor PDF no disponible. ${msg}`);
    }
    throw new Error(msg);
  }
  return {
    blob: await res.blob(),
    totalPages: parsePreviewTotalPages(res.headers.get("X-Total-Pages")),
    pdfEngine: res.headers.get("X-Pdf-Engine"),
    generatedAt: res.headers.get("X-Preview-Generated-At"),
  };
}

export function catalogPreviewHtmlUrl(catalogId: string) {
  return `${V1}/catalogs/${catalogId}/preview/html?api_base=${encodeURIComponent(API_BASE)}`;
}

// Background jobs (PRES-5A / PRES-5B)
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export type JobType = "catalog_export_pdf" | (string & {});

export type JobOut = {
  id: string;
  job_type: JobType;
  status: JobStatus;
  progress_percent: number | null;
  message: string | null;
  error_message: string | null;
  catalog_id: string | null;
  catalog_name?: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  download_available: boolean;
  can_cancel: boolean;
  metadata: Record<string, unknown>;
};

export type JobListResponse = {
  items: JobOut[];
  total: number;
};

export type JobCancelResponse = {
  job: JobOut;
  cancelled: boolean;
};

export type ListJobsParams = {
  status?: JobStatus;
  job_type?: string;
  catalog_id?: string;
  active_only?: boolean;
  limit?: number;
};

export async function listJobs(params?: ListJobsParams) {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.job_type) qs.set("job_type", params.job_type);
  if (params?.catalog_id) qs.set("catalog_id", params.catalog_id);
  if (params?.active_only) qs.set("active_only", "true");
  if (params?.limit != null) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return request<JobListResponse>(`/jobs${q ? `?${q}` : ""}`);
}

export async function getJob(jobId: string) {
  return request<JobOut>(`/jobs/${jobId}`);
}

export async function cancelJob(jobId: string) {
  return request<JobCancelResponse>(`/jobs/${jobId}/cancel`, { method: "POST" });
}

export async function downloadJobResult(jobId: string) {
  const res = await fetch(`${V1}/jobs/${jobId}/download`);
  if (!res.ok) {
    throw new Error(await readErrorMessage(res));
  }
  return res.blob();
}

export async function createCatalogPdfExportJob(catalogId: string) {
  return request<JobOut>(`/catalogs/${catalogId}/exports/pdf/jobs`, { method: "POST" });
}

// Source documents & catalog adaptation
export type SourceDocumentOut = {
  id: string;
  sha256: string;
  original_filename: string;
  mime_type: string;
  byte_size: number;
  page_count: number;
  validation_status: string;
  validation_error: string | null;
  created_at: string;
  created_by: string | null;
};

export type SourceDocumentCapabilities = {
  source_document_id: string;
  sha256: string;
  page_count: number;
  validation_status: string;
  profile_match_status: string | null;
  workflows: {
    direct_adaptation: boolean;
    pim_import: boolean;
    analysis: boolean;
  };
  note: string;
  cover_pages?: SourceDocumentCoverPages | null;
};

export type SourceDocumentCoverPages = {
  method?: string;
  page_offset?: number;
  main?: {
    slot_id: string;
    role: string;
    source_page_number: number;
    target_page_number: number;
    prepend_page: boolean;
    detection_note?: string;
  };
  sections?: {
    slot_id: string;
    source_page_number: number;
    target_page_number: number;
    section_key?: string;
    section_label?: string;
    detection_note?: string;
  }[];
  summary?: {
    section_cover_count?: number;
    prepend_main_cover?: boolean;
  };
};

export type AdaptationProjectOut = {
  id: string;
  source_document_id: string;
  analysis_snapshot_id: string | null;
  name: string;
  status: string;
  profile_key: string;
  profile_version: string;
  active_recipe_version_id: string | null;
  created_at: string;
  updated_at: string;
};

export type AdaptationOutputDeliveryManifest = {
  profile?: string;
  delivery_mode?: string;
  byte_length?: number;
  within_budget?: boolean;
  encode_pass?: string;
  budget_bytes?: number;
  soft_warn_bytes?: number;
  soft_warn_triggered?: boolean;
};

export type AdaptationExportManifest = {
  output_delivery?: AdaptationOutputDeliveryManifest;
  [key: string]: unknown;
};

export type AdaptationExportOut = {
  id: string;
  project_id: string;
  recipe_version_id: string;
  job_id: string | null;
  export_kind: string;
  status: string;
  manifest_fingerprint: string;
  manifest: AdaptationExportManifest;
  artifact_path: string | null;
  pdf_artifact_path: string | null;
  output_profile: string;
  delivery_mode: string;
  expires_at: string | null;
  created_at: string;
};

export type AdaptationJobRequest = {
  output_profile?: "email_optimized" | "archive_quality";
  delivery_mode?: "persist" | "ephemeral";
  ephemeral_ttl_seconds?: number;
};

export async function uploadSourceDocument(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<SourceDocumentOut>("/source-documents", { method: "POST", body: fd });
}

export async function startSourceDocumentAnalysis(sourceDocumentId: string) {
  return request<JobOut>(`/source-documents/${sourceDocumentId}/analysis-jobs`, { method: "POST" });
}

export async function getSourceDocumentCapabilities(sourceDocumentId: string) {
  return request<SourceDocumentCapabilities>(`/source-documents/${sourceDocumentId}/capabilities`);
}

export async function createAdaptationFromSource(sourceDocumentId: string, name?: string) {
  return request<AdaptationProjectOut>(`/source-documents/${sourceDocumentId}/adaptations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function getAdaptationProject(projectId: string) {
  return request<AdaptationProjectOut>(`/catalog-adaptations/${projectId}`);
}

export async function listAdaptationExports(projectId: string) {
  return request<{ items: AdaptationExportOut[]; total: number }>(
    `/catalog-adaptations/${projectId}/exports`,
  );
}

export async function createAdaptationPreviewJob(projectId: string, body?: AdaptationJobRequest) {
  return request<JobOut>(`/catalog-adaptations/${projectId}/preview-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}

export async function createAdaptationExportJob(projectId: string, body?: AdaptationJobRequest) {
  return request<JobOut>(`/catalog-adaptations/${projectId}/export-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}

export async function approveAdaptationExport(
  projectId: string,
  body: { export_id: string; approved_by?: string; approval_note?: string },
) {
  return request<{
    id: string;
    project_id: string;
    export_id: string;
    output_profile: string;
    renderer_version: string;
  }>(`/catalog-adaptations/${projectId}/approvals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getAdaptationApproval(projectId: string) {
  return request<{
    id: string;
    project_id: string;
    export_id: string;
    output_profile: string;
    renderer_version: string;
  }>(`/catalog-adaptations/${projectId}/approvals/latest`);
}

export async function getAdaptationParityReport(projectId: string) {
  return request<{ parity_score: number; production_parity_pass: boolean }>(
    `/catalog-adaptations/${projectId}/parity-report`,
  );
}

export async function downloadAdaptationExport(
  projectId: string,
  exportId: string,
  artifact: "pdf" | "manifest" = "pdf",
) {
  const res = await fetch(
    `${V1}/catalog-adaptations/${projectId}/exports/${exportId}/download?artifact=${artifact}`,
  );
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return res.blob();
}

export type AdaptationCoverSlot = {
  slot_id: string;
  role: string;
  cover_type: string | null;
  role_label: string | null;
  source_page_number: number;
  target_page_number: number;
  prepend_page: boolean;
  section_key: string | null;
  section_label: string | null;
  confidence: number | null;
  detection_note: string | null;
  asset_path: string | null;
  asset_sha256: string | null;
  asset_url: string | null;
  asset_status: string;
};

export type AdaptationCoverSlotsOut = {
  project_id: string;
  page_offset: number;
  prepend_main_cover: boolean;
  detection_method: string | null;
  slots: AdaptationCoverSlot[];
};

export type MediaLibraryImage = {
  relative_path: string;
  url: string;
  filename: string;
};

export async function getAdaptationCoverSlots(projectId: string) {
  return request<AdaptationCoverSlotsOut>(`/catalog-adaptations/${projectId}/cover-slots`);
}

export async function uploadAdaptationCoverSlot(projectId: string, slotId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<AdaptationCoverSlotsOut>(
    `/catalog-adaptations/${projectId}/cover-slots/${slotId}/upload`,
    { method: "POST", body: fd },
  );
}

export async function assignAdaptationCoverFromLibrary(
  projectId: string,
  slotId: string,
  relativePath: string,
) {
  return request<AdaptationCoverSlotsOut>(
    `/catalog-adaptations/${projectId}/cover-slots/${slotId}/assign-media`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relative_path: relativePath }),
    },
  );
}

export async function listAdaptationMediaLibrary() {
  return request<{ items: MediaLibraryImage[]; total: number }>(
    "/catalog-adaptations/media-library/images",
  );
}

export async function listPriceLists() {
  return request<
    { id: string; source_filename: string; imported_at: string; supplier_id: string }[]
  >("/price-lists");
}

export async function diffPriceLists(
  a: string,
  b: string,
  params?: { min_delta_pct?: number; direction?: string; only_changes?: boolean },
) {
  const qs = new URLSearchParams();
  if (params?.min_delta_pct != null) qs.set("min_delta_pct", String(params.min_delta_pct));
  if (params?.direction) qs.set("direction", params.direction);
  if (params?.only_changes) qs.set("only_changes", "true");
  const q = qs.toString();
  return request<{
    items: {
      sku: string;
      name: string;
      price_a: string | null;
      price_b: string | null;
      delta_abs: string | null;
      delta_pct: string | null;
      change_type: string;
    }[];
  }>(`/price-lists/${a}/diff/${b}${q ? `?${q}` : ""}`);
}

export function diffPriceListsCsvUrl(a: string, b: string, min_delta_pct?: number) {
  const qs = new URLSearchParams();
  if (min_delta_pct != null) qs.set("min_delta_pct", String(min_delta_pct));
  return `${V1}/price-lists/${a}/diff/${b}/export.csv?${qs}`;
}

// Settings
export type AppSettings = {
  iva_disclaimer: string;
  catalog_logo_url: string | null;
  iva_rate_percent: string;
  catalog_template: string;
  show_iva_column: boolean;
};

export async function getSettings() {
  return request<AppSettings>("/settings");
}

export async function updateSettings(body: Partial<AppSettings>) {
  return request<AppSettings>("/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function uploadLogo(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<AppSettings>("/settings/logo", { method: "POST", body: fd });
}

export async function createBackup() {
  return request<{ path: string; filename: string }>("/system/backup", { method: "POST" });
}

export async function restoreBackup(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<{ status: string }>("/system/restore", { method: "POST", body: fd });
}

export { API_BASE };
