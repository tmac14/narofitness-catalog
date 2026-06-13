import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  FileUp,
  FolderTree,
  GitCompare,
  LayoutDashboard,
  Package,
  Settings,
  Truck,
} from "lucide-react";

export type ShellNavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  mobileLabel?: string;
};

/** Single source of truth — all eight destinations, order preserved for desktop. */
export const SHELL_NAV_PRIMARY: ShellNavItem[] = [
  { to: "/", label: "Inicio", icon: LayoutDashboard },
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
