import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type ProductDetailLayoutProps = {
  main: ReactNode;
  sidebar: ReactNode;
  className?: string;
};

export function ProductDetailLayout({ main, sidebar, className }: ProductDetailLayoutProps) {
  return (
    <div className={cn("product-detail-grid", className)}>
      <div className="product-detail-grid__main space-y-6">{main}</div>
      <aside className="product-detail-grid__sidebar space-y-6">{sidebar}</aside>
    </div>
  );
}
