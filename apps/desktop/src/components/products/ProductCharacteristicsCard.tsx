import type { ProductMasterDetail } from "@/lib/api";
import {
  collectVariantSpecColumns,
  hasAnyDisplayedSpecs,
  masterSpecsForDisplay,
  specHasValue,
  variantSpecValue,
  variantsWithDisplayableSpecs,
} from "@/lib/productSpecs";
import {
  characteristicsVariantColumns,
  getDetailVariantCellValue,
} from "@/lib/variantRepresentation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DataTableScroll } from "@/components/ui/data-table";
import { ProductSpecChip } from "./ProductSpecChip";
import { ProductAttributeForm } from "./ProductAttributeForm";

type ProductCharacteristicsCardProps = {
  master: ProductMasterDetail;
  attrKey: string;
  attrVal: string;
  onAttrKeyChange: (value: string) => void;
  onAttrValChange: (value: string) => void;
  onSaveAttribute: () => void;
};

export function ProductCharacteristicsCard({
  master,
  attrKey,
  attrVal,
  onAttrKeyChange,
  onAttrValChange,
  onSaveAttribute,
}: ProductCharacteristicsCardProps) {
  const masterSpecs = masterSpecsForDisplay(master.specs);
  const variantsWithSpecs = variantsWithDisplayableSpecs(master.variants);
  const showEmpty = !hasAnyDisplayedSpecs(master);
  const isSingleVariant = master.variants.length === 1;
  const useContractColumns = (master.variant_columns?.length ?? 0) > 0;
  const apiSpecColumns = characteristicsVariantColumns(master);
  const variantColumns = useContractColumns
    ? apiSpecColumns.map((column) => ({ key: column.key, label: column.label, sortOrder: 0 }))
    : collectVariantSpecColumns(master.variants);

  return (
    <Card className="builder-panel" aria-labelledby="product-characteristics-heading">
      <CardHeader>
        <CardTitle id="product-characteristics-heading">Características</CardTitle>
        <CardDescription>Atributos del producto y especificaciones por variante.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {showEmpty ? (
          <p
            className="rounded-lg border border-dashed border-border bg-muted/10 px-4 py-6 text-center text-sm text-muted-foreground"
            role="status"
          >
            Este producto no tiene características registradas.
          </p>
        ) : null}

        {masterSpecs.length > 0 ? (
          <section aria-labelledby="master-specs-heading">
            <h3
              id="master-specs-heading"
              className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground"
            >
              Características del producto
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {masterSpecs.map((spec) => (
                <ProductSpecChip key={spec.key} spec={spec} />
              ))}
            </div>
          </section>
        ) : null}

        {variantsWithSpecs.length > 0 ? (
          <section aria-labelledby="variant-specs-heading">
            <h3
              id="variant-specs-heading"
              className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground"
            >
              Características de variantes
            </h3>

            {isSingleVariant ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {(master.variants[0].specs ?? []).filter(specHasValue).map((spec) => (
                  <ProductSpecChip key={spec.key} spec={spec} />
                ))}
              </div>
            ) : (
              <DataTableScroll maxHeight="max-h-[320px]">
                <table className="w-full min-w-[28rem] text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/30">
                      <th
                        scope="col"
                        className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide"
                      >
                        SKU
                      </th>
                      {variantColumns.map((column) => (
                        <th
                          key={column.key}
                          scope="col"
                          className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide"
                        >
                          {column.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {variantsWithSpecs.map((variant, index) => (
                      <tr
                        key={variant.id}
                        className={index % 2 === 0 ? "bg-background" : "bg-muted/15"}
                      >
                        <td className="whitespace-nowrap px-3 py-2 font-mono text-xs font-semibold text-primary">
                          {variant.sku}
                        </td>
                        {variantColumns.map((column) => (
                          <td key={column.key} className="whitespace-nowrap px-3 py-2">
                            {useContractColumns
                              ? getDetailVariantCellValue(variant, column.key)
                              : variantSpecValue(variant, column.key)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DataTableScroll>
            )}
          </section>
        ) : null}

        <ProductAttributeForm
          attrKey={attrKey}
          attrVal={attrVal}
          onAttrKeyChange={onAttrKeyChange}
          onAttrValChange={onAttrValChange}
          onSaveAttribute={onSaveAttribute}
          defaultOpen={showEmpty}
        />
      </CardContent>
    </Card>
  );
}
