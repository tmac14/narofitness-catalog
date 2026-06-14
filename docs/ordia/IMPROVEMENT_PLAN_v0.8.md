# Ordia Improvement Plan v0.8

**Status:** **CLOSED**  
**Date:** 2026-06-14  
**Scope:** Model routing (v0.7) + workflow intents (v0.8) + documentation zero-gap closeout  
**Baseline:** [SPEC_v0.6.md](./SPEC_v0.6.md)

---

## 1. Program summary

| Slice | Spec | Decision | Status |
|-------|------|----------|--------|
| v0.7 Model tier routing | [SPEC_v0.7.md](./SPEC_v0.7.md) | ORDIA-D022 | **CLOSED** |
| v0.8 Workflow intents | [SPEC_v0.8.md](./SPEC_v0.8.md) | ORDIA-D023 | **CLOSED** |
| Documentation closeout | This plan | — | **CLOSED** |

**Package version:** `ordia-core` **0.8.0**

---

## 2. v0.7 deliverables (ORDIA-D022)

- [x] `MODEL_REGISTRY.yaml` + recommend CLI
- [x] Hooks: tier warn, context logging
- [x] `model_tier_min` enforcement (warn)
- [x] Model usage template + strict validate mode
- [x] Codex self-report contract
- [x] `test_ordia_model_routing.py`

---

## 3. v0.8 deliverables (ORDIA-D023)

- [x] `ordia/workflows/` module + 21 core intents
- [x] CLI `workflow` + `prompt`
- [x] Narofitness profile overlay YAML
- [x] Protocol parity (Cursor + Codex)
- [x] `DAILY_USAGE.md` + README landing
- [x] `test_ordia_workflows.py` in `control:test`

---

## 4. Documentation closeout (zero gap)

- [x] `CHANGELOG.md` → 0.7.0 / 0.8.0
- [x] Package manuals synced (ARCHITECTURE, HOOKS, TESTING, MANIFEST, PROTOCOLS, COMMANDS)
- [x] `AGENTS.md`, `ordia.yaml` header → v0.8
- [x] `PUBLISH_CHECKLIST` → v0.8 gates
- [x] Delete `docs/ordia/templates/` (ORDIA-D021 enforcement)
- [x] Greenfield init ships product docs (`README`, `DAILY_USAGE`, SPECs)
- [x] Inventory: SPEC v0.7/v0.8 → CORE
- [x] `REFERENCE_PROFILE.md` → workflows overlay

---

## 5. Validation gates (exit)

| Gate | Command | Required |
|------|---------|----------|
| Control tests | `npm run control:test` | PASS |
| Project validate | `npm run control:validate` | PASS |
| Docs inventory | `python scripts/audit_docs_inventory.py --check` | 100% |
| Bundle sync | `python scripts/sync_ordia_cursor_bundle.py --check` | in sync |

---

## 6. Next program (out of scope)

- PyPI publish execution (see [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md))
- Marketplace `@ordia/cursor`
- Additional profile overlays beyond Narofitness
