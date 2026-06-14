import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import {
  mergeTopBarRouteActions,
  TopBarRouteActionsContext,
  type TopBarRouteAction,
  type TopBarRouteActionsContextValue,
} from "@/context/topBarRouteActionsShared";

export function TopBarRouteActionsProvider({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const registryRef = useRef(new Map<string, TopBarRouteAction[]>());
  const [actions, setActions] = useState<TopBarRouteAction[]>([]);

  const syncVisible = useCallback(() => {
    setActions(mergeTopBarRouteActions(registryRef.current));
  }, []);

  const register = useCallback(
    (ownerId: string, ownerActions: TopBarRouteAction[]) => {
      registryRef.current.set(ownerId, ownerActions);
      syncVisible();
    },
    [syncVisible],
  );

  const unregister = useCallback(
    (ownerId: string) => {
      registryRef.current.delete(ownerId);
      syncVisible();
    },
    [syncVisible],
  );

  useEffect(() => {
    registryRef.current.clear();
    const timer = window.setTimeout(() => {
      setActions([]);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [pathname]);

  const value = useMemo<TopBarRouteActionsContextValue>(
    () => ({ actions, register, unregister }),
    [actions, register, unregister],
  );

  return (
    <TopBarRouteActionsContext.Provider value={value}>{children}</TopBarRouteActionsContext.Provider>
  );
}
