# Ordia Cursor Hooks and Rules

**Bundle source:** `packages/ordia-cursor/templates/`  
**Install via:** `ordia init --with-cursor`  
**Related:** [MANIFEST.md](./MANIFEST.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [PROTOCOLS.md](./PROTOCOLS.md)

---

## Purpose

Explain how Cursor **hooks** and **rules** enforce Ordia session discipline:
which events fire, fail-open vs fail-closed behavior, UNIFIED approval gates,
manifest-driven path classification, and the closure validator reentrancy guard.

## Audience

Cursor integration maintainers, profile authors customizing rules, and agents
debugging blocked edits or missing headers.

---

## Components

```text
.cursor/
├── hooks.json                          # Event → command mapping
├── session-protocol.json               # Persisted session (gitignored)
├── hooks/
│   ├── session_start.py                # sessionStart — fail-open
│   ├── validate_runtime_header.py      # beforeSubmitPrompt — fail-closed
│   ├── check_model_tier.py             # beforeSubmitPrompt — warn-only tier + intent
│   ├── log_model_context.py            # preCompact / sessionEnd — telemetry
│   ├── guard_mode_before_edit.py       # preToolUse — fail-closed
│   └── lib/
│       ├── control_context.py          # Session API + path guards
│       ├── ordia_manifest.py           # Inline stdlib manifest loader
│       ├── model_routing_lite.py       # Stdlib model tier helpers for hooks
│       └── workflow_intents_lite.py    # Warn-only unknown intent: lines
```

└── rules/
    ├── ordia-runtime-protocol-header.mdc
    ├── ordia-recovery-bootstrap.mdc
    ├── ordia-orchestration-mode.mdc
    ├── ordia-implementation-mode.mdc
    ├── ordia-coordination-docs.mdc
    └── <profile>-*.mdc                 # e.g. narofitness-permanent-guardrails
```

Rules provide **prompt-time guidance**; hooks provide **hard enforcement** (headers, edits) and **warn-only** checks (model tier, workflow intent).

---

## Hook events

| Event | Script | Trigger |
|---|---|---|
| `sessionStart` | `session_start.py` | New Cursor chat session |
| `beforeSubmitPrompt` | `validate_runtime_header.py` | User submits prompt (header deny) |
| `beforeSubmitPrompt` | `check_model_tier.py` | User submits prompt (tier + intent warn) |
| `preToolUse` | `guard_mode_before_edit.py` | Agent invokes Write/StrReplace/Delete/Edit |
| `preCompact` | `log_model_context.py` | Context compaction |
| `sessionEnd` | `log_model_context.py` | Chat session ends |

`hooks.json` substitutes `{PYTHON}` with `sys.executable` at init time (`ORDIA-D008`).

---

## Fail-open vs fail-closed matrix

| Hook | On exception | On missing session | Rationale |
|---|---|---|---|
| `sessionStart` | **Allow** (inject fallback context) | N/A | Never block chat start; recovery must remain possible |
| `beforeSubmitPrompt` | **Deny** (header hook) / **Allow** (tier hook) | Deny if change-capable without header | Prevent silent unauthenticated edits |
| `check_model_tier` | **Allow** + warn | Allow | Tier mismatch and unknown intent are informational |
| `guard_mode_before_edit` | **Deny** | Deny | Last line of defense for file mutations |

This asymmetry is **intentional** (v0.6 D-03 / SPEC honesty). Do not describe
Ordia as universally fail-closed.

### sessionStart (fail-open)

```python
# On any exception:
emit_json({"additional_context": "Ordia recovery hook failed; read AGENTS.md..."})
return 0  # always allow session to proceed
```

Success path:

1. Read `ORCHESTRATION_STATE` §0 runtime/protocol fields
2. `persist_session_from_state(root, "sessionStart")`
3. Build `recovery_context(root)` — active task, control paths, bootstrap pointers
4. Warn if runtime/protocol are `NONE_SELECTED`
5. Return `additional_context` JSON to Cursor

### validate_runtime_header (fail-closed)

Decision tree:

```text
Prompt contains Runtime + Protocol headers?
  YES → persist session → allow
  NO → read-only prompt? → allow
  NO → existing valid session? → allow
  NO → seed from ORCHESTRATION_STATE? → allow
  NO → change-capable prompt? → DENY with HEADER_HELP
  NO → allow
```

Change-capable detection includes implementation verbs, file paths, and tool
invocation patterns (see `control_context.is_change_capable_prompt`).

On exception: **deny** with unexpected error message.

### guard_mode_before_edit (fail-closed)

1. Ignore non-edit tools
2. Load session from `session-protocol.json` or seed from state
3. No session → **deny**
4. Extract edit path from tool payload
5. Call `product_edit_blocked(session, path, root)`
6. Blocked → **deny** with reason + control root hint

On exception: **deny**.

---

## Session persistence

File: `.cursor/session-protocol.json` (must be **gitignored**)

Typical fields:

```json
{
  "runtime": "ONLY_CURSOR",
  "protocol": "IMPLEMENTATION",
  "session_mode": "UNIFIED",
  "implementation_approved": false,
  "ordia_profile": "narofitness",
  "source": "beforeSubmitPrompt"
}
```

Population sources:

| Source | When |
|---|---|
| User prompt headers | `beforeSubmitPrompt` |
| ORCHESTRATION_STATE §0 | `sessionStart`, header hook fallback |
| Implementation approval phrase | UNIFIED + user says APPROVE IMPLEMENTATION |

### Session freshness (ORDIA-D017)

When `Active task ID` in live state changes, persisted session is treated as
**stale** for change-capable prompts until user re-declares `Runtime:` + `Protocol:`
or state re-seeds a valid pair. No TTL-based expiry in v0.6.

---

## UNIFIED session mode

Declared via header:

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Session: UNIFIED
```

| Phase | Product edits | Control docs |
|---|---|---|
| PLAN | Blocked | Allowed (orchestration behaviors) |
| EXECUTE (after approval) | Allowed | Allowed if task scope requires |
| QA | Blocked | Blocked |
| CLOSE | Blocked | Required (RUNTIME-D006) |

Approval detection: `detect_implementation_approval(prompt)` sets
`implementation_approved: true` on existing UNIFIED session.

Requires `enforcement.unifiedRequiresApproval: true` in manifest (default).

---

## Path classification

Hooks load manifest via chain:

```text
get_ordia_config(root)
  → try import ordia.config (if ordia-core installed)
  → fallback: hooks/lib/ordia_manifest.py (stdlib YAML subset)
```

Classification functions mirror core:

| Function | Blocks when |
|---|---|
| Product path + ORCHESTRATION | Always (if orchestrationBlocksProduct) |
| Product path + UNIFIED w/o approval | Until implementation approved |
| Product path + IMPLEMENTATION | Allowed with valid session |
| Control path | Allowed with valid session |
| QA evidence path | Allowed (implementation/QA) |

Manifest keys: `enforcement.productRoots`, `controlRoots`, `qaEvidenceRoots`.

Example — Narofitness:

```yaml
productRoots: [apps/]
controlRoots: [docs/coordination/, packages/ordia-core/, ...]
```

Edit to `apps/desktop/src/pages/Foo.tsx` under `Protocol: ORCHESTRATION` → denied.

Edit to `docs/coordination/TASK_REGISTRY.yaml` → allowed.

---

## Rules (.mdc) overview

Rules are loaded by Cursor for every prompt; they **do not** block tools.

| Rule file | Role |
|---|---|
| `ordia-runtime-protocol-header.mdc` | Parse Runtime/Protocol; route to protocol doc |
| `ordia-recovery-bootstrap.mdc` | Cold-start read order from `{controlRoot}` |
| `ordia-orchestration-mode.mdc` | Control-plane identity; forbid product edits |
| `ordia-implementation-mode.mdc` | Executor identity; final report format |
| `ordia-coordination-docs.mdc` | Limited control doc edit permission |
| `narofitness-permanent-guardrails.mdc` | Domain guardrails (profile only) |

All portable rules resolve `{controlRoot}` from `ordia.yaml` → `control.root`.

Protocol routing prefers `{controlRoot}/protocols/` when directory exists
(`ORDIA-D007`).

---

## ORDIA_CLOSURE_VALIDATOR_ACTIVE

Environment variable set by closure subprocess (`ordia.validator.closure`):

```python
env[CLOSURE_VALIDATOR_ACTIVE_ENV] = "1"  # "ORDIA_CLOSURE_VALIDATOR_ACTIVE"
```

Purpose: when `closure.validator` runs `npm run control:validate`, nested
`validate_closure_gate` skips spawning another subprocess — prevents infinite loop.

Hooks do **not** read this variable; validator only.

---

## Drift prevention

Monorepo guard:

```powershell
python scripts/sync_ordia_cursor_bundle.py --check
```

Copies `packages/ordia-cursor/templates/` → `.cursor/` when maintaining reference repo.

Test: `scripts/test_ordia_bundle_drift.py`

---

## Doctor verification

`ordia doctor` validates hook wiring:

- Parses each command in `hooks.json`
- Verifies Python executable invocable
- Ensures script path stays inside project root
- Runs `py_compile` on each hook script

See [CLI.md](./CLI.md).

---

## Failure modes

| User-visible message | Cause | Resolution |
|---|---|---|
| Add Runtime and Protocol headers | Change-capable prompt without session | Add headers to prompt |
| Blocked edit: Runtime and Protocol not established | Edit without session file | Restart chat or declare headers |
| Blocked edit: orchestration cannot modify product | Product path under ORCHESTRATION | Switch to IMPLEMENTATION or edit control docs |
| UNIFIED product block | Missing approval | User sends APPROVE IMPLEMENTATION |
| Hook script missing | Incomplete init | `ordia init --with-cursor --force` |
| session-protocol.json tracked | Git commit mistake | Add to .gitignore; untrack file |

---

## Security notes (v0.6 scope)

- Shell/git command blocking **not implemented** (ORDIA-D018 spike only)
- Validator + prompt contract remain backstop for destructive operations
- Hooks scope to file edit tools only; Shell tool unrestricted

---

## Cross-links

- Manifest enforcement fields → [MANIFEST.md](./MANIFEST.md)
- Architecture data flow → [ARCHITECTURE.md](./ARCHITECTURE.md)
- Protocol documents → [PROTOCOLS.md](./PROTOCOLS.md)
- Validator closure env → [VALIDATOR.md](./VALIDATOR.md)
- Narofitness guardrails → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
- Init install → [GREENFIELD.md](./GREENFIELD.md)
