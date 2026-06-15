import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUp, Loader2, Sparkles, Upload } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  createAdaptationFromSource,
  getJob,
  getSourceDocumentCapabilities,
  startSourceDocumentAnalysis,
  uploadSourceDocument,
  type JobOut,
  type SourceDocumentCapabilities,
  type SourceDocumentOut,
} from "@/lib/api";

async function waitForJob(jobId: string): Promise<JobOut> {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const job = await getJob(jobId);
    if (job.status === "succeeded" || job.status === "failed" || job.status === "cancelled") {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error("Tiempo de espera agotado");
}

export default function SourceDocumentIntakePage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState<SourceDocumentOut | null>(null);
  const [capabilities, setCapabilities] = useState<SourceDocumentCapabilities | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState<"upload" | "analyze" | "ready">("upload");

  const refreshCapabilities = useCallback(async (sourceId: string) => {
    const caps = await getSourceDocumentCapabilities(sourceId);
    setCapabilities(caps);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setBusy(true);
    try {
      const doc = await uploadSourceDocument(file);
      setSource(doc);
      setStep("analyze");
      const job = await startSourceDocumentAnalysis(doc.id);
      const finished = await waitForJob(job.id);
      if (finished.status !== "succeeded") {
        throw new Error(finished.error_message ?? "El análisis falló");
      }
      await refreshCapabilities(doc.id);
      setStep("ready");
      toast.success("PDF analizado correctamente");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo procesar el PDF");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!source?.id) return;
    void refreshCapabilities(source.id).catch(() => undefined);
  }, [source?.id, refreshCapabilities]);

  const handleAdapt = async () => {
    if (!source) return;
    setBusy(true);
    try {
      const project = await createAdaptationFromSource(source.id);
      navigate(`/adaptations/${project.id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo crear el proyecto de adaptación");
    } finally {
      setBusy(false);
    }
  };

  const handleImport = () => {
    navigate("/import");
    toast.message("Importar al PIM", {
      description: "Usa Importar tarifa con el mismo PDF cuando el flujo de origen único esté conectado.",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Nuevo catálogo desde PDF"
        description="Sube un PDF de proveedor, detecta capacidades y elige adaptación directa o importación al PIM."
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Upload className="h-4 w-4" />
            Documento fuente
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            type="file"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm"
          />
          <Button onClick={() => void handleUpload()} disabled={!file || busy}>
            {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileUp className="mr-2 h-4 w-4" />}
            Subir y analizar
          </Button>
        </CardContent>
      </Card>

      {source && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Perfil detectado</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{source.original_filename}</Badge>
              <Badge variant="outline">{source.page_count} páginas</Badge>
              <Badge variant="outline">{(source.byte_size / (1024 * 1024)).toFixed(2)} MB</Badge>
            </div>
            {capabilities && (
              <>
                <p>
                  Estado perfil: <strong>{capabilities.profile_match_status ?? "pendiente"}</strong>
                </p>
                <p className="text-xs text-muted-foreground">{capabilities.note}</p>
                <div className="flex flex-wrap gap-2">
                  {capabilities.workflows.direct_adaptation && (
                    <Badge>Adaptación directa</Badge>
                  )}
                  {capabilities.workflows.pim_import && <Badge>Importación PIM</Badge>}
                  {capabilities.workflows.analysis && <Badge variant="outline">Análisis</Badge>}
                </div>
              </>
            )}
            {step === "ready" && capabilities && (
              <div className="flex flex-wrap gap-3 pt-2">
                <Button
                  onClick={() => void handleAdapt()}
                  disabled={!capabilities.workflows.direct_adaptation || busy}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Personalizar PDF (Adaptar)
                </Button>
                <Button
                  variant="outline"
                  onClick={handleImport}
                  disabled={!capabilities.workflows.pim_import || busy}
                >
                  Importar productos al PIM
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
