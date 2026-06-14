import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ResponsiveCardHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <header className={cn("responsive-data-card__header", className)}>{children}</header>;
}
