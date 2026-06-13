export type EditorViewMode = "builder" | "preview";

export function resolveEditorView(showPreview: boolean): EditorViewMode {
  return showPreview ? "preview" : "builder";
}

export type ExportWarningsNavigation = {
  closePreview: boolean;
  targetTab: "presentation";
};

export function exportWarningsNavigationIntent(): ExportWarningsNavigation {
  return { closePreview: true, targetTab: "presentation" };
}

export function applyDiagnosticsFilter(masterId: string): {
  masterHighlightId: string;
  searchInput: string;
  page: number;
} {
  return { masterHighlightId: masterId, searchInput: "", page: 1 };
}
