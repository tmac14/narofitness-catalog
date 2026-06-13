import { describe, expect, it } from "vitest";
import {
  applyDiagnosticsFilter,
  exportWarningsNavigationIntent,
  resolveEditorView,
} from "@/lib/editorPreview";

describe("editorPreview helpers", () => {
  it("resolveEditorView switches between builder and preview", () => {
    expect(resolveEditorView(false)).toBe("builder");
    expect(resolveEditorView(true)).toBe("preview");
  });

  it("exportWarningsNavigationIntent closes preview and opens presentation", () => {
    expect(exportWarningsNavigationIntent()).toEqual({
      closePreview: true,
      targetTab: "presentation",
    });
  });

  it("applyDiagnosticsFilter resets search and page", () => {
    expect(applyDiagnosticsFilter("master-1")).toEqual({
      masterHighlightId: "master-1",
      searchInput: "",
      page: 1,
    });
  });
});
