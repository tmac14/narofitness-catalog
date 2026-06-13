# Auditorías — referencia extendida

La referencia canónica de comandos npm está en **[COMMANDS.md](../COMMANDS.md)** (sección Auditorías).

Este archivo conserva detalle adicional de auditorías históricas de PR.

## Comandos activos (resumen)

Ver [COMMANDS.md § Auditorías](../COMMANDS.md#auditorías).

## Auditorías históricas de PR (sin npm script)

Ejecutar con Docker levantado (`npm run docker:up`):

```powershell
docker compose exec -e PYTHONPATH=/app api python scripts/validate_pr_i0_workflow.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_j.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k_preflight.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k_k0_validation.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k1_preflight.py
```

Copiar informes: `npm run audit:report -- pr-j` (etc.).
