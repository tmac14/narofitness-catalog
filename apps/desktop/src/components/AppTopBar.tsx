import { Minus, X } from "lucide-react";

import { BrandLockup } from "@/components/brand/BrandLockup";

import { PaletteTrigger } from "@/components/topbar/PaletteTrigger";

import { RouteActionsStrip } from "@/components/topbar/RouteActionsStrip";

import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";



const isElectron = typeof window !== "undefined" && window.narocatalog?.isElectron;



function WindowControls() {

  if (!isElectron) return null;



  return (

    <div className="app-topbar__controls titlebar-no-drag flex shrink-0 items-center gap-0.5">

      <Button

        type="button"

        variant="ghost"

        size="icon"

        className="app-topbar__control-btn h-11 w-11 text-muted-foreground hover:text-foreground lg:h-9 lg:w-9"

        onClick={() => window.narocatalog?.windowControls.minimize()}

        aria-label="Minimizar"

      >

        <Minus className="h-4 w-4" aria-hidden="true" />

      </Button>

      <Button

        type="button"

        variant="ghost"

        size="icon"

        className="app-topbar__control-btn h-11 w-11 text-muted-foreground hover:text-destructive lg:h-9 lg:w-9"

        onClick={() => window.narocatalog?.windowControls.close()}

        aria-label="Cerrar"

      >

        <X className="h-4 w-4" aria-hidden="true" />

      </Button>

    </div>

  );

}



export function AppTopBar() {

  return (

    <header

      className={cn(

        "app-topbar",

        isElectron && "titlebar-drag",

      )}

      aria-label="Barra principal de la aplicación"

    >

      <div className="app-topbar__inner">

        <BrandLockup className="app-topbar__brand titlebar-no-drag shrink-0" />

        <div className="app-topbar__drag-spacer titlebar-drag min-w-0 flex-1" aria-hidden="true" />

        <div className="app-topbar__actions titlebar-no-drag flex shrink-0 items-center gap-1.5 sm:gap-2">

          <RouteActionsStrip />

          <PaletteTrigger />

          <WindowControls />

        </div>

      </div>

    </header>

  );

}



/** @deprecated Use AppTopBar — kept for existing imports during migration. */

export const TitleBar = AppTopBar;

