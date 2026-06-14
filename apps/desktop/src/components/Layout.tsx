import { useEffect, useRef, useState, type RefObject } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  BookOpen,
  FileUp,
  FolderTree,
  GitCompare,
  LayoutDashboard,
  MoreHorizontal,
  Package,
  PanelLeft,
  Settings,
  Truck,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { AppTopBar } from "@/components/AppTopBar";
import { AppCommandPalette } from "@/components/AppCommandPalette";
import { StatusBarProvider } from "@/context/StatusBarContext";
import { CommandPaletteProvider } from "@/context/CommandPaletteContext";
import { TopBarRouteActionsProvider } from "@/context/TopBarRouteActionsContext";
import { AppStatusBar } from "@/components/status-bar/AppStatusBar";
import {
  isNavActive,
  SHELL_NAV_ALL,
  SHELL_NAV_PRIMARY,
  SHELL_NAV_SECONDARY,
  type ShellNavItem,
} from "@/lib/shellNav";

function isMoreNavActive(pathname: string): boolean {
  return SHELL_NAV_SECONDARY.some((item) => isNavActive(pathname, item.to));
}

function ShellSheetAccessibleClose({
  closeRef,
  className,
}: {
  closeRef: RefObject<HTMLButtonElement>;
  className?: string;
}) {
  return (
    <SheetClose asChild>
      <Button
        ref={closeRef}
        type="button"
        variant="ghost"
        size="icon"
        className={cn("h-11 w-11 shrink-0 text-muted-foreground hover:text-foreground", className)}
        aria-label="Cerrar panel"
      >
        <X className="h-5 w-5" aria-hidden="true" />
      </Button>
    </SheetClose>
  );
}

function focusShellSheetClose(closeRef: RefObject<HTMLButtonElement>) {
  closeRef.current?.focus();
}
type NavLinkRowProps = {
  item: ShellNavItem;
  pathname: string;
  onNavigate?: () => void;
  compact?: boolean;
};

function NavLinkRow({ item, pathname, onNavigate, compact }: NavLinkRowProps) {
  const Icon = item.icon;
  const active = isNavActive(pathname, item.to);

  return (
    <Link
      to={item.to}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "nav-link flex items-center rounded-lg text-sm font-medium transition-colors",
        compact ? "min-h-11 min-w-11 justify-center px-2" : "gap-2.5 px-3 py-2.5",
        active
          ? "bg-accent text-accent-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
      title={compact ? item.label : undefined}
    >
      <Icon className={cn("h-5 w-5 shrink-0", active && "text-primary")} aria-hidden="true" />
      {compact ? <span className="sr-only">{item.label}</span> : item.label}
    </Link>
  );
}

function ShellNavList({
  pathname,
  onNavigate,
  className,
}: {
  pathname: string;
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      {SHELL_NAV_ALL.map((item) => (
        <NavLinkRow key={item.to} item={item} pathname={pathname} onNavigate={onNavigate} />
      ))}
    </div>
  );
}

