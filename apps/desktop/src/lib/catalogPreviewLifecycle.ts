/** When to clear or preserve preview stale flags across PDF preview lifecycle events. */

export function shouldClearStaleOnPreviewRefreshStart(): boolean {
  return false;
}

export function shouldClearStaleOnPreviewReady(): boolean {
  return true;
}

export function shouldClearStaleOnPreviewError(): boolean {
  return false;
}

/** Export queued after stale auto-refresh must abort if PDF preview regeneration fails. */
export function shouldAbortExportAfterPreviewError(exportAfterPreviewPending: boolean): boolean {
  return exportAfterPreviewPending;
}
