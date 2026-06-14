import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ResponsiveDataCardList({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <ul
      className={cn(
        "responsive-data-card-list__items flex list-none flex-col gap-0 pl-0",
        className,
      )}
    >
      {children}
    </ul>
  );
}
