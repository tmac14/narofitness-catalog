import { Button } from "@/components/ui/button";
import { useTopBarRouteActions } from "@/context/useRegisterTopBarRouteActions";
import { cn } from "@/lib/utils";

export function RouteActionsStrip() {
  const actions = useTopBarRouteActions();

  if (actions.length === 0) {
    return null;
  }

  return (
    <div
      className="titlebar-no-drag app-topbar__route-actions flex min-w-0 shrink items-center gap-1"
      aria-label="Acciones de la sección"
    >
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Button
            key={action.id}
            type="button"
            variant="ghost"
            size="sm"
            disabled={action.disabled}
            className={cn(
              "app-topbar__route-action h-9 max-w-[9rem] gap-1.5 px-2.5 text-xs font-medium text-muted-foreground hover:text-foreground lg:h-8 lg:max-w-[11rem]",
            )}
            onClick={action.onClick}
            aria-label={action.ariaLabel ?? action.label}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">{action.label}</span>
          </Button>
        );
      })}
    </div>
  );
}
