import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ResponsiveMetaGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <dl className={cn("responsive-meta-grid", className)}>{children}</dl>;
}