function MobileBottomNav({
  pathname,
  moreOpen,
  onMoreOpenChange,
}: {
  pathname: string;
  moreOpen: boolean;
  onMoreOpenChange: (open: boolean) => void;
}) {
  const moreActive = isMoreNavActive(pathname);
  const moreCloseRef = useRef<HTMLButtonElement>(null);

  return (
    <nav
      aria-label="Navegación principal"
      className="flex shrink-0 border-t border-border bg-card tablet:hidden lg:hidden"
      style={{
        paddingBottom: "var(--safe-area-inset-bottom)",
      }}
    >
      {SHELL_NAV_PRIMARY.map((item) => {
        const Icon = item.icon;
        const active = isNavActive(pathname, item.to);
        const label = item.mobileLabel ?? item.label;

        return (
          <Link
            key={item.to}
            to={item.to}
            aria-current={active ? "page" : undefined}
            className={cn(
              "nav-link flex min-h-11 min-w-0 flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 text-[0.65rem] font-medium leading-tight transition-colors",
              active
                ? "text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span className="max-w-full truncate">{label}</span>
          </Link>
        );
      })}

      <Sheet open={moreOpen} onOpenChange={onMoreOpenChange}>
        <SheetTrigger asChild>
          <button
            type="button"
            aria-label="Más secciones"
            aria-expanded={moreOpen}
            aria-current={moreActive ? "page" : undefined}
            className={cn(
              "nav-link flex min-h-11 min-w-0 flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 text-[0.65rem] font-medium leading-tight transition-colors",
              moreActive
                ? "text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <MoreHorizontal className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>Más</span>
          </button>
        </SheetTrigger>
        <SheetContent
          showClose={false}
          className="max-h-[min(70vh,32rem)]"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            focusShellSheetClose(moreCloseRef);
          }}
        >
          <div className="relative">
            <ShellSheetAccessibleClose
              closeRef={moreCloseRef}
              className="absolute right-2 top-2 z-10"
            />
            <SheetHeader className="pr-14">
              <SheetTitle>Más secciones</SheetTitle>
              <SheetDescription>
                Proveedores, categorías, comparación de tarifas y configuración.
              </SheetDescription>
            </SheetHeader>
          </div>
          <div className="flex flex-col gap-0.5 overflow-y-auto px-4 pb-6">
            {SHELL_NAV_SECONDARY.map((item) => {
              const Icon = item.icon;
              const active = isNavActive(pathname, item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => onMoreOpenChange(false)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "nav-link flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
                    active
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </SheetContent>
      </Sheet>
    </nav>
  );
}

export default function Layout() {
  const loc = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const drawerCloseRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDrawerOpen(false);
      setMoreOpen(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loc.pathname]);

  return (
    <StatusBarProvider>
      <TopBarRouteActionsProvider>
        <CommandPaletteProvider>
          <div className="flex h-dvh min-w-[360px] flex-col overflow-hidden bg-background">
            <a href="#main-content" className="skip-link">
              Saltar al contenido principal
            </a>
            <AppTopBar />
            <AppCommandPalette />
            <div className="flex min-h-0 flex-1 flex-col">
              <div className="flex min-h-0 flex-1 min-w-0">
            {/* Desktop / wide: full sidebar */}
            <nav
              aria-label="Navegación principal"
              className="hidden w-64 shrink-0 flex-col border-r border-border bg-card px-3 py-4 lg:flex"
            >
              <div className="mb-5 px-2">
                <p className="text-base font-bold tracking-tight text-foreground">Menú</p>
                <p className="mt-0.5 text-xs text-muted-foreground">Secciones de la aplicación</p>
              </div>
              <ShellNavList pathname={loc.pathname} />
            </nav>

            {/* Tablet landscape: icon rail */}
            <nav
              aria-label="Navegación principal"
              className="hidden w-[4.5rem] shrink-0 flex-col items-center gap-1 border-r border-border bg-card px-1.5 py-3 tablet-landscape:flex lg:hidden"
            >
              {SHELL_NAV_ALL.map((item) => (
                <NavLinkRow key={item.to} item={item} pathname={loc.pathname} compact />
              ))}
            </nav>

            <div className="flex min-h-0 min-w-0 flex-1 flex-col">
              {/* Tablet portrait: section header + drawer trigger */}
              <header className="hidden shrink-0 items-center border-b border-border bg-card px-3 py-2 tablet-portrait:flex lg:hidden">
                <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
                  <SheetTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="h-11 w-11 shrink-0"
                      aria-label="Abrir menú de navegación"
                    >
                      <PanelLeft className="h-5 w-5" aria-hidden="true" />
                    </Button>
                  </SheetTrigger>
                  <SheetContent
                    showClose={false}
                    className={cn(
                      "inset-x-auto inset-y-0 bottom-auto left-0 right-auto top-0 h-full w-[min(20rem,85vw)] max-h-none rounded-none rounded-r-lg border-r",
                      "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left",
                    )}
                    onOpenAutoFocus={(event) => {
                      event.preventDefault();
                      focusShellSheetClose(drawerCloseRef);
                    }}
                  >
                    <div className="relative">
                      <ShellSheetAccessibleClose
                        closeRef={drawerCloseRef}
                        className="absolute right-2 top-2 z-10"
                      />
                      <SheetHeader className="pr-14">
                        <SheetTitle>Menú</SheetTitle>
                        <SheetDescription>Secciones de la aplicación</SheetDescription>
                      </SheetHeader>
                    </div>
                    <div className="overflow-y-auto px-4 pb-6">
                      <ShellNavList
                        pathname={loc.pathname}
                        onNavigate={() => setDrawerOpen(false)}
                      />
                    </div>
                  </SheetContent>
                </Sheet>
              </header>

              <main
                id="main-content"
                tabIndex={-1}
                className={cn(
                  "app-scroll min-h-0 flex-1 bg-background outline-none",
                  "p-4 tablet:p-5 lg:p-8",
                )}
              >
                <div className="page-container h-full min-w-0">
                  <Outlet />
                </div>
              </main>
            </div>
              </div>

              <MobileBottomNav
                pathname={loc.pathname}
                moreOpen={moreOpen}
                onMoreOpenChange={setMoreOpen}
              />
              <AppStatusBar />
            </div>
          </div>
        </CommandPaletteProvider>
      </TopBarRouteActionsProvider>
    </StatusBarProvider>
  );
}
