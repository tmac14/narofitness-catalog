import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  FileText,
  FileUp,
  FolderTree,
  GitCompare,
  LayoutDashboard,
  Package,
  Settings,
  Truck,
} from "lucide-react";
import type { CommandPaletteItem } from "@/lib/commandPalette";

export type ShellNavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  mobileLabel?: string;
};

/** Single source of truth — all eight destinations, order preserved for desktop. */
export const SHELL_NAV_PRIMARY: ShellNavItem[] = [
  { to: "/", label: "Inicio", icon: LayoutDashboard },
  { to: "/catalog-from-pdf", label: "Catálogo desde PDF", mobileLabel: "Desde PDF", icon: FileText },
  { to: "/import", label: "Importar tarifa", mobileLabel: "Importar", icon: FileUp },
  { to: "/products", label: "Productos", icon: Package },
  { to: "/catalogs", label: "Catálogos", icon: BookOpen },
];

export const SHELL_NAV_SECONDARY: ShellNavItem[] = [
  { to: "/suppliers", label: "Proveedores", icon: Truck },
  { to: "/categories", label: "Categorías", icon: FolderTree },
  { to: "/price-lists", label: "Comparar tarifas", icon: GitCompare },
  { to: "/settings", label: "Configuración", icon: Settings },
];

export const SHELL_NAV_ALL: ShellNavItem[] = [...SHELL_NAV_PRIMARY, ...SHELL_NAV_SECONDARY];

export function isNavActive(pathname: string, to: string): boolean {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function resolveActiveNavLabel(pathname: string): string {
  const active = SHELL_NAV_ALL.find((item) => isNavActive(pathname, item.to));
  return active?.label ?? "NaroCatalog";
}

/** Build command-palette navigation items from the shell nav registry. */
export function buildShellNavPaletteCommands(
  onNavigate: (to: string) => void,
): CommandPaletteItem[] {
  return SHELL_NAV_ALL.map((item) => ({
    id: `nav:${item.to}`,
    label: item.label,
    group: "nav" as const,
    icon: item.icon,
    keywords: [item.label, item.to, item.mobileLabel ?? ""].filter(Boolean),
    onSelect: () => onNavigate(item.to),
  }));
}
