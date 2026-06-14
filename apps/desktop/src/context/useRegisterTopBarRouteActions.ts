import { useContext, useEffect, useId } from "react";
import { TopBarRouteActionsContext } from "@/context/topBarRouteActionsShared";
import type { TopBarRouteAction } from "@/context/topBarRouteActionsShared";

function useTopBarRouteActionsContext() {
  const ctx = useContext(TopBarRouteActionsContext);
  if (!ctx) {
    throw new Error("useRegisterTopBarRouteActions must be used within TopBarRouteActionsProvider");
  }
  return ctx;
}

/**
 * Register up to two contextual top-bar actions for the current route.
 * Actions are cleared automatically on unmount and when the route changes.
 *
 * @example Phase 2 (Agent 1A — catalog editor)
 * ```tsx
 * useRegisterTopBarRouteActions([
 *   { id: "preview", label: "Vista previa", icon: Eye, onClick: openPreview },
 *   { id: "export-pdf", label: "Exportar PDF", icon: FileDown, onClick: startExport },
 * ]);
 * ```
 */
export function useRegisterTopBarRouteActions(actions: TopBarRouteAction[]) {
  const ownerId = useId();
  const { register, unregister } = useTopBarRouteActionsContext();
  const actionsKey = actions.map((a) => `${a.id}:${a.disabled ? "1" : "0"}`).join("|");

  useEffect(() => {
    register(ownerId, actions);
    return () => unregister(ownerId);
  }, [ownerId, register, unregister, actionsKey, actions]);
}

/** Read currently visible route actions (top bar strip). */
export function useTopBarRouteActions() {
  return useTopBarRouteActionsContext().actions;
}
