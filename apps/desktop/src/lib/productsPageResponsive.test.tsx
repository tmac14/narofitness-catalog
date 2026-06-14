import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router-dom/server";
import type { ProductMaster } from "@/lib/api";
import { ProductMasterCard } from "@/components/products/ProductMasterCard";
import { ProductMasterCardList } from "@/components/products/ProductMasterCardList";
import { restoreVariantSheetFocus } from "@/components/products/productVariantExpandSheetFocus";
import { ProductVariantExpandSheetBody } from "@/components/products/ProductVariantExpandSheet";
import { PRODUCTS_LIST_VIEW_POLICY, computeDataViewModeFromWidth } from "@/hooks/useDataViewMode";

function makeMaster(overrides: Partial<ProductMaster> = {}): ProductMaster {
  return {
    id: "master-1",
    name: "Responsive test product",
    brand: "Acme",
    category_id: null,
    master_key: null,
    notes: null,
    variant_count: 1,
    references: ["SKU-1"],
    price: "10,00 €",
    variant_columns: [],
    source_page: 30,
    source_pages: [30],
    variants: [
      {
        id: "v1",
        sku: "SKU-1",
        display_name: null,
        reference_label: null,
        price: "10,00 €",
        image_url: null,
        brand: "Acme",
        brand_display: null,
        variant_label: null,
        attributes: {},
        source_page: 30,
        source_pages: [30],
      },
    ],
    ...overrides,
  };
}

describe("ProductsPage responsive cards and sheet", () => {
  it("renders a touch-first master card without horizontal table markup", () => {
    const html = renderToStaticMarkup(
      <ProductMasterCard master={makeMaster()} index={0} onOpenVariants={() => {}} />,
    );
    expect(html).toContain("responsive-data-card");
    expect(html).toContain("Responsive test product");
    expect(html).toContain("10,00 €");
    expect(html).not.toContain("<table");
    expect(html).not.toContain("product-list-table");
  });

  it("shows a variants action for multi-variant masters", () => {
    const html = renderToStaticMarkup(
      <ProductMasterCard
        master={makeMaster({
          variant_count: 2,
          variants: [
            makeMaster().variants[0],
            { ...makeMaster().variants[0], id: "v2", sku: "SKU-2" },
          ],
        })}
        index={0}
        onOpenVariants={() => {}}
      />,
    );
    expect(html).toContain("2 variantes");
    expect(html).toContain('aria-label="Mostrar 2 variantes de Responsive test product"');
  });

  it("renders card list sort controls for mobile/tablet mode", () => {
    const html = renderToStaticMarkup(
      <ProductMasterCardList
        items={[makeMaster()]}
        sortBy="name"
        sortDir="asc"
        onSort={() => {}}
        variantSheetMasterId={null}
        onOpenVariants={() => {}}
        onVariantSheetOpenChange={() => {}}
      />,
    );
    expect(html).toContain("products-card-sort");
    expect(html).toContain("product-master-card-list");
  });

  it("renders variant cards inside the expand sheet, not a nested table", () => {
    const master = makeMaster({
      variant_count: 2,
      variants: [
        makeMaster().variants[0],
        {
          ...makeMaster().variants[0],
          id: "v2",
          sku: "SKU-2",
          price: "12,00 €",
          source_page: 40,
          source_pages: [40],
        },
      ],
    });

    const html = renderToStaticMarkup(
      <StaticRouter location="/products">
        <ProductVariantExpandSheetBody master={master} />
      </StaticRouter>,
    );
    expect(html).toContain("product-variant-card");
    expect(html).toContain("SKU-2");
    expect(html).toContain("12,00 €");
    expect(html).not.toContain("product-variants-panel__table");
  });

  it("maps products list policy to cards below desktop and table at desktop+", () => {
    expect(computeDataViewModeFromWidth(360, PRODUCTS_LIST_VIEW_POLICY).showCards).toBe(true);
    expect(computeDataViewModeFromWidth(640, PRODUCTS_LIST_VIEW_POLICY).showCards).toBe(true);
    expect(computeDataViewModeFromWidth(1024, PRODUCTS_LIST_VIEW_POLICY).showTable).toBe(true);
  });
});

describe("ProductVariantExpandSheet focus restore", () => {
  function makeFocusEvent() {
    const preventDefault = vi.fn();
    return {
      event: { preventDefault } as unknown as Event,
      preventDefault,
    };
  }

  function makeTrigger(connected: boolean) {
    const focus = vi.fn();
    return {
      trigger: {
        isConnected: connected,
        focus,
      } as unknown as HTMLButtonElement,
      focus,
    };
  }

  it("prevents Radix close auto-focus and restores the connected trigger (Escape path)", () => {
    const { event, preventDefault } = makeFocusEvent();
    const { trigger, focus } = makeTrigger(true);

    restoreVariantSheetFocus(event, trigger);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(focus).toHaveBeenCalledTimes(1);
  });

  it("prevents Radix close auto-focus and restores the connected trigger (close button path)", () => {
    const { event, preventDefault } = makeFocusEvent();
    const { trigger, focus } = makeTrigger(true);

    restoreVariantSheetFocus(event, trigger);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(focus).toHaveBeenCalledTimes(1);
  });

  it("does not focus when the trigger is disconnected", () => {
    const { event, preventDefault } = makeFocusEvent();
    const { trigger, focus } = makeTrigger(false);

    restoreVariantSheetFocus(event, trigger);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(focus).not.toHaveBeenCalled();
  });

  it("does not throw when no trigger was stored", () => {
    const { event, preventDefault } = makeFocusEvent();

    expect(() => restoreVariantSheetFocus(event, null)).not.toThrow();
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it("stores the clicked variants button as the sheet trigger", () => {
    const { trigger } = makeTrigger(true);
    let storedTrigger: HTMLButtonElement | null = null;

    const handler = (clicked: HTMLButtonElement) => {
      storedTrigger = clicked;
    };

    handler(trigger);

    expect(storedTrigger).toBe(trigger);
  });
});
