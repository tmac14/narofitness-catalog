import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, Download, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { AdaptationCoversPanel } from "@/components/adaptation/AdaptationCoversPanel";
import { PageHeader } from "@/components/PageHeader";
import {
  formatAdaptationProjectStatus,
  formatDeliveryMode,
  formatExportKind,
  formatExportStatus,
  formatOutputProfile,
  formatParityScore,
} from "@/lib/adaptationUiLabels";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  approveAdaptationExport,
  createAdaptationExportJob,
  createAdaptationPreviewJob,
  downloadAdaptationExport,
  downloadJobResult,
  getAdaptationApproval,
  getAdaptationParityReport,
  getAdaptationProject,
  getJob,
  listAdaptationExports,
  type AdaptationExportOut,
  type AdaptationJobRequest,
  type AdaptationProjectOut,
  type JobOut,
} from "@/lib/api";

type OutputProfile = "email_optimized" | "archive_quality";
type DeliveryMode = "persist" | "ephemeral";

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

async function waitForJob(jobId: string): Promise<JobOut> {
  for (let attempt = 0; attempt < 180; attempt += 1) {
    const job = await getJob(jobId);
    if (job.status === "succeeded" || job.status === "failed" || job.status === "cancelled") {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error("Tiempo de espera agotado");
}

export default function AdaptationStudioPage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<AdaptationProjectOut | null>(null);
  const [exports, setExports] = useState<AdaptationExportOut[]>([]);
  const [outputProfile, setOutputProfile] = useState<OutputProfile>("email_optimized");
  const [deliveryMode, setDeliveryMode] = useState<DeliveryMode>("persist");
  const [busy, setBusy] = useState(false);
  const [parityScore, setParityScore] = useState<number | null>(null);
  const [hasApproval, setHasApproval] = useState(false);

  const latestPreview = useMemo(
    () => exports.find((entry) => entry.export_kind === "preview"),
    [exports],
  );
  const latestFinal = useMemo(
    () => exports.find((entry) => entry.export_kind === "final"),
    [exports],
  );

  const refresh = useCallback(async () => {
    if (!projectId) return;
    const [loadedProject, loadedExports] = await Promise.all([
      getAdaptationProject(projectId),
      listAdaptationExports(projectId),
    ]);
    setProject(loadedProject);
    setExports(loadedExports.items);
    try {
      const report = await getAdaptationParityReport(projectId);
      setParityScore(report.parity_score);
    } catch {
      setParityScore(null);
    }
    try {
      await getAdaptationApproval(projectId);
      setHasApproval(true);
    } catch {
      setHasApproval(false);
    }
  }, [projectId]);

  useEffect(() => {
    void refresh().catch((error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo cargar el estudio");
      navigate("/catalog-from-pdf");
    });
  }, [refresh, navigate]);

  const jobRequest = (): AdaptationJobRequest => ({
    output_profile: outputProfile,
    delivery_mode: deliveryMode,
    ephemeral_ttl_seconds: deliveryMode === "ephemeral" ? 3600 : undefined,
  });

  const runPreview = async () => {
    if (!projectId) return;
    setBusy(true);
    try {
      const job = await createAdaptationPreviewJob(projectId, jobRequest());
      const finished = await waitForJob(job.id);
      if (finished.status !== "succeeded") {
        throw new Error(finished.error_message ?? "La vista previa falló");
      }
      await refresh();
      toast.success("Vista previa generada");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Error al generar vista previa");
    } finally {
      setBusy(false);
    }
  };

  const runFinalExport = async () => {
    if (!projectId) return;
    setBusy(true);
    try {
      const job = await createAdaptationExportJob(projectId, {
        output_profile: outputProfile,
        delivery_mode: "persist",
      });
      const finished = await waitForJob(job.id);
      if (finished.status !== "succeeded") {
        throw new Error(finished.error_message ?? "La exportación final falló");
      }
      await refresh();
      toast.success("Exportación final lista");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Error en exportación final");
    } finally {
      setBusy(false);
    }
  };

  const approveLatestPersistPreview = async () => {
    if (!projectId || !latestPreview) return;
    if (latestPreview.delivery_mode !== "persist") {
      toast.error("Solo se puede aprobar una vista previa guardada en el proyecto");
      return;
    }
    setBusy(true);
    try {
      await approveAdaptationExport(projectId, { export_id: latestPreview.id });
      await refresh();
      toast.success("Vista previa aprobada");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo aprobar");
    } finally {
      setBusy(false);
    }
  };

  const downloadLatest = async () => {
    if (!projectId || !latestPreview?.pdf_artifact_path) return;
    try {
      const blob =
        latestPreview.delivery_mode === "ephemeral" && latestPreview.job_id
          ? await downloadJobResult(latestPreview.job_id)
          : await downloadAdaptationExport(projectId, latestPreview.id, "pdf");
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${project?.name ?? "catalogo"}_${latestPreview.output_profile}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo descargar");
    }
  };

  const deliveryBytes = latestPreview?.manifest?.output_delivery?.byte_length ?? null;
  const withinBudget = latestPreview?.manifest?.output_delivery?.within_budget;

  return (
    <div className="space-y-6">
      <PageHeader
        title={project?.name ?? "Estudio de adaptación"}
        description="Personaliza las portadas, genera una vista previa y exporta el catálogo final."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Opciones de entrega</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Formato de salida</Label>
              <div className="space-y-2">
                <label className="flex cursor-pointer items-start gap-2 rounded-md border p-3">
                  <input
                    type="radio"
                    name="output_profile"
                    checked={outputProfile === "email_optimized"}
                    onChange={() => setOutputProfile("email_optimized")}
                  />
                  <span>
                    <strong>Catálogo para email</strong>
                    <p className="text-xs text-muted-foreground">Máx. 15 MB, ideal para adjuntar</p>
                  </span>
                </label>
                <label className="flex cursor-pointer items-start gap-2 rounded-md border p-3">
                  <input
                    type="radio"
                    name="output_profile"
                    checked={outputProfile === "archive_quality"}
                    onChange={() => setOutputProfile("archive_quality")}
                  />
                  <span>
                    <strong>Calidad de archivo</strong>
                    <p className="text-xs text-muted-foreground">
                      Máxima fidelidad visual; puede superar 15 MB
                    </p>
                  </span>
                </label>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Destino del fichero</Label>
              <div className="space-y-2">
                <label className="flex cursor-pointer items-start gap-2 rounded-md border p-3">
                  <input
                    type="radio"
                    name="delivery_mode"
                    checked={deliveryMode === "persist"}
                    onChange={() => setDeliveryMode("persist")}
                  />
                  <span>
                    <strong>Guardar en el proyecto</strong>
                    <p className="text-xs text-muted-foreground">
                      Queda en historial; necesario para aprobar
                    </p>
                  </span>
                </label>
                <label className="flex cursor-pointer items-start gap-2 rounded-md border p-3">
                  <input
                    type="radio"
                    name="delivery_mode"
                    checked={deliveryMode === "ephemeral"}
                    onChange={() => setDeliveryMode("ephemeral")}
                  />
                  <span>
                    <strong>Solo descarga temporal</strong>
                    <p className="text-xs text-muted-foreground">Enlace válido 1 h</p>
                  </span>
                </label>
              </div>
            </div>
            <Button onClick={() => void runPreview()} disabled={busy}>
              {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
              Generar vista previa
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Estado del proyecto</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">
                {formatAdaptationProjectStatus(project?.status)}
              </Badge>
              {parityScore != null && (
                <Badge variant="secondary">{formatParityScore(parityScore)}</Badge>
              )}
              {hasApproval && (
                <Badge className="gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Aprobado
                </Badge>
              )}
            </div>
            {latestPreview && (
              <div className="space-y-1 rounded-md border p-3">
                <p>
                  Última vista previa: <strong>{formatOutputProfile(latestPreview.output_profile)}</strong>
                  {" · "}
                  {formatDeliveryMode(latestPreview.delivery_mode)}
                </p>
                {deliveryBytes != null && (
                  <p>
                    Tamaño: {formatBytes(deliveryBytes)}{" "}
                    {withinBudget === false ? (
                      <Badge variant="destructive">Fuera de presupuesto</Badge>
                    ) : (
                      <Badge variant="secondary">Dentro de presupuesto</Badge>
                    )}
                  </p>
                )}
                <div className="flex flex-wrap gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={() => void downloadLatest()}>
                    <Download className="mr-2 h-4 w-4" />
                    Descargar PDF
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => void approveLatestPersistPreview()}
                    disabled={busy || latestPreview.delivery_mode !== "persist" || hasApproval}
                  >
                    Aprobar vista previa
                  </Button>
                </div>
              </div>
            )}
            <Button
              onClick={() => void runFinalExport()}
              disabled={busy || !hasApproval}
              className="w-full"
            >
              Generar exportación final
            </Button>
            {latestFinal && (
              <p className="text-xs text-muted-foreground">
                Última exportación final: {formatOutputProfile(latestFinal.output_profile)}
                {" · "}
                {latestFinal.manifest?.output_delivery?.byte_length
                  ? formatBytes(latestFinal.manifest.output_delivery.byte_length)
                  : "—"}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {projectId && <AdaptationCoversPanel projectId={projectId} />}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Historial de exportaciones</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {exports.length === 0 && <p className="text-muted-foreground">Sin exportaciones todavía.</p>}
          {exports.map((entry) => (
            <div key={entry.id} className="flex flex-wrap items-center justify-between gap-2 border-b py-2">
              <span>
                {formatExportKind(entry.export_kind)} · {formatOutputProfile(entry.output_profile)} ·{" "}
                {formatDeliveryMode(entry.delivery_mode)}
              </span>
              <Badge variant="outline">{formatExportStatus(entry.status)}</Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
