import { useCallback, useEffect, useState } from "react";

import { Link, useParams } from "react-router-dom";

import { toast } from "sonner";

import {
  API_BASE,
  createMasterImageFromUrl,
  createVariantImageFromUrl,
  deleteProductImage,
  flattenCategories,
  getMaster,
  getVariantPriceHistory,
  listCategories,
  setImagePrimary,
  updateMaster,
  updateMasterSpecs,
  uploadMasterImage,
  uploadVariantImage,
  type ProductMasterDetail,
} from "@/lib/api";

import { type VariantPriceHistoryState } from "@/lib/priceHistory";
import { getSingleVariant } from "@/lib/productDetailLayout";
import { priceHistoryLoadError } from "@/lib/variantPanelLabels";

import { ProductDetailSkeleton } from "@/components/LoadingPage";

import { ErrorState } from "@/components/ErrorState";

import { useDelayedLoading } from "@/hooks/useDelayedLoading";

import { Button } from "@/components/ui/button";

import { ProductDetailHero } from "@/components/products/ProductDetailHero";

import { ProductDetailContent } from "@/components/products/ProductDetailContent";

const GENERAL_FORM_ID = "product-general-form";

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();

  const [master, setMaster] = useState<ProductMasterDetail | null>(null);

  const [loading, setLoading] = useState(true);

  const [loadError, setLoadError] = useState(false);

  const [saving, setSaving] = useState(false);

  const showSkeleton = useDelayedLoading(loading);

  const [categories, setCategories] = useState<{ id: string; label: string }[]>([]);

  const [expandedVariant, setExpandedVariant] = useState<string | null>(null);

  const [historyByVariant, setHistoryByVariant] = useState<
    Record<string, VariantPriceHistoryState>
  >({});

  const [attrKey, setAttrKey] = useState("");

  const [attrVal, setAttrVal] = useState("");

  const reload = useCallback(() => {
    if (!id) return;

    setLoadError(false);

    getMaster(id)
      .then(setMaster)
      .catch(() => {
        setMaster(null);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      reload();
      void listCategories().then((c) => setCategories(flattenCategories(c)));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [id, reload]);

  const loadVariantHistory = useCallback((variantId: string, force = false) => {
    setHistoryByVariant((prev) => {
      const current = prev[variantId];
      if (!force && (current?.status === "loaded" || current?.status === "loading")) {
        return prev;
      }
      return {
        ...prev,
        [variantId]: {
          status: "loading",
          items: force ? (current?.items ?? []) : [],
        },
      };
    });

    getVariantPriceHistory(variantId)
      .then((response) => {
        setHistoryByVariant((prev) => ({
          ...prev,
          [variantId]: { status: "loaded", items: response.items },
        }));
      })
      .catch(() => {
        setHistoryByVariant((prev) => ({
          ...prev,
          [variantId]: {
            status: "error",
            items: [],
            errorMessage: priceHistoryLoadError(),
          },
        }));
      });
  }, []);

  const singleVariant = master ? getSingleVariant(master) : null;
  const singleVariantId = singleVariant?.id ?? null;

  useEffect(() => {
    if (!expandedVariant) return;
    const timer = window.setTimeout(() => {
      loadVariantHistory(expandedVariant);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [expandedVariant, loadVariantHistory]);

  useEffect(() => {
    if (!singleVariant) return;
    const timer = window.setTimeout(() => {
      loadVariantHistory(singleVariant.id);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [singleVariant, singleVariantId, loadVariantHistory]);

  const expandedHistoryState: VariantPriceHistoryState = expandedVariant
    ? (historyByVariant[expandedVariant] ?? { status: "loading", items: [] })
    : { status: "loading", items: [] };

  const singleVariantHistoryState: VariantPriceHistoryState = singleVariant
    ? (historyByVariant[singleVariant.id] ?? { status: "loading", items: [] })
    : { status: "loading", items: [] };

  async function onSave(e: React.FormEvent) {
    e.preventDefault();

    if (!id || !master) return;

    setSaving(true);

    try {
      await updateMaster(id, {
        name: master.name,
        brand: master.brand,
        notes: master.notes,
        category_id: master.category_id,
      });

      toast.success("Producto guardado.");
      reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  async function onSaveAttribute() {
    if (!id || !master || !attrKey) return;

    const existing = (master.specs || []).map((s) => ({
      key: s.key,
      value: s.key === attrKey ? attrVal : (s.value ?? null),
    }));

    const hasKey = (master.specs || []).some((s) => s.key === attrKey);
    const specs = hasKey ? existing : [...existing, { key: attrKey, value: attrVal }];

    await updateMasterSpecs(id, specs);
    setAttrKey("");
    setAttrVal("");
    toast.success("Atributo guardado.");
    reload();
  }

  const productName = master?.name ?? "Producto";

  return (
    <div className="product-detail-page">
      {loadError ? (
        <ErrorState
          title="No se encontró el producto"
          description="El producto no existe o no se pudo cargar. Vuelva al listado e inténtelo de nuevo."
          action={
            <Button asChild size="sm" variant="secondary">
              <Link to="/products">Volver a productos</Link>
            </Button>
          }
        />
      ) : showSkeleton || !master ? (
        <ProductDetailSkeleton />
      ) : (
        <>
          <ProductDetailHero
            master={master}
            apiBase={API_BASE}
            formId={GENERAL_FORM_ID}
            saving={saving}
          />

          <ProductDetailContent
            master={master}
            apiBase={API_BASE}
            productName={productName}
            formId={GENERAL_FORM_ID}
            saving={saving}
            categories={categories}
            attrKey={attrKey}
            attrVal={attrVal}
            onMasterChange={setMaster}
            onSave={(event) => void onSave(event)}
            onAttrKeyChange={setAttrKey}
            onAttrValChange={setAttrVal}
            onSaveAttribute={() => void onSaveAttribute()}
            expandedVariantId={expandedVariant}
            expandedHistoryState={expandedHistoryState}
            onToggleExpand={(variantId) => {
              setExpandedVariant((prev) => (prev === variantId ? null : variantId));
            }}
            onRetryHistory={
              expandedVariant ? () => loadVariantHistory(expandedVariant, true) : undefined
            }
            onUploadMasterImage={async (file) => {
              if (!id) return;
              await uploadMasterImage(id, file);
              reload();
            }}
            onAddMasterImageFromUrl={async (url) => {
              if (!id) return;
              await createMasterImageFromUrl(id, url);
              reload();
            }}
            onDeleteMasterImage={async (imageId) => {
              await deleteProductImage(imageId);
              reload();
            }}
            onSetMasterImagePrimary={async (imageId) => {
              await setImagePrimary(imageId);
              reload();
            }}
            onUploadVariantImage={async (variantId, file) => {
              await uploadVariantImage(variantId, file);
              reload();
            }}
            onAddVariantImageFromUrl={async (variantId, url) => {
              await createVariantImageFromUrl(variantId, url);
              reload();
            }}
            onDeleteVariantImage={async (imageId) => {
              await deleteProductImage(imageId);
              reload();
            }}
            onSetVariantImagePrimary={async (imageId) => {
              await setImagePrimary(imageId);
              reload();
            }}
            singleVariantHistoryState={singleVariantHistoryState}
            onRetrySingleVariantHistory={
              singleVariant ? () => loadVariantHistory(singleVariant.id, true) : undefined
            }
          />
        </>
      )}
    </div>
  );
}
