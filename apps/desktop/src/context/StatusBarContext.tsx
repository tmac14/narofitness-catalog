import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { cancelJob, downloadJobResult, getJob, health, listJobs, type JobOut } from "@/lib/api";
import { executeJobCancel, executeJobDownload } from "@/lib/jobActions";
import {
  StatusBarContext,
  type HealthSnapshot,
  type StatusBarContextValue,
} from "@/context/statusBarContextShared";
import {
  applyActiveJobsPoll,
  fetchActiveJobsSafely,
  jobsPollIntervalMs,
  shouldShowRecentTerminal,
} from "@/lib/jobLabels";

const INITIAL_HEALTH: HealthSnapshot = {
  connected: null,
  pdfEngine: null,
  pdfEngineError: null,
  pdfEngineFallback: null,
  pdfEnginesAvailable: [],
  version: null,
  lastCheckedAt: null,
};

export function StatusBarProvider({ children }: { children: ReactNode }) {
  const [healthState, setHealthState] = useState<HealthSnapshot>(INITIAL_HEALTH);
  const [panelOpen, setPanelOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState<JobOut[]>([]);
  const [panelJobs, setPanelJobs] = useState<JobOut[]>([]);
  const [recentTerminalJob, setRecentTerminalJob] = useState<JobOut | null>(null);
  const [recentTerminalShownAt, setRecentTerminalShownAt] = useState<number | null>(null);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const statusBarTriggerRef = useRef<HTMLButtonElement>(null);
  const previousActiveIdsRef = useRef<Set<string>>(new Set());

  const refreshHealth = useCallback(() => {
    health()
      .then((h) =>
        setHealthState({
          connected: true,
          pdfEngine: h.pdf_engine ?? null,
          pdfEngineError: h.pdf_engine_error ?? null,
          pdfEngineFallback: h.pdf_engine_fallback ?? null,
          pdfEnginesAvailable: h.pdf_engines_available ?? [],
          version: h.version ?? null,
          lastCheckedAt: new Date(),
        }),
      )
      .catch(() =>
        setHealthState((prev) => ({
          ...prev,
          connected: false,
          pdfEngine: null,
          pdfEngineError: null,
          pdfEngineFallback: null,
          pdfEnginesAvailable: [],
          lastCheckedAt: new Date(),
        })),
      );
  }, []);

  const resolveDisappearedJobs = useCallback(async (disappearedIds: string[]) => {
    for (const jobId of disappearedIds) {
      try {
        const job = await getJob(jobId);
        if (job.status === "succeeded" || job.status === "failed") {
          setRecentTerminalJob(job);
          setRecentTerminalShownAt(Date.now());
        }
      } catch {
        // Ignore per-job fetch errors during transition detection.
      }
    }
  }, []);

  const refreshActiveJobs = useCallback(async () => {
    if (healthState.connected !== true) return;

    const result = await fetchActiveJobsSafely(listJobs);
    if (result.error) {
      setJobsError("No se pudieron cargar las tareas activas");
      return;
    }

    const { nextActiveIds, disappearedIds } = applyActiveJobsPoll(
      previousActiveIdsRef.current,
      result.items,
    );
    previousActiveIdsRef.current = nextActiveIds;

    if (disappearedIds.length > 0) {
      void resolveDisappearedJobs(disappearedIds);
    }

    setActiveJobs(result.items);
    setJobsError(null);
  }, [healthState.connected, resolveDisappearedJobs]);

  const refreshPanelJobs = useCallback(async () => {
    if (healthState.connected !== true) return;

    try {
      const response = await listJobs({ limit: 20 });
      setPanelJobs(response.items);
      setJobsError(null);
    } catch {
      setJobsError("No se pudieron cargar las tareas");
    }
  }, [healthState.connected]);

  const refreshJobs = useCallback(async () => {
    await refreshActiveJobs();
    if (panelOpen) {
      await refreshPanelJobs();
    }
  }, [panelOpen, refreshActiveJobs, refreshPanelJobs]);

  const cancelJobById = useCallback(
    async (jobId: string) => {
      const result = await executeJobCancel(jobId, cancelJob);
      if (result.ok) {
        await refreshJobs();
      }
      return result;
    },
    [refreshJobs],
  );

  const downloadJobById = useCallback(async (job: JobOut) => {
    return executeJobDownload(job, downloadJobResult);
  }, []);

  useEffect(() => {
    if (healthState.connected === false) {
      const timer = window.setTimeout(() => {
        setActiveJobs([]);
        setPanelJobs([]);
        previousActiveIdsRef.current = new Set();
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [healthState.connected]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refreshHealth();
    }, 0);
    const interval = window.setInterval(() => {
      refreshHealth();
    }, 15000);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [refreshHealth]);

  useEffect(() => {
    if (healthState.connected !== true) return;

    const timer = window.setTimeout(() => {
      void refreshActiveJobs();
    }, 0);
    const intervalMs = jobsPollIntervalMs(activeJobs.length, panelOpen);
    const interval = window.setInterval(() => {
      void refreshActiveJobs();
    }, intervalMs);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [healthState.connected, activeJobs.length, panelOpen, refreshActiveJobs]);

  useEffect(() => {
    if (!panelOpen || healthState.connected !== true) return;

    const timer = window.setTimeout(() => {
      void refreshPanelJobs();
    }, 0);
    const interval = window.setInterval(() => {
      void refreshPanelJobs();
    }, 10_000);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [panelOpen, healthState.connected, refreshPanelJobs]);

  useEffect(() => {
    if (!shouldShowRecentTerminal(recentTerminalJob, recentTerminalShownAt)) {
      if (recentTerminalJob != null) {
        const timer = window.setTimeout(() => {
          setRecentTerminalJob(null);
          setRecentTerminalShownAt(null);
        }, 0);
        return () => window.clearTimeout(timer);
      }
      return;
    }

    const remaining = (recentTerminalShownAt ?? 0) + 15_000 - Date.now();
    const timeout = window.setTimeout(
      () => {
        setRecentTerminalJob(null);
        setRecentTerminalShownAt(null);
      },
      Math.max(remaining, 0),
    );
    return () => window.clearTimeout(timeout);
  }, [recentTerminalJob, recentTerminalShownAt]);

  const visibleRecentTerminal = shouldShowRecentTerminal(recentTerminalJob, recentTerminalShownAt)
    ? recentTerminalJob
    : null;

  const value = useMemo<StatusBarContextValue>(
    () => ({
      health: healthState,
      panelOpen,
      setPanelOpen,
      statusBarTriggerRef,
      refreshHealth,
      activeJobs,
      panelJobs,
      recentTerminalJob: visibleRecentTerminal,
      jobsError,
      refreshJobs,
      cancelJobById,
      downloadJobById,
    }),
    [
      healthState,
      panelOpen,
      activeJobs,
      panelJobs,
      visibleRecentTerminal,
      jobsError,
      refreshHealth,
      refreshJobs,
      cancelJobById,
      downloadJobById,
    ],
  );

  return <StatusBarContext.Provider value={value}>{children}</StatusBarContext.Provider>;
}
