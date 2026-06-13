import { describe, expect, it } from "vitest";
import {
  shouldAbortExportAfterPreviewError,
  shouldClearStaleOnPreviewError,
  shouldClearStaleOnPreviewReady,
  shouldClearStaleOnPreviewRefreshStart,
} from "./catalogPreviewLifecycle";

describe("catalogPreviewLifecycle", () => {
  it("clears stale only after successful PDF load", () => {
    expect(shouldClearStaleOnPreviewRefreshStart()).toBe(false);
    expect(shouldClearStaleOnPreviewReady()).toBe(true);
    expect(shouldClearStaleOnPreviewError()).toBe(false);
  });

  it("aborts export-after-preview when PDF regeneration fails", () => {
    expect(shouldAbortExportAfterPreviewError(true)).toBe(true);
    expect(shouldAbortExportAfterPreviewError(false)).toBe(false);
  });
});
