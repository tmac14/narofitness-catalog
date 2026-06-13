# ENGINEERING-QUALITY-TOOLING

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: tool execution, existing tests/build, CI configuration audit, and
  project-control checker
- Status: `CLOSED`
- Task ID: `QUALITY-TOOLING-FOUNDATIONS-AND-BASELINE`
- Decision: `ENG-D001` approved by explicit PR-05 start on 2026-06-13

## Objective

Enforce `docs/ENGINEERING_STANDARDS.md` with project-owned lint, format,
typecheck, and CI quality gates.

## Approved Stack

- Frontend/tooling: ESLint flat config, `typescript-eslint` typed linting,
  React Hooks rules, Prettier, and `tsc --noEmit`.
- Python: Ruff lint/format and Pyright.
- Root scripts: domain-specific checks plus aggregate baseline and future
  blocking quality gates.
- CI: non-blocking baseline jobs in PR-05; blocking gates only after
  remediation.

## Risks

- dependency and lockfile changes;
- broad formatting diffs;
- pre-existing violations;
- false confidence if tools are configured but not run in CI.
- YAML parsers accepting duplicate mapping keys silently; add strict
  duplicate-key validation to the canonical project-control checker.

## Recommended Rollout

1. PR-05: audit-only configuration, dependencies, commands, CI baseline, and
   measured debt.
2. PR-06: frontend lint/type/format remediation.
3. PR-07: Python Ruff remediation.
4. PR-08: Python type-safety remediation.
5. PR-09: dependency hygiene.
6. PR-10: blocking CI enforcement.

## Approved PR-05 Plan

1. Add project-owned ESLint, Prettier, Ruff, and Pyright configuration.
2. Add canonical commands and dependency manifests/lockfiles.
3. Add non-blocking CI baseline steps that still expose failures clearly.
4. Run each tool and record exact baseline counts.
5. Preserve existing tests/build/control behavior.
6. Do not mass-format or remediate product code in this PR.

- Plan status: `APPROVED`
- Approval source: explicit user start of PR-05
- Approval date: 2026-06-13
- Lock gate: `CONFIRMED_NONE_REQUIRED`
- Ready gate: `READY_FOR_IMPLEMENTATION`

## Scope

- Allowed:
  - root and desktop package manifests/lockfiles;
  - lint, format, typecheck, and CI configuration;
  - Python development-tool requirements;
  - canonical command and engineering-standard documentation;
  - control records and this task packet.
- Blocked:
  - broad formatting or product-code remediation;
  - backend/frontend behavior changes;
  - migrations, data, importer behavior, and paused-track activation;
  - blocking CI enforcement before remediation.

## Acceptance Criteria

- [x] Selected tools install reproducibly.
- [x] Canonical domain and aggregate commands exist.
- [x] CI executes baseline quality checks non-blockingly.
- [x] Baseline debt is measured and recorded by domain/tool.
- [x] Existing frontend tests/build and control validation pass.
- [x] No broad product-code formatting or remediation is introduced.
- [x] Follow-up PR boundaries are explicit.

## Implemented Foundations

- Frontend/tooling:
  - ESLint `9.39.4` flat config;
  - `typescript-eslint` `8.61.0` typed rules;
  - React Hooks `7.1.1` and React Refresh rules;
  - Prettier `3.8.4`;
  - canonical `tsc --noEmit` command.
- Python:
  - Ruff `0.15.17`, pinned in `apps/api/requirements-dev.txt`;
  - Pyright `1.1.410`, pinned in the root npm lockfile;
  - Python `3.12` target and standard type-checking mode.
- Repository control:
  - domain-specific and aggregate quality commands;
  - non-blocking `quality-baseline` CI checks;
  - future strict `quality:check` command;
  - duplicate YAML mapping keys rejected by the canonical control loader and
    covered by focused tests.

## Baseline Debt

| Domain / tool | Measured baseline |
|---|---:|
| Frontend ESLint | 121 errors, 18 warnings, 45 files |
| Frontend Prettier | 194 files needing formatting |
| Frontend TypeScript | 57 errors across 19 files |
| Python Ruff lint | 335 findings, 227 fixable, 153 files |
| Python Ruff format | 140 files needing formatting; 93 already formatted |
| Python Pyright | 470 errors, 0 warnings, 233 files analyzed |

`npm run quality:baseline` reports all six debt areas and exits `0`.
`npm run quality:check` runs the same checks and exits non-zero until the
approved remediation sequence is complete.

## Validation Evidence

- Evidence ID: `EVID-CTRL-008`.
- Root `npm ci`: PASS.
- Desktop lockfile consistency: `npm ci --dry-run --ignore-scripts` PASS.
- Desktop dependency installation: PASS.
- Direct local desktop `npm ci`: blocked by an already-running
  `esbuild.exe`; no process was terminated. Clean CI uses `npm ci`.
- Desktop tests: PASS (`47` files, `367` tests).
- Desktop production build: PASS (`2026` modules transformed).
- CI configuration audit: PASS; six debt checks are non-blocking, while
  project-control validation/tests remain blocking.
- `npm run control:test`: PASS (`2/2`), including duplicate-key rejection.
- `npm run control:validate`: PASS (`19` tasks, `7` operational agents,
  `0` warnings, `0` errors).
- Strict YAML unique-key audit: PASS.
- No product code was formatted, fixed, or behaviorally changed.
- Desktop npm audit reported `14` dependency vulnerabilities; remediation is
  reserved for PR-09 dependency hygiene.

## Follow-Up Boundaries

1. PR-06: frontend lint, type, and format remediation.
2. PR-07: Python Ruff remediation.
3. PR-08: Python type-safety remediation.
4. PR-09: dependency hygiene, including npm audit findings.
5. PR-10: convert quality checks into blocking CI gates.

## Next Safe Action

No action. PR-05 is implemented, validated, and closed. Explicitly start PR-06
before remediating frontend debt.
