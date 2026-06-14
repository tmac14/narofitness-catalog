import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ResponsiveCardFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <footer className={cn("responsive-data-card__footer", className)}>{children}</footer>;
}
