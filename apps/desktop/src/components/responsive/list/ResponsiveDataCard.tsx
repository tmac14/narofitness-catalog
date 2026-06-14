import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ResponsiveDataCard({
  index,
  modifierClass,
  className,
  children,
}: {
  index: number;
  modifierClass?: string | null;
  className?: string;
  children: ReactNode;
}) {
  return (
    <article
      className={cn(
        "responsive-data-card",
        index % 2 === 0 ? "responsive-data-card--even" : "responsive-data-card--odd",
        modifierClass,
        className,
      )}
    >
      {children}
    </article>
  );
}
