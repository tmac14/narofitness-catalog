import { AlertTriangle } from "lucide-react";
import { catalogPreviewHtmlUrl } from "@/lib/api";
import { HTML_FALLBACK_TITLE, HTML_FALLBACK_WARNING } from "@/lib/catalogPreviewCopy";

type Props = {
  catalogId: string;
  previewKey: number;
};

/** Labelled legacy HTML preview — no pagination, approximate layout only. */
export function ApproximateHtmlPreview({ catalogId, previewKey }: Props) {
  return (
    <div className="approximate-html-preview flex min-h-0 flex-1 flex-col overflow-hidden border-t border-border">
      <div className="flex shrink-0 items-start gap-2 border-b border-warning/30 bg-warning/10 px-4 py-2 text-sm text-warning">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <div>
          <p className="font-medium">{HTML_FALLBACK_TITLE}</p>
          <p className="text-warning/90">{HTML_FALLBACK_WARNING}</p>
        </div>
      </div>
      <iframe
        title="catalog-preview-html-fallback"
        src={`${catalogPreviewHtmlUrl(catalogId)}&_=${previewKey}`}
        className="preview-workspace-frame min-h-[360px] flex-1 border-0"
      />
    </div>
  );
}
