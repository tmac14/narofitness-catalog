import { useRef, useState } from "react";
import { ExternalLink, ImageIcon, Link2, Loader2, Star, Trash2 } from "lucide-react";
import { isExternalProductImage, type ProductImage } from "@/lib/api";
import {
  productMediaAddAnotherLabel,
  productMediaEmptyHint,
  productMediaEmptyTitle,
  productMediaExternalBadgeLabel,
  productMediaInstructionsId,
  productMediaReplaceHint,
  productMediaUploadAriaLabel,
  productMediaUploadFailedError,
  productMediaUploadingLabel,
  productMediaUrlCancelLabel,
  productMediaUrlFieldLabel,
  productMediaUrlFailedError,
  productMediaUrlHint,
  productMediaUrlSchemeHint,
  productMediaUrlStorageHint,
  productMediaUrlSubmitLabel,
  productMediaUrlSubmittingLabel,
  productMediaUseExternalUrlLabel,
  productMediaVariantDescription,
  productMediaVariantHeading,
  productMediaViewOriginLabel,
  type ProductMediaScope,
} from "@/lib/productMediaLabels";
import { validateProductMediaFile, validateProductMediaUrl } from "@/lib/productMediaValidation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export type ProductMediaCardProps = {
  scope: ProductMediaScope;
  images: ProductImage[];
  apiBase: string;
  onUpload: (file: File) => Promise<void>;
  onDelete: (imageId: string) => Promise<void>;
  onSetPrimary?: (imageId: string) => Promise<void>;
  onAddFromUrl?: (url: string) => Promise<void>;
  productName?: string;
  sku?: string;
  altLabel?: string;
  className?: string;
  headingId?: string;
};

function previewImage(images: ProductImage[]): ProductImage | null {
  return images.find((img) => img.is_primary) ?? images[0] ?? null;
}

function ExternalImageOriginLink({ url }: { url: string }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-xs text-muted-foreground underline-offset-2 hover:text-primary hover:underline"
    >
      <ExternalLink className="h-3 w-3 shrink-0" aria-hidden="true" />
      {productMediaViewOriginLabel()}
    </a>
  );
}

function ExternalSourceBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "rounded bg-muted px-1 py-0.5 text-[0.55rem] font-medium uppercase tracking-wide text-muted-foreground",
        className,
      )}
    >
      {productMediaExternalBadgeLabel()}
    </span>
  );
}

