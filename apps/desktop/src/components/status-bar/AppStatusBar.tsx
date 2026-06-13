import { ChevronUp, Loader2, Wifi, WifiOff } from "lucide-react";
import { useStatusBar } from "@/context/useStatusBar";
import { centerStatusLabel } from "@/lib/jobLabels";
import { connectionStatusLabel, rightWarningSummary } from "@/lib/statusBarLabels";
import { cn } from "@/lib/utils";
import { ProcessCenterPanel } from "./ProcessCenterPanel";

export function AppStatusBar() {
  const { health, panelOpen, setPanelOpen, statusBarTriggerRef, activeJobs, recentTerminalJob } =
    useStatusBar();
  const centerLabel = centerStatusLabel(activeJobs, recentTerminalJob);
  const connected = health.connected;
  const pdfDegraded = connected === true && !health.pdfEngine;
  const connectionLabel = connectionStatusLabel(connected);
  const rightWarning = rightWarningSummary(connected, pdfDegraded);

  return (
    <>
      <button
        ref={statusBarTriggerRef}
        type="button"
        className={cn(
          "app-status-bar shrink-0",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[color:var(--statusbar-fg)]/80",
        )}
        aria-label="Abrir centro de procesos"
        aria-expanded={panelOpen}
        aria-controls="process-center-panel"
        onClick={() => setPanelOpen(true)}
      >
        <span
          className="app-status-bar__zone app-status-bar__zone--system"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {connected === null ? (
            <Loader2
              className="h-3.5 w-3.5 shrink-0 animate-spin motion-reduce:animate-none"
              aria-hidden="true"
            />
          ) : connected ? (
            <Wifi className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          ) : (
            <WifiOff className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          )}
          <span className="app-status-bar__zone-label">{connectionLabel}</span>
        </span>

        <span className="app-status-bar__zone app-status-bar__zone--center hidden sm:flex">
          <span className="app-status-bar__zone-label truncate">{centerLabel}</span>
        </span>

        <span
          className={cn(
            "app-status-bar__zone app-status-bar__zone--summary",
            rightWarning && "app-status-bar__zone--summary-alert",
          )}
        >
          {rightWarning && (
            <span className="truncate rounded border border-amber-300/45 bg-amber-950/35 px-1.5 py-0.5 text-[0.65rem] font-medium text-amber-50">
              {rightWarning}
            </span>
          )}
          <ChevronUp className="h-3.5 w-3.5 shrink-0 opacity-90" aria-hidden="true" />
        </span>
      </button>

      <ProcessCenterPanel />
    </>
  );
}
