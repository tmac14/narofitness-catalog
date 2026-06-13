import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Settings, Database, Download } from "lucide-react";
import {
  API_BASE,
  createBackup,
  getSettings,
  restoreBackup,
  updateSettings,
  uploadLogo,
  type AppSettings,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { FormSkeleton } from "@/components/LoadingPage";
import { ErrorState } from "@/components/ErrorState";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const isPackaged = typeof window !== "undefined" && !import.meta.env.DEV;

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [restoreConfirm, setRestoreConfirm] = useState("");
  const [pendingRestoreFile, setPendingRestoreFile] = useState<File | null>(null);
  const restoreInputRef = useRef<HTMLInputElement>(null);
  const showSkeleton = useDelayedLoading(loading);

  const loadSettings = useCallback(() => {
    setLoading(true);
    setLoadError(false);
    getSettings()
      .then(setSettings)
      .catch(() => setLoadError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadSettings();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadSettings]);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    if (!settings) return;
    try {
      const s = await updateSettings({
        iva_disclaimer: settings.iva_disclaimer,
        iva_rate_percent: settings.iva_rate_percent,
        catalog_template: settings.catalog_template,
        show_iva_column: settings.show_iva_column,
      });
      setSettings(s);
      toast.success("Configuración guardada.");
    } catch (err) {
      toast.error(String(err));
    }
  }

  async function confirmRestore() {
    if (!pendingRestoreFile || restoreConfirm !== "RESTAURAR") return;
    try {
      await restoreBackup(pendingRestoreFile);
      toast.success("Restauración completada. Reinicie la aplicación.");
      setRestoreOpen(false);
      setRestoreConfirm("");
      setPendingRestoreFile(null);
      if (restoreInputRef.current) restoreInputRef.current.value = "";
    } catch (err) {
      toast.error(String(err));
    }
  }

  if (loading && showSkeleton) {
    return (
      <div>
        <PageHeader
          title="Configuración"
          description="Ajustes de catálogo PDF, IVA y copias de seguridad."
          icon={Settings}
        />
        <FormSkeleton />
        <div className="mt-6">
          <FormSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Configuración"
        description="Ajustes de catálogo PDF, IVA y copias de seguridad."
        icon={Settings}
      />

      {loadError ? (
        <ErrorState
          title="No se pudo cargar la configuración"
          description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
          action={
            <Button type="button" size="sm" variant="secondary" onClick={loadSettings}>
              Reintentar
            </Button>
          }
        />
      ) : settings ? (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Catálogo PDF</CardTitle>
            <CardDescription>Texto legal, IVA y plantilla de exportación.</CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(event) => {
                void onSave(event);
              }}
              className="space-y-4 max-w-xl"
            >
              <div className="space-y-2">
                <Label htmlFor="iva-disclaimer">Texto legal IVA (pie de catálogo PDF)</Label>
                <Textarea
                  id="iva-disclaimer"
                  value={settings.iva_disclaimer}
                  onChange={(e) => setSettings({ ...settings, iva_disclaimer: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="iva-rate">IVA % (columna PVP con IVA)</Label>
                <Input
                  id="iva-rate"
                  type="number"
                  className="w-24"
                  value={settings.iva_rate_percent}
                  onChange={(e) => setSettings({ ...settings, iva_rate_percent: e.target.value })}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                La columna PVP + IVA y el aumento % del catálogo se configuran en cada catálogo
                (Editor de catálogo → Opciones del PDF).
              </p>
              <div className="space-y-2">
                <Label htmlFor="template">Plantilla PDF</Label>
                <Select
                  id="template"
                  value={settings.catalog_template}
                  onChange={(e) => setSettings({ ...settings, catalog_template: e.target.value })}
                >
                  <option value="branded">Con portada e índice</option>
                  <option value="default">Simple</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="logo">Logo catálogo</Label>
                {settings.catalog_logo_url && (
                  <img
                    src={`${API_BASE}${settings.catalog_logo_url}`}
                    alt="Logo del catálogo"
                    className="max-h-[60px] rounded border border-border"
                  />
                )}
                <Input
                  id="logo"
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    void uploadLogo(f)
                      .then(setSettings)
                      .then(() => toast.success("Logo actualizado"));
                  }}
                />
              </div>
              <Button type="submit">Guardar</Button>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-4 w-4" aria-hidden="true" />
            Copia de seguridad
          </CardTitle>
          <CardDescription>Exporta base de datos e imágenes en un ZIP.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            type="button"
            onClick={() => {
              void (async () => {
                try {
                  const r = await createBackup();
                  toast.success(`Copia creada: ${r.filename}`);
                } catch (e) {
                  toast.error(String(e));
                }
              })();
            }}
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Crear copia de seguridad
          </Button>
          <div className="space-y-2">
            <Label htmlFor="restore">Restaurar copia (sobrescribe todos los datos)</Label>
            <Input
              id="restore"
              ref={restoreInputRef}
              type="file"
              accept=".zip"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                setPendingRestoreFile(f);
                setRestoreConfirm("");
                setRestoreOpen(true);
              }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Datos de la aplicación</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          {isPackaged ? (
            <p>
              Los datos se guardan en su equipo, en la carpeta de la aplicación NaroCatalog. El
              motor de base de datos va incluido en la instalación.
            </p>
          ) : (
            <p>
              Modo desarrollo: los datos se almacenan en el volumen de datos del entorno de pruebas.
            </p>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={restoreOpen}
        onOpenChange={(open) => {
          setRestoreOpen(open);
          if (!open) {
            setRestoreConfirm("");
            setPendingRestoreFile(null);
            if (restoreInputRef.current) restoreInputRef.current.value = "";
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Restaurar copia de seguridad?</DialogTitle>
            <DialogDescription>
              Esta acción sobrescribirá todos los datos actuales (productos, tarifas, catálogos).
              Escriba <strong>RESTAURAR</strong> para confirmar.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="restore-confirm">Confirmación</Label>
            <Input
              id="restore-confirm"
              value={restoreConfirm}
              onChange={(e) => setRestoreConfirm(e.target.value)}
              placeholder="RESTAURAR"
              autoComplete="off"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setRestoreOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={restoreConfirm !== "RESTAURAR" || !pendingRestoreFile}
              onClick={() => {
                void confirmRestore();
              }}
            >
              Restaurar ahora
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
