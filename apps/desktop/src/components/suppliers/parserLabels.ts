const PARSER_LABELS: Record<string, string> = {
  fdl_pdf: "PDF FDL",
  generic_pdf: "PDF genérico",
};

export function parserLabel(key: string): string {
  return PARSER_LABELS[key] ?? key.replace(/_/g, " ");
}
