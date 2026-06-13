import { createContext, type RefObject } from "react";
import type { JobOut } from "@/lib/api";

export type HealthSnapshot = {
  connected: boolean | null;
  pdfEngine: string | null;
  pdfEngineError: string | null;
  pdfEngineFallback: string | null;
  pdfEnginesAvailable: string[];
  version: string | null;
  lastCheckedAt: Date | null;
};

export type StatusBarContextValue = {
  health: HealthSnapshot;
  panelOpen: boolean;
  setPanelOpen: (open: boolean) => void;
  statusBarTriggerRef: RefObject<HTMLButtonElement>;
  refreshHealth: () => void;
  activeJobs: JobOut[];
  panelJobs: JobOut[];
  recentTerminalJob: JobOut | null;
  jobsError: string | null;
  refreshJobs: () => Promise<void>;
  cancelJobById: (jobId: string) => Promise<{ ok: true } | { ok: false; message: string }>;
  downloadJobById: (
    job: JobOut,
  ) => Promise<{ ok: true; filename: string } | { ok: false; message: string }>;
};

export const StatusBarContext = createContext<StatusBarContextValue | null>(null);
