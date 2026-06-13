import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  diagnosticTypeLabel,
  formatSkipOrDiagnosticReason,
  groupDiagnosticsBySeverity,
  type LayoutDiagnostic,
} from "@/lib/catalogLayout";

type Props = {
  diagnostics: LayoutDiagnostic[];
  defaultOpen?: boolean;
  onSelectMaster?: (masterId: string) => void;
};

const SEVERITY_META = {
  critical: { label: "Crítico", variant: "critical" as const, icon: AlertCircle },
  warning: { label: "Avisos", variant: "warning" as const, icon: AlertCircle },
  info: { label: "Información", variant: "info" as const, icon: Info },
};

export function DiagnosticsPanel({ diagnostics, defaultOpen = false, onSelectMaster }: Props) {
  const grouped = groupDiagnosticsBySeverity(diagnostics);
  const hasIssues = diagnostics.length > 0;

  if (!hasIssues) {
    return (
      <Card className="builder-panel">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Diagnóstico</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
            No hay incidencias de presentación en la configuración actual.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="builder-panel">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Diagnóstico</CardTitle>
        <CardDescription>
          {diagnostics.length} incidencias · haz clic en un producto para verlo en la tabla
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {(["critical", "warning", "info"] as const).map((severity) => {
          const items = grouped[severity];
          if (items.length === 0) return null;
          const meta = SEVERITY_META[severity];
          const Icon = meta.icon;
          return (
            <details key={severity} open={defaultOpen || severity !== "info"} className="group">
              <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium">
                <Icon className="h-4 w-4 shrink-0" />
                {meta.label}
                <Badge variant={meta.variant}>{items.length}</Badge>
              </summary>
              <ul className="mt-2 space-y-1.5 pl-6 max-h-48 overflow-auto">
                {items.map((item, index) => (
                  <li key={`${item.master_id}-${item.type}-${index}`} className="text-sm">
                    {onSelectMaster ? (
                      <Button
                        type="button"
                        variant="link"
                        className="h-auto p-0 text-left font-medium"
                        onClick={() => onSelectMaster(item.master_id)}
                      >
                        {item.master_name}
                        <span className="sr-only"> — Ver en tabla</span>
                      </Button>
                    ) : (
                      <span className="font-medium">{item.master_name}</span>
                    )}
                    <span className="text-muted-foreground">
                      {" "}
                      · {diagnosticTypeLabel(item.type)}:{" "}
                      {formatSkipOrDiagnosticReason(item.message)}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          );
        })}
      </CardContent>
    </Card>
  );
}
