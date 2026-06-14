import { describe, expect, it } from "vitest";
import { Settings } from "lucide-react";
import {
  mergeTopBarRouteActions,
  TOP_BAR_ROUTE_ACTIONS_MAX,
  type TopBarRouteAction,
} from "@/context/topBarRouteActionsShared";

function makeAction(id: string): TopBarRouteAction {
  return {
    id,
    label: id,
    icon: Settings,
    onClick: () => {},
  };
}

describe("topBarRouteActionsShared", () => {
  it("merges owner registrations in insertion order", () => {
    const registry = new Map<string, TopBarRouteAction[]>([
      ["owner-a", [makeAction("a1"), makeAction("a2")]],
      ["owner-b", [makeAction("b1")]],
    ]);

    expect(mergeTopBarRouteActions(registry).map((action) => action.id)).toEqual([
      "a1",
      "a2",
    ]);
  });

  it("caps visible actions at two", () => {
    const registry = new Map<string, TopBarRouteAction[]>([
      ["owner-a", [makeAction("a1"), makeAction("a2")]],
      ["owner-b", [makeAction("b1"), makeAction("b2")]],
    ]);

    const merged = mergeTopBarRouteActions(registry);
    expect(merged).toHaveLength(TOP_BAR_ROUTE_ACTIONS_MAX);
    expect(merged.map((action) => action.id)).toEqual(["a1", "a2"]);
  });

  it("returns empty list for an empty registry", () => {
    expect(mergeTopBarRouteActions(new Map())).toEqual([]);
  });
});
