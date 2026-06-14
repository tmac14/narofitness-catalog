# Codex-Only Enforcement Spike

**Status:** SPIKE COMPLETE — implements `ORDIA-D012`  
**Date:** 2026-06-14  
**Related:** [SPEC v0.1 (archived)](../archive/ordia/specs/SPEC_v0.1.md) §10, [SPEC_v0.5.md](./SPEC_v0.5.md) §10, [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md)

---

## 1. Problem

Cursor runtimes enforce session discipline via hooks (`beforeSubmitPrompt`, `preToolUse`).
**Codex has no equivalent hook surface.** Without a defined alternative, Codex-only
sessions can skip `Runtime`/`Protocol` headers, edit product code under
`ORCHESTRATION`, and close tasks without validator proof.

**Decision (`ORDIA-D012`):** Hook parity is **not required**. Minimum viable
enforcement = prompt contract + validator/CI + unchanged human approval gates.

---

## 2. Minimum viable enforcement (MVE)

Three layers, ordered by reliability:

```text
┌─────────────────────────────────────────┐
│ 1. Prompt contract (every change turn)  │
│    Runtime + Protocol in user message     │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│ 2. Validator / CI (before merge/close)  │
│    ordia validate [--project]             │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│ 3. Human gates (unchanged)              │
│    APPROVED · LOCKS · READY · QA ACCEPT   │
└─────────────────────────────────────────┘
```

### 2.1 Prompt contract

Every **change-capable** Codex turn must include:

```text
Runtime: ONLY_CODEX
Protocol: IMPLEMENTATION
```

Orchestration turns:

```text
Runtime: ONLY_CODEX
Protocol: ORCHESTRATION
```

Optional (when using unified session):

```text
Session: UNIFIED
Ordia profile: <matches ordia.yaml profile>
```

**Routing:** Read protocol from `{controlRoot}/protocols/CODEX_IMPLEMENTATION.md` or
`CODEX_ORCHESTRATION.md` (greenfield), or flat `docs/control/*_PROTOCOL.md`
(Narofitness profile exception per `ORDIA-D007`).

**Control-plane identity:** Codex orchestrator — not Agent 1A–6 unless explicitly
assigned in the prompt.

### 2.2 Validator and CI

| When | Command | Fail condition |
|---|---|---|
| Before marking task `VALIDATED` | `npm run control:validate` (reference) or `ordia validate --project` | Any error |
| Before merge (recommended) | Same + profile-specific wrapper if present | Any error |
| Optional strict closure | `ordia validate --project --strict-closure` | Closure warnings → errors |
| Optional profile match | `ordia validate --project --strict-profile` | Header profile ≠ manifest |

Codex cannot rely on hooks to block edits. **Orchestration mode** must be
self-enforced: no product paths (`enforcement.productRoots` in `ordia.yaml`) unless
`Session: UNIFIED` + explicit user approval (`enforcement.unifiedRequiresApproval`).

### 2.3 Human gates (no automation substitute)

From `{controlRoot}/protocols/TASK_EXECUTION.md`:

- No implementation before `APPROVED`, `LOCKS_CONFIRMED`, `READY_FOR_IMPLEMENTATION`
- Closure checklist (`RUNTIME-D006`) before `VALIDATED`
- Validator may **warn** on closure gaps (v0.5); `--strict-closure` for hard fail

---

## 3. What Codex does NOT get (explicit non-goals)

| Cursor capability | Codex MVE |
|---|---|
| `beforeSubmitPrompt` header enforcement | Prompt contract only |
| `preToolUse` edit guard | Self-discipline + post-hoc validator |
| `sessionStart` recovery injection | Manual recovery bootstrap read order |
| Profile mismatch block at submit | `--strict-profile` at validate time |
| Fail-closed on hook exception | N/A |

**Acceptable trade-off:** Codex sessions depend on operator discipline and CI
catch-up rather than IDE-time denial.

---

## 4. Optional supplements (post-v0.5)

Not required for v0.5 GA; listed for future work:

| Supplement | Purpose | Effort |
|---|---|---|
| **Codex AGENTS.md / rules pack** | Ship `docs/ordia/codex/` with copy-paste session header template | Low |
| **CI workflow snippet** | GitHub Action running `ordia validate --project` on PR | Low |
| **Pre-commit hook** | Local `control:validate` before commit (developer opt-in) | Low |
| **Codex custom instructions file** | Project-level default Runtime/Protocol reminder | Medium |
| **Session file writer script** | Mirror `.cursor/session-protocol.json` for audit | Medium |

None of these replace the validator; they reduce header omission rate.

---

## 5. Reference implementation (Narofitness)

| Runtime | Control root | Validator | Protocol docs |
|---|---|---|---|
| `ONLY_CODEX` | `docs/control/` | `npm run control:validate` | Flat `*_PROTOCOL.md` |
| `CODEX_PLUS_CURSOR` | same | same + Cursor hooks | Both paths |

Codex orchestration protocol: `docs/control/CODEX_ORCHESTRATION_PROTOCOL.md`  
Codex implementation protocol: `docs/control/CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`

Greenfield copies portable templates from `packages/ordia-core/ordia/protocols/`.

---

## 6. Recommended CI snippet (illustrative)

```yaml
# .github/workflows/ordia-validate.yml (not installed by default)
jobs:
  ordia:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e packages/ordia-core
      - run: ordia validate --project
```

Profile extensions (e.g. Narofitness inventory checks) wrap the generic validator
in `scripts/validate_project_control.py`.

---

## 7. Acceptance criteria (spike)

| Criterion | Status |
|---|---|
| MVE documented (prompt + validator + gates) | **done** |
| Hook parity explicitly declined | **done** (`ORDIA-D012`) |
| Greenfield protocol paths documented | **done** |
| Optional supplements listed without scope creep | **done** |
| CI example provided | **done** |

---

## 8. Follow-up tasks (if pursuing Codex hardening)

1. Add `docs/ordia/codex/SESSION_HEADER_TEMPLATE.md` (copy-paste block)
2. Wire `ordia validate --project` into project CI when user approves
3. Evaluate Codex "project rules" or skill pack after marketplace publish (`ORDIA-D013`)

**No product code changes required** for spike closure.
