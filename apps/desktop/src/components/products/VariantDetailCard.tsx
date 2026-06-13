import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type VariantDetailCardProps = {
  children: ReactNode;
  className?: string;
};

export function VariantDetailCard({ children, className }: VariantDetailCardProps) {
  return (
    <div
      className={cn("variant-detail-card", className)}
      role="region"
      aria-label="Detalle de variante"
    >
      {children}
    </div>
  );
}
