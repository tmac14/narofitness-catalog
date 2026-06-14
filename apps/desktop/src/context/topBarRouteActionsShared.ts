import type { LucideIcon } from "lucide-react";
import { createContext } from "react";

export const TOP_BAR_ROUTE_ACTIONS_MAX = 2;

export type TopBarRouteAction = {
  id: string;
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  disabled?: boolean;
  /** Defaults to `label` when omitted. */
  ariaLabel?: string;
};

export type TopBarRouteActionsContextValue = {
  actions: TopBarRouteAction[];
  register: (ownerId: string, actions: TopBarRouteAction[]) => void;
  unregister: (ownerId: string) => void;
};

export const TopBarRouteActionsContext = createContext<TopBarRouteActionsContextValue | null>(
  null,
);

/** Merge owner registrations in insertion order, capped at {@link TOP_BAR_ROUTE_ACTIONS_MAX}. */
export function mergeTopBarRouteActions(
  registry: Map<string, TopBarRouteAction[]>,
): TopBarRouteAction[] {
  const merged: TopBarRouteAction[] = [];
  for (const ownerActions of registry.values()) {
    for (const action of ownerActions) {
      if (merged.length >= TOP_BAR_ROUTE_ACTIONS_MAX) {
        return merged;
      }
      merged.push(action);
    }
  }
  return merged;
}
