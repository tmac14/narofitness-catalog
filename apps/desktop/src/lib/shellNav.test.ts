import { describe, expect, it, vi } from "vitest";
import { buildShellNavPaletteCommands, isNavActive, resolveActiveNavLabel } from "./shellNav";

describe("shellNav", () => {
  it("isNavActive matches root and nested routes", () => {
    expect(isNavActive("/", "/")).toBe(true);
    expect(isNavActive("/products", "/")).toBe(false);
    expect(isNavActive("/products", "/products")).toBe(true);
    expect(isNavActive("/products/abc", "/products")).toBe(true);
    expect(isNavActive("/product", "/products")).toBe(false);
  });

  it("resolveActiveNavLabel returns section label or fallback", () => {
    expect(resolveActiveNavLabel("/")).toBe("Inicio");
    expect(resolveActiveNavLabel("/catalogs/42/edit")).toBe("Catálogos");
    expect(resolveActiveNavLabel("/unknown")).toBe("NaroCatalog");
  });

  it("buildShellNavPaletteCommands exposes all shell destinations", () => {
    const onNavigate = vi.fn();
    const commands = buildShellNavPaletteCommands(onNavigate);

    expect(commands).toHaveLength(8);
    expect(commands.every((command) => command.group === "nav")).toBe(true);

    commands.find((command) => command.id === "nav:/settings")?.onSelect();
    expect(onNavigate).toHaveBeenCalledWith("/settings");
  });
});
