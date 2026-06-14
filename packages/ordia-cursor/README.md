# ordia-cursor

Cursor adapter bundle for [Ordia](../../docs/ordia/README.md): rules, hooks, and
`hooks.json` installed by `ordia init --with-cursor`.

## Layout

```text
templates/
  hooks.json        {PYTHON} placeholder → sys.executable at init
  hooks/
    lib/ordia_manifest.py       stdlib-only manifest loader (no pip required)
    lib/control_context.py      shared session, registry, recovery helpers
    lib/model_routing_lite.py   tier slug mapping + rate-limit notes (mirrors ordia-core)
    session_start.py            inject recovery + model-picker reminder
    validate_runtime_header.py  fail-closed Runtime/Protocol header gate
    check_model_tier.py         warn on tier approval / mismatch (Auto Mode exempt)
    log_model_context.py        append model telemetry JSONL (preCompact, sessionEnd)
    guard_mode_before_edit.py   UNIFIED / orchestration product-code guard
  rules/            ordia-*.mdc (portable core rules)
```

Project-specific guardrails (e.g. `narofitness-permanent-guardrails.mdc`) are
**not** included — add them as a profile layer after init.

## Hook events (`hooks.json`)

| Event | Script | Purpose |
|-------|--------|---------|
| `sessionStart` | `session_start.py` | Recovery context + manual model selection reminder |
| `beforeSubmitPrompt` | `validate_runtime_header.py` | Require Runtime/Protocol headers (fail-closed) |
| `beforeSubmitPrompt` | `check_model_tier.py` | Model tier approval + mismatch warnings |
| `preToolUse` | `guard_mode_before_edit.py` | Block product edits under orchestration / UNIFIED |
| `preCompact` | `log_model_context.py` | Context pressure telemetry |
| `sessionEnd` | `log_model_context.py` | Session duration / reason telemetry |

Telemetry path: `{models.telemetryRoot}/sessions.jsonl` (default `temp/qa/model-usage/`).

## Cross-platform hooks (`ORDIA-D008`)

The bundle template uses `{PYTHON}` in `hooks.json` hook commands. When you run
`ordia init --with-cursor`, Ordia replaces `{PYTHON}` with **`sys.executable`**
(the same Python interpreter that ran init). This avoids Windows-only `py -3` or
assumptions about `python3` on PATH.

After init, verify hooks with:

```powershell
npm run ordia:doctor -- --directory <your-project>
```

Doctor reports hook command invocability and flags any unresolved `{PYTHON}`
placeholder.

Greenfield hooks load the manifest via the vendored inline loader in
`.cursor/hooks/lib/ordia_manifest.py`. Optional full `ordia-core` via
`pip install -e packages/ordia-core` adds CLI and extended validation.

## Usage

From a repo with `packages/ordia-core`:

```powershell
npm run ordia:init -- --profile myapp --with-cursor --directory ../my-greenfield
```

Or copy `templates/` into `.cursor/` manually (replace `{PYTHON}` with your
Python executable path).

## Drift sync

When changing live `.cursor/hooks` or `.cursor/rules/ordia-*.mdc` in the
reference repo:

```powershell
python scripts/sync_ordia_cursor_bundle.py --check
python scripts/sync_ordia_cursor_bundle.py --sync
```

Synced hook files include `model_routing_lite.py` — keep in sync with
`ordia.model_routing.registry.model_slug_to_tier`.

## Requirements

- Python 3.10+ for hook scripts
- `ordia.yaml` at repository root (including `models:` block)
- `MODEL_REGISTRY.yaml` under control root
- Protocol stubs under `{control.root}/protocols/` (installed by `ordia init`)

Future publish target: `@ordia/cursor` (Cursor marketplace extension).
