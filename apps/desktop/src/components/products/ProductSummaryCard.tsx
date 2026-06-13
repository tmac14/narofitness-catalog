import { Euro, FolderTree, Hash, Layers, StickyNote, Tag } from "lucide-react";
import type { ProductMasterDetail } from "@/lib/api";
import { masterPriceSummaryLabel } from "@/lib/priceHistory";
import {
  categoryBreadcrumb,
  formatReferencesSummary,
  variantCountLabel,
} from "@/lib/productDetailMeta";
import { masterBrandDisplay } from "@/lib/variantRepresentation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type SummaryRowProps = {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  mono?: boolean;
};

function SummaryRow({ icon: Icon, label, value, mono }: SummaryRowProps) {
  return (
    <div className="flex items-start gap-3 py-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        <p
          className={
            mono
              ? "truncate font-mono text-sm font-semibold text-primary"
              : "truncate text-sm text-foreground"
          }
          title={value}
        >
          {value}
        </p>
      </div>
    </div>
  );
}

type ProductSummaryCardProps = {
  master: ProductMasterDetail;
  singleProductMode?: boolean;
};

export function ProductSummaryCard({ master, singleProductMode = false }: ProductSummaryCardProps) {
  const category = categoryBreadcrumb(master) ?? "—";
  const references = formatReferencesSummary(master);
  const notesPreview = master.notes?.trim() || "—";
  const priceSummary = masterPriceSummaryLabel(master.variants);

  return (
    <Card className="builder-panel lg:sticky lg:top-4">
      <CardHeader>
        <CardTitle className="text-base">Resumen</CardTitle>
        <CardDescription>Vista rápida del producto.</CardDescription>
      </CardHeader>
      <CardContent className="divide-y divide-border">
        <SummaryRow icon={Tag} label="Marca" value={masterBrandDisplay(master) ?? "—"} />
        <SummaryRow icon={FolderTree} label="Categoría" value={category} />
        {singleProductMode ? null : (
          <SummaryRow
            icon={Layers}
            label="Variantes"
            value={variantCountLabel(master.variants.length)}
          />
        )}
        <SummaryRow icon={Euro} label="PVP" value={priceSummary} />
        <SummaryRow icon={Hash} label="Referencias" value={references} mono />
        <SummaryRow icon={StickyNote} label="Notas" value={notesPreview} />
      </CardContent>
    </Card>
  );
}
