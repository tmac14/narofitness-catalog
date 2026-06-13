# Resultados Fase 0 — Spikes

## Parser PDF (`scripts/spike_pdf_parser.py`)

Ejecutado sobre `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`:

| Métrica | Valor |
|---------|-------|
| Filas detectadas | 871 |
| Estado OK | 836 (96.0%) |
| Revisar | 35 |
| Duplicado | 0 |
| Objetivo MVP (≥90% OK) | **PASS** |

Causas principales de `revisar`: SKUs con patrón extendido ya corregido en regex (`DOBNEXO05N`, etc.).

## Export PDF (`scripts/spike_weasyprint.py`)

Genera `temp/spike_output.pdf` solo con WeasyPrint. Falla si el motor no está disponible.

---

Regenerar métricas:

```powershell
python scripts/spike_pdf_parser.py
python scripts/spike_weasyprint.py
```
