import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ResponsiveCollapsiblePanel({
  panelId,
  triggerLabel,
  open,
  onOpenChange,
  collapseEnabled,
  panelClassName,
  showPanelBorder,
  children,
}: {
  panelId: string;
  triggerLabel: ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  collapseEnabled: boolean;
  panelClassName?: string;
  showPanelBorder?: boolean;
  children: ReactNode;
}) {
  const panelVisible = !collapseEnabled || open;

  return (
    <>
      {collapseEnabled ? (
        <Button
          type="button"
          variant="secondary"
          className="responsive-collapsible-panel__toggle min-h-11 w-full justify-between gap-2 sm:w-auto"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => onOpenChange(!open)}
        >
          {triggerLabel}
          <ChevronDown
            className={cn("h-4 w-4 shrink-0 transition-transform", open && "rotate-180")}
            aria-hidden="true"
          />
        </Button>
      ) : null}

      {panelVisible ? (
        <div
          id={panelId}
          className={cn(
            "responsive-collapsible-panel__content",
            panelClassName,
            showPanelBorder && "border-t border-border pt-4",
          )}
        >
          {children}
        </div>
      ) : null}
    </>
  );
}
