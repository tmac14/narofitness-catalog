import type { ReactNode } from "react";
import { MoreVertical } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ResponsiveTouchMenuTrigger({
  ariaLabel,
  className,
  children,
}: {
  ariaLabel: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn(
        "responsive-touch-menu-trigger h-11 w-11 shrink-0 text-muted-foreground hover:text-foreground",
        className,
      )}
      aria-label={ariaLabel}
    >
      {children ?? <MoreVertical className="h-5 w-5" aria-hidden="true" />}
    </Button>
  );
}