export function ProductMediaCard({
  scope,
  images,
  apiBase,
  onUpload,
  onDelete,
  onSetPrimary,
  onAddFromUrl,
  productName,
  sku,
  altLabel,
  className,
  headingId,
}: ProductMediaCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [submittingUrl, setSubmittingUrl] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [urlFormOpen, setUrlFormOpen] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);

  const preview = previewImage(images);
  const busy = uploading || submittingUrl || busyId != null;
  const canSetPrimary = typeof onSetPrimary === "function";
  const canAddFromUrl = typeof onAddFromUrl === "function";
  const instructionsId = productMediaInstructionsId(scope);
  const variantHeadingId = headingId ?? "variant-images-heading";
  const urlFieldId = `product-media-url-${scope}`;
  const previewMinHeight = scope === "master" ? "min-h-[160px]" : "min-h-[140px]";
  const previewMaxHeight = scope === "master" ? "max-h-[200px]" : "max-h-[160px]";

  function openFilePicker() {
    if (busy) return;
    fileInputRef.current?.click();
  }

  function onPreviewKeyDown(e: React.KeyboardEvent) {
    if (busy) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openFilePicker();
    }
  }

  function closeUrlForm() {
    setUrlFormOpen(false);
    setUrlInput("");
    setUrlError(null);
  }

  async function processFile(file: File) {
    const validation = validateProductMediaFile(file);
    if (!validation.ok) {
      setError(validation.message);
      return;
    }

    setError(null);
    setUrlError(null);
    setUploading(true);
    try {
      await onUpload(file);
    } catch {
      setError(productMediaUploadFailedError());
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function submitUrl() {
    if (!onAddFromUrl) return;

    const validation = validateProductMediaUrl(urlInput);
    if (!validation.ok) {
      setUrlError(validation.message);
      return;
    }

    setUrlError(null);
    setError(null);
    setSubmittingUrl(true);
    try {
      await onAddFromUrl(validation.url);
      closeUrlForm();
    } catch {
      setUrlError(productMediaUrlFailedError());
    } finally {
      setSubmittingUrl(false);
    }
  }

  async function handleDelete(imageId: string) {
    setBusyId(imageId);
    try {
      await onDelete(imageId);
    } finally {
      setBusyId(null);
    }
  }

  async function handleSetPrimary(imageId: string) {
    if (!onSetPrimary) return;
    setBusyId(imageId);
    try {
      await onSetPrimary(imageId);
    } finally {
      setBusyId(null);
    }
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
    if (!busy) setDragOver(true);
  }

  function onDragLeave(e: React.DragEvent) {
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setDragOver(false);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (busy) return;
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    void processFile(file);
  }

  const imageAlt =
    scope === "master" && productName
      ? preview?.is_primary
        ? `Imagen principal de ${productName}`
        : `Imagen de ${productName}`
      : `Imagen de ${altLabel ?? sku ?? "variante"}`;

  const previewBusyLabel = uploading
    ? productMediaUploadingLabel()
    : submittingUrl
      ? productMediaUrlSubmittingLabel()
      : null;

  return (
    <div className={cn("product-media-card space-y-3", className)}>
      {scope === "variant" ? (
        <div className="space-y-1">
          <h4
            id={variantHeadingId}
            className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            {productMediaVariantHeading()}
          </h4>
          {sku ? (
            <p className="text-xs text-muted-foreground">{productMediaVariantDescription(sku)}</p>
          ) : null}
        </div>
      ) : null}

      {error ? (
        <p
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
        >
          {error}
        </p>
      ) : null}

      <div
        role="button"
        tabIndex={busy ? -1 : 0}
        aria-label={productMediaUploadAriaLabel(scope, sku)}
        aria-busy={uploading || submittingUrl}
        aria-disabled={busy}
        aria-describedby={instructionsId}
        className={cn(
          "product-media-card__preview group image-card relative flex items-center justify-center bg-muted/20",
          previewMinHeight,
          !busy && "cursor-pointer",
          dragOver && "ring-2 ring-primary/50",
          busy && "pointer-events-none opacity-90",
        )}
        onClick={() => openFilePicker()}
        onKeyDown={onPreviewKeyDown}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        {previewBusyLabel ? (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <Loader2
              className="h-8 w-8 animate-spin motion-reduce:animate-none"
              aria-hidden="true"
            />
            <p className="text-xs">{previewBusyLabel}</p>
          </div>
        ) : preview ? (
          <>
            <img
              src={`${apiBase}${preview.url}`}
              alt={imageAlt}
              className={cn("w-full object-contain p-2", previewMaxHeight)}
            />
            {isExternalProductImage(preview) ? (
              <ExternalSourceBadge className="absolute left-2 top-2" />
            ) : null}
            <div
              className="product-media-card__replace-hint absolute inset-0 flex items-center justify-center bg-foreground/45 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
              aria-hidden="true"
            >
              <span className="rounded-md bg-background/90 px-3 py-1.5 text-xs font-medium text-foreground shadow-sm">
                {productMediaReplaceHint()}
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-1.5 px-4 py-6 text-center text-muted-foreground">
            <ImageIcon
              className={cn(scope === "master" ? "h-10 w-10" : "h-9 w-9", "opacity-50")}
              aria-hidden="true"
            />
            <p className="text-sm font-medium text-foreground/80">
              {productMediaEmptyTitle(scope)}
            </p>
            <p id={instructionsId} className="text-xs">
              {productMediaEmptyHint()}
            </p>
          </div>
        )}
      </div>

      {preview && !uploading && !submittingUrl ? (
        <p id={instructionsId} className="sr-only">
          {productMediaEmptyHint()}
        </p>
      ) : null}

      {preview?.external_url && isExternalProductImage(preview) ? (
        <div className="flex justify-end">
          <ExternalImageOriginLink url={preview.external_url} />
        </div>
      ) : null}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="sr-only"
        disabled={busy}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void processFile(file);
        }}
      />

      {images.length > 0 && !busy ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 w-full text-xs text-muted-foreground"
          onClick={() => openFilePicker()}
        >
          {productMediaAddAnotherLabel()}
        </Button>
      ) : null}

      {canAddFromUrl ? (
        <div className="space-y-2">
          {!urlFormOpen ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-8 w-full gap-1.5 text-xs"
              disabled={busy}
              onClick={() => {
                setUrlFormOpen(true);
                setUrlError(null);
              }}
            >
              <Link2 className="h-3.5 w-3.5" aria-hidden="true" />
              {productMediaUseExternalUrlLabel()}
            </Button>
          ) : (
            <div
              className="product-media-url-form rounded-md border border-border bg-muted/10 p-3 space-y-3"
              aria-busy={submittingUrl}
            >
              <div className="space-y-1">
                <p className="text-xs font-medium text-foreground">{productMediaUrlHint()}</p>
                <p className="text-xs text-muted-foreground">{productMediaUrlStorageHint()}</p>
                <p className="text-xs text-muted-foreground">{productMediaUrlSchemeHint()}</p>
              </div>

              <div className="space-y-1.5">
                <label htmlFor={urlFieldId} className="text-xs font-medium text-foreground">
                  {productMediaUrlFieldLabel()}
                </label>
                <Input
                  id={urlFieldId}
                  type="url"
                  value={urlInput}
                  placeholder="https://…"
                  disabled={submittingUrl}
                  className="h-9 text-sm"
                  onChange={(e) => {
                    setUrlInput(e.target.value);
                    if (urlError) setUrlError(null);
                  }}
                />
              </div>

              {urlError ? (
                <p role="alert" className="text-xs text-destructive">
                  {urlError}
                </p>
              ) : null}

              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  className="h-8"
                  disabled={submittingUrl}
                  onClick={() => void submitUrl()}
                >
                  {submittingUrl ? (
                    <Loader2
                      className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none"
                      aria-hidden="true"
                    />
                  ) : null}
                  {productMediaUrlSubmitLabel()}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8"
                  disabled={submittingUrl}
                  onClick={closeUrlForm}
                >
                  {productMediaUrlCancelLabel()}
                </Button>
              </div>
            </div>
          )}
        </div>
      ) : null}

      {images.length > 1 ? (
        <div className="grid grid-cols-3 gap-2">
          {images.map((img) => (
            <div
              key={img.id}
              className={cn(
                "image-card relative overflow-hidden",
                img.is_primary && "border-primary ring-1 ring-primary/40",
              )}
            >
              <img
                src={`${apiBase}${img.url}`}
                alt=""
                className={cn(
                  "w-full object-contain bg-muted/30",
                  scope === "master" ? "h-16" : "h-14",
                )}
              />
              <div className="absolute left-0.5 top-0.5 flex flex-col gap-0.5">
                {img.is_primary ? (
                  <span
                    className={cn(
                      "rounded bg-primary/90 px-1 py-0.5 font-medium text-primary-foreground",
                      scope === "master" ? "text-[0.6rem]" : "text-[0.55rem]",
                    )}
                  >
                    Principal
                  </span>
                ) : null}
                {isExternalProductImage(img) ? <ExternalSourceBadge /> : null}
              </div>
              <div className="flex gap-0.5 p-0.5">
                {canSetPrimary && !img.is_primary ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className={cn("flex-1", scope === "master" ? "h-7 px-1" : "h-6 px-0.5")}
                    disabled={busy}
                    aria-label="Marcar como principal"
                    onClick={() => void handleSetPrimary(img.id)}
                  >
                    <Star className="h-3 w-3" aria-hidden="true" />
                  </Button>
                ) : null}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "flex-1 text-destructive hover:text-destructive",
                    scope === "master" ? "h-7 px-1" : "h-6 px-0.5",
                  )}
                  disabled={busy}
                  aria-label="Borrar imagen"
                  onClick={() => void handleDelete(img.id)}
                >
                  {busyId === img.id ? (
                    <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                  ) : (
                    <Trash2 className="h-3 w-3" aria-hidden="true" />
                  )}
                </Button>
              </div>
              {img.external_url && isExternalProductImage(img) ? (
                <div className="border-t border-border/60 px-1 py-0.5">
                  <ExternalImageOriginLink url={img.external_url} />
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : images.length === 1 ? (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {canSetPrimary && !images[0].is_primary ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={busy}
                onClick={() => void handleSetPrimary(images[0].id)}
              >
                <Star className="h-3.5 w-3.5" aria-hidden="true" />
                Principal
              </Button>
            ) : null}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={busy}
              className="text-destructive hover:text-destructive"
              onClick={() => void handleDelete(images[0].id)}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              Borrar
            </Button>
            {isExternalProductImage(images[0]) ? <ExternalSourceBadge /> : null}
          </div>
          {images[0].external_url && isExternalProductImage(images[0]) ? (
            <ExternalImageOriginLink url={images[0].external_url} />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
