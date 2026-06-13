import type { ProductMasterDetail } from "@/lib/api";
import type { VariantPriceHistoryState } from "@/lib/priceHistory";
import {
  getSingleVariant,
  isSingleVariantProduct,
  shouldShowVariantsTab,
} from "@/lib/productDetailLayout";
import { ProductCharacteristicsCard } from "@/components/products/ProductCharacteristicsCard";
import { ProductDetailLayout } from "@/components/products/ProductDetailLayout";
import { ProductGeneralFormCard } from "@/components/products/ProductGeneralFormCard";
import { ProductImageGallery } from "@/components/products/ProductImageGallery";
import { ProductSummaryCard } from "@/components/products/ProductSummaryCard";
import { ProductVariantsPanel } from "@/components/products/ProductVariantsPanel";
import {
  SingleVariantCommercialCard,
  SingleVariantSidebarPanel,
} from "@/components/products/SingleVariantProductDetails";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export type ProductDetailContentProps = {
  master: ProductMasterDetail;
  apiBase: string;
  productName: string;
  formId: string;
  saving: boolean;
  categories: { id: string; label: string }[];
  attrKey: string;
  attrVal: string;
  onMasterChange: (master: ProductMasterDetail) => void;
  onSave: (event: React.FormEvent) => void;
  onAttrKeyChange: (value: string) => void;
  onAttrValChange: (value: string) => void;
  onSaveAttribute: () => void;
  expandedVariantId: string | null;
  expandedHistoryState: VariantPriceHistoryState;
  onToggleExpand: (variantId: string) => void;
  onRetryHistory?: () => void;
  onUploadMasterImage: (file: File) => Promise<void>;
  onAddMasterImageFromUrl: (url: string) => Promise<void>;
  onDeleteMasterImage: (imageId: string) => Promise<void>;
  onSetMasterImagePrimary: (imageId: string) => Promise<void>;
  onUploadVariantImage: (variantId: string, file: File) => Promise<void>;
  onAddVariantImageFromUrl: (variantId: string, url: string) => Promise<void>;
  onDeleteVariantImage: (imageId: string) => Promise<void>;
  onSetVariantImagePrimary: (imageId: string) => Promise<void>;
  singleVariantHistoryState: VariantPriceHistoryState;
  onRetrySingleVariantHistory?: () => void;
};

function MasterGeneralSection({
  master,
  categories,
  formId,
  saving,
  attrKey,
  attrVal,
  onMasterChange,
  onSave,
  onAttrKeyChange,
  onAttrValChange,
  onSaveAttribute,
}: Pick<
  ProductDetailContentProps,
  | "master"
  | "categories"
  | "formId"
  | "saving"
  | "attrKey"
  | "attrVal"
  | "onMasterChange"
  | "onSave"
  | "onAttrKeyChange"
  | "onAttrValChange"
  | "onSaveAttribute"
>) {
  return (
    <>
      <ProductGeneralFormCard
        master={master}
        categories={categories}
        formId={formId}
        onChange={onMasterChange}
        onSubmit={onSave}
        saving={saving}
      />
      <ProductCharacteristicsCard
        master={master}
        attrKey={attrKey}
        attrVal={attrVal}
        onAttrKeyChange={onAttrKeyChange}
        onAttrValChange={onAttrValChange}
        onSaveAttribute={onSaveAttribute}
      />
    </>
  );
}

export function ProductDetailContent({
  master,
  apiBase,
  productName,
  formId,
  saving,
  categories,
  attrKey,
  attrVal,
  onMasterChange,
  onSave,
  onAttrKeyChange,
  onAttrValChange,
  onSaveAttribute,
  expandedVariantId,
  expandedHistoryState,
  onToggleExpand,
  onRetryHistory,
  onUploadMasterImage,
  onAddMasterImageFromUrl,
  onDeleteMasterImage,
  onSetMasterImagePrimary,
  onUploadVariantImage,
  onAddVariantImageFromUrl,
  onDeleteVariantImage,
  onSetVariantImagePrimary,
  singleVariantHistoryState,
  onRetrySingleVariantHistory,
}: ProductDetailContentProps) {
  const singleVariant = getSingleVariant(master);
  const showVariantsTab = shouldShowVariantsTab(master.variants.length);

  if (isSingleVariantProduct(master) && singleVariant) {
    return (
      <ProductDetailLayout
        main={
          <>
            <ProductGeneralFormCard
              master={master}
              categories={categories}
              formId={formId}
              onChange={onMasterChange}
              onSubmit={onSave}
              saving={saving}
            />
            <SingleVariantCommercialCard variant={singleVariant} />
            <ProductCharacteristicsCard
              master={master}
              attrKey={attrKey}
              attrVal={attrVal}
              onAttrKeyChange={onAttrKeyChange}
              onAttrValChange={onAttrValChange}
              onSaveAttribute={onSaveAttribute}
            />
          </>
        }
        sidebar={
          <>
            <SingleVariantSidebarPanel
              variant={singleVariant}
              apiBase={apiBase}
              historyState={singleVariantHistoryState}
              onRetryHistory={onRetrySingleVariantHistory}
              onUploadImage={(file) => onUploadVariantImage(singleVariant.id, file)}
              onAddImageFromUrl={(url) => onAddVariantImageFromUrl(singleVariant.id, url)}
              onDeleteImage={onDeleteVariantImage}
              onSetPrimaryImage={onSetVariantImagePrimary}
            />
            <ProductSummaryCard master={master} singleProductMode />
          </>
        }
      />
    );
  }

  return (
    <Tabs defaultValue="master">
      <TabsList className="mb-6">
        <TabsTrigger value="master">Datos generales</TabsTrigger>
        {showVariantsTab ? (
          <TabsTrigger value="variants">Variantes ({master.variants.length})</TabsTrigger>
        ) : null}
      </TabsList>

      <TabsContent value="master">
        <ProductDetailLayout
          main={
            <MasterGeneralSection
              master={master}
              categories={categories}
              formId={formId}
              saving={saving}
              attrKey={attrKey}
              attrVal={attrVal}
              onMasterChange={onMasterChange}
              onSave={onSave}
              onAttrKeyChange={onAttrKeyChange}
              onAttrValChange={onAttrValChange}
              onSaveAttribute={onSaveAttribute}
            />
          }
          sidebar={
            <>
              <ProductImageGallery
                master={master}
                apiBase={apiBase}
                productName={productName}
                onUpload={onUploadMasterImage}
                onAddFromUrl={onAddMasterImageFromUrl}
                onDelete={onDeleteMasterImage}
                onSetPrimary={onSetMasterImagePrimary}
              />
              <ProductSummaryCard master={master} />
            </>
          }
        />
      </TabsContent>

      {showVariantsTab ? (
        <TabsContent value="variants">
          <ProductVariantsPanel
            master={master}
            apiBase={apiBase}
            expandedVariantId={expandedVariantId}
            historyState={expandedHistoryState}
            onToggleExpand={onToggleExpand}
            onRetryHistory={onRetryHistory}
            onUploadVariantImage={onUploadVariantImage}
            onAddVariantImageFromUrl={onAddVariantImageFromUrl}
            onDeleteVariantImage={onDeleteVariantImage}
            onSetVariantImagePrimary={onSetVariantImagePrimary}
          />
        </TabsContent>
      ) : null}
    </Tabs>
  );
}
