import type { JobOut, JobStatus } from "@/lib/api";

const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  queued: "En cola",
  running: "En curso",
  succeeded: "Completado",
  failed: "Error",
  cancelled: "Cancelado",
};

export const RECENT_TERMINAL_TTL_MS = 15_000;

export function jobStatusLabel(status: JobStatus): string {
  return JOB_STATUS_LABELS[status];
}

export function isActiveJobStatus(status: JobStatus): boolean {
  return status === "queued" || status === "running";
}

export function jobTitle(job: JobOut): string {
  const catalogName =
    job.catalog_name ??
    (typeof job.metadata.catalog_name === "string" ? job.metadata.catalog_name : null);

  if (job.job_type === "catalog_export_pdf") {
    return catalogName ? `Exportar PDF — ${catalogName}` : "Exportar PDF";
  }
  if (job.job_type === "catalog_adaptation_preview") {
    const profile =
      typeof job.metadata.output_profile === "string" ? job.metadata.output_profile : null;
    return profile ? `Vista previa adaptación (${profile})` : "Vista previa adaptación";
  }
  if (job.job_type === "catalog_adaptation_export") {
    const profile =
      typeof job.metadata.output_profile === "string" ? job.metadata.output_profile : null;
    return profile ? `Exportación final (${profile})` : "Exportación final adaptación";
  }

  return catalogName ?? job.message ?? job.job_type;
}

export function centerStatusLabel(activeJobs: JobOut[], recentTerminal: JobOut | null): string {
  const active = activeJobs.filter((job) => isActiveJobStatus(job.status));

  if (active.length === 0) {
    if (recentTerminal?.status === "failed") return "Error en exportación";
    if (recentTerminal?.status === "succeeded") return "Exportación completada";
    return "Sin tareas activas";
  }

  if (active.length === 1) {
    const job = active[0];
    if (job.job_type === "catalog_export_pdf" && job.status === "running") {
      if (job.progress_percent != null) {
        return `Exportando PDF… ${job.progress_percent}%`;
      }
      return "Exportando PDF…";
    }
    return "1 proceso en curso";
  }

  return `${active.length} procesos en curso`;
}

export function progressAriaLabel(job: JobOut): string | null {
  if (job.progress_percent == null) return null;
  return `Progreso de ${jobTitle(job)}: ${job.progress_percent} por ciento`;
}

export function formatJobTimestamp(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function jobsPollIntervalMs(activeCount: number, panelOpen: boolean): number {
  if (activeCount > 0) return 2000;
  if (panelOpen) return 10_000;
  return 15_000;
}

export function applyActiveJobsPoll(previousActiveIds: Set<string>, items: JobOut[]) {
  const nextActiveIds = new Set(items.map((job) => job.id));
  const disappearedIds = [...previousActiveIds].filter((id) => !nextActiveIds.has(id));
  return { nextActiveIds, disappearedIds };
}

export function shouldShowRecentTerminal(
  job: JobOut | null,
  shownAt: number | null,
  now = Date.now(),
): boolean {
  if (!job || shownAt == null) return false;
  if (job.status !== "succeeded" && job.status !== "failed") return false;
  return now - shownAt < RECENT_TERMINAL_TTL_MS;
}

export type JobRowViewModel = {
  id: string;
  title: string;
  statusLabel: string;
  status: JobStatus;
  message: string | null;
  errorMessage: string | null;
  progressPercent: number | null;
  progressAria: string | null;
  createdAt: string;
  startedAt: string;
  finishedAt: string;
  canCancel: boolean;
  downloadAvailable: boolean;
  engineLabel: string | null;
  generatedAt: string | null;
};

export async function fetchActiveJobsSafely(
  listJobsFn: (params: { active_only: boolean }) => Promise<{ items: JobOut[] }>,
): Promise<{ items: JobOut[]; error: null } | { items: null; error: true }> {
  try {
    const response = await listJobsFn({ active_only: true });
    return { items: response.items, error: null };
  } catch {
    return { items: null, error: true };
  }
}

export function buildJobRowViewModel(job: JobOut): JobRowViewModel {
  const engine =
    typeof job.metadata.pdf_engine === "string"
      ? job.metadata.pdf_engine
      : typeof job.metadata.engine === "string"
        ? job.metadata.engine
        : null;
  const generatedAt =
    typeof job.metadata.generated_at === "string" ? job.metadata.generated_at : null;

  return {
    id: job.id,
    title: jobTitle(job),
    statusLabel: jobStatusLabel(job.status),
    status: job.status,
    message: job.message,
    errorMessage: job.error_message,
    progressPercent: job.progress_percent,
    progressAria: progressAriaLabel(job),
    createdAt: formatJobTimestamp(job.created_at),
    startedAt: formatJobTimestamp(job.started_at),
    finishedAt: formatJobTimestamp(job.finished_at),
    canCancel: job.can_cancel,
    downloadAvailable: job.download_available,
    engineLabel: engine,
    generatedAt: generatedAt ? formatJobTimestamp(generatedAt) : null,
  };
}
