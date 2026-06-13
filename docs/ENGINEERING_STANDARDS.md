# Engineering Standards

Canonical engineering and naming standards for Narofitness/PIM.

## 1. Language

- Code identifiers, code comments, tests, technical documentation, API fields,
  task IDs, logs, and commit messages use English.
- Product UI copy uses Spanish unless a feature explicitly targets another
  locale.
- Supplier source text may remain unchanged when it is evidence or imported
  data.
- Do not translate canonical SKU, category, or supplier evidence silently.

## 2. General Design

- Prefer simple, explicit, forward-facing designs.
- No legacy compatibility or fallback paths unless explicitly approved.
- No productive hardcodes by SKU, page, or one-off catalog row.
- Convert repeated exceptions into auditable configuration or systemic rules.
- Keep modules cohesive and dependencies directional.
- Separate domain logic, persistence, transport, and presentation concerns.
- Avoid hidden mutation, implicit global state, and silent failure.
- Validate at boundaries and preserve traceability to source data.
- Optimize only after measuring; prevent N+1 queries by design.

## 3. Repository Naming

| Item | Convention |
|---|---|
| Task IDs | `UPPER-KEBAB-CASE`, scoped by track |
| Decision IDs | `<AREA>-D<number>` or stable control ID |
| Evidence IDs | `EVID-<AREA>-<number>` |
| Markdown policy files | `UPPER_SNAKE_CASE.md` |
| Task packet files | Exact task ID: `<TASK-ID>.md` |
| Python modules | `snake_case.py` |
| Python tests | `test_<behavior>.py` |
| React components/pages | `PascalCase.tsx` |
| React hooks | `useCamelCase.ts` |
| TypeScript utilities | `camelCase.ts` |
| TypeScript tests | `<module>.test.ts` or `<surface>.test.tsx` |
| Database tables/columns | `snake_case` |
| API JSON fields | `snake_case` |
| Environment variables/constants | `UPPER_SNAKE_CASE` |

Use domain language, not implementation accidents. Names must describe intent,
not temporary mechanics.

## 4. Python / FastAPI / SQLAlchemy

- Follow PEP 8 and modern Python typing.
- Functions, variables, and modules use `snake_case`; classes use `PascalCase`.
- Add return types to public and non-trivial functions.
- Prefer small pure helpers for parsing, normalization, and policy decisions.
- Routers handle HTTP concerns; services own domain behavior.
- Pydantic schemas define API boundaries; do not leak ORM objects accidentally.
- SQLAlchemy queries must avoid per-row database access in loops.
- Transactions and destructive operations must be explicit.
- Seeds must be deterministic and idempotent.
- Alembic migrations remain linear, reviewable, and independently testable.
- Catch only exceptions that can be handled meaningfully; preserve root cause.
- Log operational context without leaking sensitive data.

## 5. TypeScript / React / Electron

- TypeScript remains strict; do not use `any` without a documented boundary.
- Components use `PascalCase`; hooks start with `use`; utilities use
  `camelCase`.
- Keep data access and API contracts out of visual components.
- Prefer explicit state machines or derived state over duplicated state.
- Effects synchronize external systems; they do not replace event handling.
- Do not add `useMemo` or `useCallback` by default.
- Preserve keyboard, focus, screen-reader, touch, and responsive behavior.
- Mobile and tablet are first-class; do not compress dense desktop tables into
  unusable layouts.
- Shared UI primitives require a per-file lock.
- User-visible copy is Spanish, concise, and plain-language.

## 6. APIs and Data

- API routes are versioned under `/api/v1`.
- Request and response changes require an explicit contract and tests.
- Additive fields require deterministic defaults.
- Persist source facts once; derive read models rather than duplicating data.
- Schema and migration changes require explicit approval.
- Category, grouping, and spec rules must be systemic and auditable.
- Import changes must preserve full-catalog metrics and mandatory regressions.

## 7. Tests and Validation

- Test observable behavior, contracts, regressions, and failure modes.
- Every bug fix requires a failing-before/passing-after proof when practical.
- Keep fixtures focused; SKU/page literals belong only in tests, fixtures, or
  audit evidence.
- Backend changes require targeted tests plus relevant API/import regressions.
- Frontend changes require tests, build, and runtime/visual QA when behavior is
  not fully testable.
- Importer changes separate focus pages, regression pages `11/12/13/14`, and
  the 65-page full-catalog gate.
- Never mark implementation as validated while mandatory evidence is pending.

## 8. Documentation and Control

- Follow `docs/DOCUMENTATION_GOVERNANCE.md`.
- Every non-trivial task requires discovery, an approved plan, locks, a task
  packet, validation, and durable evidence.
- Historical documents cannot override the live task registry.
- Update control documents only at material transitions.

## 9. Tooling Baseline

Currently enforced:

- TypeScript `strict: true`
- Vitest
- Pytest
- `.editorconfig`
- project-control consistency checker

Configured as non-blocking baseline checks:

- ESLint flat config with typed `typescript-eslint` and React Hooks rules
- Prettier format checks
- `tsc --noEmit`
- Ruff lint and format checks
- Pyright in standard mode
- CI quality-baseline steps with `continue-on-error: true`

Quality checks expose existing debt but do not authorize broad suppressions,
mass formatting, or unrelated remediation. `npm run quality:baseline` runs all
checks and exits successfully while reporting debt. `npm run quality:check`
uses the same checks and fails when debt exists; it becomes a blocking gate
only after the approved remediation sequence is complete.
