# Ordia Improvement Plan v0.6

**Status:** IN PROGRESS — Slice 1 DONE (2026-06-14)  
**Baseline:** [SPEC_v0.5.md](./SPEC_v0.5.md) (feature-complete monorepo baseline)  
**Target:** v0.6 — **excellence-grade** product: truthful docs, self-contained package manuals, portable command registry, rigorous `docs/` hygiene  
**Prior audit:** v0.5 QA report + post-v0.5 deep audit (51 tests PASS; 18+ gaps identified)

---

## 1. Executive summary

Ordia v0.5 delivers a working control plane but **overstates** several claims
(duplicate templates, incomplete closure gate, PyPI packaging, `AGENTS.md` drift).
Enforcement has operational bypasses (stale sessions, shell/git, non-product paths).
The package lacks **first-class self-documentation**. The repo’s command
infrastructure (`COMMANDS.md`, `commands.catalog.json`, `npm run help*`) is
**more mature than Ordia’s own CLI docs** and should become a **portable Ordia
capability**. The `docs/` tree contains pre-Ordia residue, Spanish orphans,
historical task closeouts, and inventory drift.

v0.6 converts audit findings into **three priority tiers (P0–P2)** and **six
workstreams**, estimated **6–8 implementation slices**.

| Tier | Goal | Exit gate |
|---|---|---|
| **P0 — Truth & integrity** | Docs match code; no duplicate sources; closure honest | Audit gaps G-A04, G-DOC01, G-CL01 closed or descoped with decision |
| **P1 — Package excellence** | `ordia-core` ships extensive docs; tests cover strict paths | ≥ 70 control/ordia tests; package-data in wheel |
| **P2 — Platform & hygiene** | Ordia Commands framework; `docs/` cleanup program complete | Command catalog validates; docs inventory 100% classified |

**Non-goals for v0.6:** execute PyPI/marketplace publish (use [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md)); rename Narofitness `docs/control/`; product code in `apps/**`.

---

## 2. Audit baseline (v0.6 entry)

### 2.1 Strengths (preserve)

| Area | Evidence |
|---|---|
| Session API + hooks | 12 hook tests; fail-closed header/edit guards |
| Manifest + validator | Generic `--project`; profile + closure modules |
| Greenfield E2E | 8 tests; inline manifest loader |
| Drift CI | `sync_ordia_cursor_bundle.py --check` in suite |
| Protocol templates | 6 files; init install |
| Codex MVE | Spike documented (`ORDIA-D012`) |
| Command catalog (repo) | 50+ npm scripts; `help:validate` sync gate |

### 2.2 Gaps to close in v0.6

| ID | Severity | Gap |
|---|---|---|
| G-A04 | **P0** | `docs/ordia/templates/` duplicates package templates (A-04 falsely DONE) |
| G-DOC01 | **P0** | `AGENTS.md` v0.2 links broken; omits v0.5 / ORDIA-D007–D013 |
| G-DOC02 | **P0** | Improvement plan metric "stale refs = 0" false |
| G-CL01 | **P0** | Closure gate missing validator PASS; `closure.validator` unused |
| G-PKG01 | **P1** | No `package-data`; version 0.4.0 vs program v0.5 |
| G-INIT02 | **P1** | `monorepo/minimal/` nested duplicate in template tree |
| G-REG01 | **P1** | AGENT_REGISTRY references 3/6 protocols |
| G-DOC03 | **P1** | Doctor does not verify hook invocability (SPEC overstates) |
| G-VAL01 | **P1** | `--strict-profile` / `--strict-closure` untested at CLI |
| G-CMD01 | **P2** | `ordia:*` npm scripts absent from `commands.catalog.json` |
| G-CMD02 | **P2** | No portable command registry in `@ordia/core` |
| G-DOC-CLN | **P2** | `docs/` lacks full-tree inventory; Spanish orphans; archive debt |
| G-ENF01 | **P2** | Stale session, shell/git bypass, profile mismatch non-blocking |
| G-PKG-DOC | **P1** | Package README minimal; no architecture/CLI/hooks manuals |

---

## 3. Target state (v0.6)

```text
packages/ordia-core/
├── ordia/                    # runtime (unchanged layout + commands module)
├── docs/                     # NEW — extensive self-documentation
│   ├── README.md             # index + reading order
│   ├── ARCHITECTURE.md
│   ├── MANIFEST.md
│   ├── CLI.md
│   ├── VALIDATOR.md
│   ├── HOOKS_AND_RULES.md
│   ├── PROTOCOLS.md
│   ├── COMMANDS.md           # Ordia command registry spec + core commands
│   ├── GREENFIELD.md
│   ├── REFERENCE_PROFILE.md
│   ├── TESTING.md
│   └── CHANGELOG.md
├── pyproject.toml            # 0.6.0 + package-data
└── ...

Greenfield / reference:
  ordia help                    → command index (COMMANDS.md parity)
  ordia help -- validate        → command detail
  ordia commands validate       → sync npm/catalog/manifest (profile adapter)

docs/ (repo):
  docs/README.md                → topology map (ordia | coordination | product | archive)
  docs/control/DOCUMENTATION_INVENTORY.md → covers ALL docs/** (not coordination-only)
  docs/ordia/templates/         → DELETED (single source: packages/ordia-core/ordia/templates/)
  docs/archive/                 → historical closeouts, migrated Spanish docs (explicit headers)
```

---

## 4. Workstreams

### Workstream A — P0 Truth & integrity

#### A-01 — Remove duplicate template source

| Field | Value |
|---|---|
| **Gap** | G-A04 |
| **Action** | Delete `docs/ordia/templates/**`; grep repo for references; update DECISION_LOG ORDIA-D003 footnote if needed |
| **Acceptance** | `rg "docs/ordia/templates"` = 0 outside historical archive headers |
| **Validation** | `npm run control:test` PASS |

#### A-02 — Reconcile top-level project docs

| Field | Value |
|---|---|
| **Gap** | G-DOC01, G-DOC02 |
| **Action** | Update `AGENTS.md` Ordia section → v0.6 baseline, fix links (`docs/ordia/README.md`, `ordia.yaml`), ORDIA-D001–D013; update `ordia.yaml` header comment; align `DOCUMENTATION_INVENTORY.md` Ordia row to v0.5+ |
| **Acceptance** | No broken relative links from `AGENTS.md`; version strings consistent |
| **Validation** | New `scripts/test_ordia_doc_links.py` or extend validator |

#### A-03 — Closure gate: implement or descope

| Field | Value |
|---|---|
| **Gap** | G-CL01 |
| **Options** | (a) **Implement:** run `closure.validator` command (subprocess) when task → VALIDATED; record PASS in evidence or warn; (b) **Descope:** update SPEC_v0.1, TASK_EXECUTION protocol, improvement plans to match 4-condition check only |
| **Decision** | Requires **ORDIA-D014** — **DECIDED:** subprocess warn / strict error |
| **Acceptance** | Code, specs, and validator behavior aligned; test added |
| **Default recommendation** | (a) lightweight: parse `closure.validator` from manifest, subprocess with timeout, warn on non-zero (strict mode → error) |

#### A-04 — Honest improvement-plan metrics

| Field | Value |
|---|---|
| **Action** | Add v0.6 plan; mark v0.5 retrospective notes where claims were overstated |
| **Acceptance** | No checkbox marked DONE without evidence command |

**Phase A exit gate:**

```powershell
npm run control:test
npm run control:validate
rg "docs/ordia/templates"   # zero hits
python scripts/ordia_cli.py validate --project
```

---

### Workstream B — P1 Package excellence

#### B-01 — PyPI-ready packaging

| Field | Value |
|---|---|
| **Gap** | G-PKG01 |
| **Action** | Bump `ordia-core` to **0.6.0**; add `[tool.setuptools.package-data]` for `ordia/templates/**`, `ordia/protocols/**`; add `LICENSE`; expose `ordia.__version__` |
| **Acceptance** | `pip wheel` + install in clean venv → `ordia init --with-cursor` works without monorepo |
| **Validation** | New `scripts/test_ordia_wheel.py` |

#### B-02 — Template tree hygiene

| Field | Value |
|---|---|
| **Gap** | G-INIT02 |
| **Action** | Remove `packages/ordia-core/ordia/templates/monorepo/minimal/`; verify `_copy_template_tree` output |
| **Acceptance** | Monorepo init creates no `<target>/minimal/` subtree |

#### B-03 — AGENT_REGISTRY protocol completeness

| Field | Value |
|---|---|
| **Gap** | G-REG01 |
| **Action** | Add CODEX + RECOVERY protocol paths to greenfield `AGENT_REGISTRY.yaml`; add second control_plane_runtime for Codex or document in RECOVERY only |
| **Acceptance** | `validate_control_plane_protocols` PASS on greenfield; test checks 6/6 files |

#### B-04 — Doctor accuracy

| Field | Value |
|---|---|
| **Gap** | G-DOC03 |
| **Action** | Either (a) smoke-run each hook with `--help` or dry-run probe, or (b) revise SPEC_v0.5 §7 to "checks placeholder and file presence" |
| **Recommendation** | (a) minimal: `subprocess.run([python, hook, '--help'], ...)` or parse first line |
| **Acceptance** | Doctor reports pass/fail per hook; test covers bad `{PYTHON}` |

#### B-05 — Test matrix expansion

| Field | Value |
|---|---|
| **Gap** | G-VAL01, audit §6 |
| **Action** | Add tests: `--strict-profile`, `--strict-closure` CLI; PyYAML missing; QA evidence paths; `session_start` recovery snippet; header deny path; `sync --sync`; 6/6 protocols |
| **Target** | ≥ **70** control/ordia tests |
| **Acceptance** | `npm run control:test` count ≥ 70 |

#### B-06 — Extensive package self-documentation

| Field | Value |
|---|---|
| **Gap** | G-PKG-DOC |
| **Action** | Create `packages/ordia-core/docs/` tree (see §6); ship in wheel via package-data; `ordia init` copies index to `docs/ordia/PACKAGE_DOCS/` or links in scaffold README |
| **Acceptance** | Every public module has a doc section; reading order ≤ 30 min to full understanding |
| **Quality bar** | Each doc: purpose, API surface, examples, failure modes, cross-links |

**Phase B exit gate:**

```powershell
npm run control:test                    # ≥ 70
cd packages/ordia-core && python -m build
pip install dist/ordia_core-0.6.0*.whl && ordia init --with-cursor -C %TEMP%\wheel-test
```

---

### Workstream C — P2 Ordia Commands framework

**Vision:** Replicate the **robustness of `COMMANDS.md`** as a portable Ordia
subsystem. Nearly all repo npm scripts are **candidates** for cataloging; Ordia
owns the **registry schema, validation, help CLI, and sync gates**; project
profiles own **command entries**.

#### C-01 — Command registry schema (`ORDIA-D015`)

| Field | Value |
|---|---|
| **Deliverable** | `packages/ordia-core/ordia/commands/schema.py` + JSON Schema `commands.catalog.v1.schema.json` |
| **Fields** | `meta`, `quickFlows`, `localUrls`, `sections[]`, `commands[]` with `name`, `description`, `examples`, `underlyingScript`, `flags`, `requires`, `related`, `profile`, `runtime` |
| **Sources** | Extract from `scripts/commands.catalog.json` (reference impl) |
| **Acceptance** | Schema validates existing Narofitness catalog without changes |

#### C-02 — Ordia CLI `help` subsystem

| Field | Value |
|---|---|
| **Commands** | `ordia help`, `ordia help -- <cmd>`, `ordia help --list`, `ordia commands validate` |
| **Implementation** | Port logic from `scripts/npm-help.mjs` + `validate-commands-catalog.mjs` to Python in `ordia/commands/` (stdlib + optional rich output) |
| **Acceptance** | `ordia help --list` shows control + ordia commands; `ordia commands validate` PASS on reference repo |

#### C-03 — Manifest integration

| Field | Value |
|---|---|
| **Action** | Add optional `commands:` section to `ordia.yaml` (v0.3 schema bump — **ORDIA-D016**) |
| **Fields** | `catalog: path/to/commands.catalog.json`, `npmPackage: package.json`, `validateOnControlCheck: true` |
| **Acceptance** | `ordia validate` warns if catalog path missing when section present; `control:validate` optionally runs command sync |

#### C-04 — Catalog completeness (reference profile)

| Field | Value |
|---|---|
| **Gap** | G-CMD01 |
| **Action** | Add to `commands.catalog.json`: `ordia`, `ordia:init`, `ordia:validate`, `ordia:doctor`, `sync_ordia_cursor_bundle` (if scripted), document in COMMANDS.md |
| **Acceptance** | `npm run help:validate` PASS; ordia commands discoverable via `npm run help -- ordia:validate` |

#### C-05 — Command taxonomy & export model

| Field | Value |
|---|---|
| **Layers** | |
| | **L1 Ordia Core** — `ordia:*`, `control:*`, `help:*` (portable) |
| | **L2 Quality** — `quality:*`, `lint:*`, `typecheck:*` (optional profile module) |
| | **L3 Domain** — `dev:*`, `db:*`, `audit:*`, `docker:*`, `tunnel:*`, `pack:*` (Narofitness profile; cataloged via same schema) |
| **Export rule** | Any command referenced in task packets, protocols, or agent prompts **must** appear in catalog + COMMANDS.md (or profile COMMANDS overlay) |
| **Deliverable** | `packages/ordia-core/docs/COMMANDS.md` — spec + L1 commands; Narofitness keeps root `COMMANDS.md` as **profile overlay** importing Ordia spec |
| **Acceptance** | Document lists 100% of L1 commands; inventory script reports L2/L3 coverage % |

#### C-06 — CI gate

| Field | Value |
|---|---|
| **Action** | Wire `ordia commands validate` into `control:test` or `control:validate` when manifest declares catalog |
| **Acceptance** | Drift between package.json and catalog fails control suite |

**Phase C exit gate:**

```powershell
npm run help:validate
python scripts/ordia_cli.py help --list
python scripts/ordia_cli.py commands validate
npm run control:test
```

---

### Workstream D — P2 Enforcement hardening (selective)

Not full hook parity; close **high-value** gaps without scope explosion.

#### D-01 — Session freshness policy (`ORDIA-D017`)

| Options | (a) TTL on `session-protocol.json`; (b) require header re-declaration when task ID in state changes; (c) document as accepted risk |
| **Recommendation** | (b) — re-persist when `active_task_id` in state differs from session metadata |
| **Acceptance** | Test: state task change → next change-capable prompt requires header or re-seed |

#### D-02 — Profile strict hook mode (optional manifest flag)

| Field | Value |
|---|---|
| **Action** | `enforcement.strictProfile: true` → deny edits when profile mismatch |
| **Default** | false (backward compatible) |
| **Acceptance** | Test + doc in HOOKS_AND_RULES.md |

#### D-03 — SPEC honesty for fail-open sessionStart

| Field | Value |
|---|---|
| **Action** | Document asymmetric fail-closed (header/edit) vs fail-open (sessionStart) in package docs |
| **Acceptance** | No SPEC claims universal fail-closed |

#### D-04 — Shell/git guard spike (optional P2 stretch)

| Field | Value |
|---|---|
| **Action** | Spike only: `preToolUse` matcher for `Shell` with deny patterns for `git commit`, `alembic`, destructive rm |
| **Decision** | ORDIA-D018 — scope vs maintenance cost |
| **Default** | Spike doc; implement only if user approves |

**Phase D exit gate:** tests for D-01/D-02; spike recorded if D-04 deferred.

---

### Workstream E — P2 Documentation cleanup program

**Problem:** `docs/` mixes CORE control, ACTIVE tracks, Spanish product docs,
historical PR closeouts, duplicates, and unclassified orphans. Pre-Ordia residue
conflicts with current English-canonical governance.

#### E-01 — Full-tree documentation inventory

| Field | Value |
|---|---|
| **Action** | Extend `DOCUMENTATION_INVENTORY.md` to cover **all** `docs/**` (not only coordination) |
| **Tooling** | New `scripts/audit_docs_inventory.py` — emit CSV/Markdown table: path, lifecycle, language, last_modified, inbound_links, classification |
| **Acceptance** | 100% of `docs/**` files classified |

#### E-02 — Topology and navigation

| Field | Value |
|---|---|
| **Deliverable** | `docs/README.md` — map: |
| | `docs/ordia/` — Ordia product specs & plans |
| | `docs/control/` — live control plane (Narofitness profile) |
| | `docs/design/` — product design system |
| | `docs/archive/` — **NEW** — historical, closeouts, migrated docs |
| | Root-level product docs — status per file |
| **Acceptance** | New contributor finds any doc in ≤ 2 clicks from `docs/README.md` |

#### E-03 — Classification batches (execute in order)

| Batch | Paths | Action |
|---|---|---|
| **E-3a DELETE** | `docs/ordia/templates/**` | Delete (**ORDIA-D021** / A-01) |
| **E-3b ARCHIVE** | `docs/control/tasks/RUNTIME-SYMMETRY-PR*.md`, `PROTOCOL-HARDENING-PR*.md`, completed program closeouts | Move → `docs/archive/coordination/tasks/` with `Status: ARCHIVED` header |
| **E-3c ARCHIVE** | `docs/control/PR-K-family-regex-design.md` | Move → `docs/archive/coordination/` (inventory already ARCHIVE_CANDIDATE) |
| **E-3d MIGRATE** | Spanish root docs: `ANALISIS_FUNCIONAL.md`, `ARQUITECTURA_TECNICA.md` | **ORDIA-D019:** translate → `docs/product/FUNCTIONAL_ANALYSIS.md`, `docs/product/TECHNICAL_ARCHITECTURE.md`; archive originals → `docs/archive/product/es/` |
| **E-3e CONSOLIDATE** | Manual QA docs (`MANUAL_QA_*.md`) | Single index `docs/qa/MANUAL_QA_INDEX.md`; keep files ACTIVE with cross-links |
| **E-3f REVIEW** | `docs/control/contracts/**` | Per-contract lifecycle when owning task VALIDATED; mark ARCHIVE_CANDIDATE if superseded |
| **E-3g FIX** | Stale SPEC §Next sections (v0.2, v0.3) | Add "Historical" banner or trim |
| **E-3h DEDUP** | Duplicate path entries (Windows `\` vs `/`) | Normalize links to forward slashes |

#### E-04 — Reference integrity gate

| Field | Value |
|---|---|
| **Action** | `scripts/audit_docs_links.py` — broken relative links, orphan files (zero inbound), stale task ID refs |
| **Wire** | Optional `--strict` in `control:validate` for Narofitness profile |
| **Acceptance** | Zero broken links in CORE + ACTIVE docs |

#### E-05 — Governance update

| Field | Value |
|---|---|
| **Action** | Update `DOCUMENTATION_GOVERNANCE.md` with archive policy, Ordia doc authority, command catalog requirement |
| **Acceptance** | Single lifecycle policy covers full `docs/` tree |

**Phase E exit gate:**

```powershell
python scripts/audit_docs_inventory.py --check   # 100% classified
python scripts/audit_docs_links.py --strict      # 0 broken links in CORE/ACTIVE
npm run control:validate
```

---

### Workstream F — P2 SPEC v0.6 & publish readiness

#### F-01 — Publish [SPEC_v0.6.md](./SPEC_v0.6.md)

Summarize: package docs, commands framework, cleanup, enforcement, version 0.6.0.

#### F-02 — Update [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md)

Bump target version 0.6.0; add package-docs and commands validate gates.

#### F-03 — CHANGELOG

Create `packages/ordia-core/docs/CHANGELOG.md` + root Ordia section.

**Phase F exit gate:** SPEC_v0.6 ACTIVE; publish checklist pre-publish gates all PASS.

---

## 5. Package documentation tree (B-06 detail)

Target: **≥ 15,000 words** across package docs; every doc follows template:
Purpose → Audience → Concepts → API/CLI → Examples → Failure modes → Related.

| Document | Contents |
|---|---|
| **README.md** | Index, quick start, reading order, links to specs |
| **ARCHITECTURE.md** | Layers, runtime matrix, data flow diagrams, profile model |
| **MANIFEST.md** | Full `ordia.yaml` schema v0.2 (+ v0.3 commands extension), path rules, examples |
| **CLI.md** | Every command/flag; npm passthrough; exit codes; Windows/PowerShell notes |
| **VALIDATOR.md** | All checks, strict flags, extension points, Narofitness wrapper pattern |
| **HOOKS_AND_RULES.md** | Hook events, fail-open/closed table, session API, path classification, UNIFIED |
| **PROTOCOLS.md** | Template list, routing matrix, init behavior, profile exceptions |
| **COMMANDS.md** | Registry schema, L1 commands, validate/help usage, profile overlay pattern |
| **GREENFIELD.md** | init flows, `--with-cursor`, doctor troubleshooting, no-monorepo path |
| **REFERENCE_PROFILE.md** | How Narofitness maps onto Ordia; what not to copy |
| **TESTING.md** | Test suites, adding tests, drift sync, wheel test |
| **CHANGELOG.md** | Semver history |

**Init behavior:** copy `packages/ordia-core/docs/README.md` + `GREENFIELD.md` to
greenfield `docs/ordia/` (optional full bundle via `--with-docs` flag — **ORDIA-D020**).

---

## 6. Ordia Commands — reference catalog (L1 seed)

Commands that **must** live in Ordia core catalog (portable across profiles):

| Command | Category | Notes |
|---|---|---|
| `ordia` / `ordia:init` / `ordia:validate` / `ordia:doctor` | ordia | CLI entrypoints |
| `control:install` / `control:validate` / `control:test` | control | Validator suite |
| `help` / `help:validate` / `help:list` | help | Catalog discovery |
| `ordia help` / `ordia commands validate` | ordia | New v0.6 CLI |

**Profile catalog (Narofitness — same schema, profile tag `narofitness`):**

| Section | Example commands | Count ~ |
|---|---|---|
| dev | `dev`, `dev:web`, `dev:fresh`, `setup`, `frontend:*` | 10 |
| docker | `docker:up`, `docker:down`, … | 8 |
| db | `db:migrate`, `db:seed:*`, `db:reset:*` | 9 |
| tunnel | `tunnel:start`, `tunnel:stop` | 2 |
| test | `test:api`, `test:api:integration`, `test:api:full` | 3 |
| quality | `quality:*`, `lint:*`, `typecheck:*` | 10 |
| audit | `audit:*` | 7 |
| pack | `pack:*`, `spike:pdf` | 4 |

**Total reference repo:** ~65 npm scripts — **100% catalog coverage** is a v0.6 metric.

---

## 7. Implementation sequence (slices)

```text
Slice 1 (P0):     A-01, A-02, A-04
Slice 2 (P0):     A-03 (closure — after ORDIA-D014)
Slice 3 (P1):     B-01, B-02, B-03, B-04
Slice 4 (P1):     B-05, B-06 (package docs — large)
Slice 5 (P2):     C-01, C-02, C-04, C-06
Slice 6 (P2):     C-03, C-05, F-01, F-02
Slice 7 (P2):     E-01, E-02, E-03a–c (archive batch)
Slice 8 (P2):     E-03d–h, E-04, E-05, D-01–D-03
Optional:         D-04 shell guard spike
```

**Parallel safety:** Slices 1–4 (package) avoid mass `docs/control/` moves.
Slice 7–8 (cleanup) require **orchestration lock** on `docs/**` — no concurrent
task editing coordination docs.

---

## 8. Decision checkpoints

**Status:** **CLOSED** — `ORDIA-D014`–`ORDIA-D021` recorded 2026-06-14 (user: all documentation in English).

| ID | Question | Decision |
|---|---|---|
| **ORDIA-D014** | Closure validator semantics | **Subprocess** from `closure.validator`; warn default; `--strict-closure` → error |
| **ORDIA-D015** | Command registry schema ownership | **Ordia core** JSON Schema + `ordia/commands/` |
| **ORDIA-D016** | `ordia.yaml` commands section | **Optional `commands:`** — additive schema **v0.3**; v0.2 remains valid |
| **ORDIA-D017** | Session freshness | **Re-declare headers** when active task ID in state changes; no TTL |
| **ORDIA-D018** | Shell/git hook guard | **Spike only** in v0.6 — no implementation |
| **ORDIA-D019** | Spanish root docs | **Translate to English** `docs/product/`; originals → `docs/archive/product/es/` |
| **ORDIA-D020** | Init copies full package docs | **`--with-docs`** optional flag |
| **ORDIA-D021** | Duplicate template source | **Delete** `docs/ordia/templates/`; package templates only |

Implementation may proceed with **Slice 1** once this section is closed.

### Slice 1 completion (2026-06-14)

| Item | Status |
|---|---|
| A-01 Delete `docs/ordia/templates/` | **DONE** (`ORDIA-D021`) |
| A-02 Reconcile `AGENTS.md`, `ordia.yaml`, inventory | **DONE** |
| A-04 v0.5 metric retrospective notes | **DONE** |
| `scripts/test_ordia_doc_links.py` | **DONE** (3 tests) |
| Evidence | `docs/archive/ordia/qa/v06/SLICE1_QA_REPORT.md` |

**Next:** Slice 2 — A-03 closure subprocess (`ORDIA-D014`)

### Slice 2 completion (2026-06-14)

| Item | Status |
|---|---|
| A-03 Closure subprocess (`closure.validator`) | **DONE** |
| Reentrancy guard (`ORDIA_CLOSURE_VALIDATOR_ACTIVE`) | **DONE** |
| Tests: warn / strict / skip / reentrant | **DONE** (+5 tests) |
| Evidence | `docs/archive/ordia/qa/v06/SLICE2_QA_REPORT.md` |

**Next:** Slice 3 — B-01, B-02, B-03, B-04 (packaging + template hygiene)

### Slice 3 completion (2026-06-14)

| Item | Status |
|---|---|
| B-01 PyPI packaging 0.6.0 + package-data + LICENSE | **DONE** |
| B-02 Remove `monorepo/minimal/` subtree | **DONE** (already absent) |
| B-03 AGENT_REGISTRY 6 protocols + Codex runtime | **DONE** |
| B-04 Doctor hook invocability (py_compile probe) | **DONE** |
| `scripts/test_ordia_wheel.py` | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE3_QA_REPORT.md` |

**Next:** Slice 4 — B-05, B-06 (tests expansion + package docs)

### Slice 4 completion (2026-06-14)

| Item | Status |
|---|---|
| B-05 Test matrix ≥70 | **DONE** (71 tests) |
| B-06 `packages/ordia-core/docs/` (12 manuals) | **DONE** |
| `--with-docs` on `ordia init` (ORDIA-D020) | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE4_QA_REPORT.md` |

**Next:** Slice 5 — Ordia Commands framework (C-01–C-06)

### Slice 5 completion (2026-06-14)

| Item | Status |
|---|---|
| C-01 Command registry schema in core | **DONE** |
| C-02 `ordia help` + `ordia commands validate` | **DONE** |
| C-03 Manifest `commands:` + control validate gate | **DONE** |
| C-04 Catalog ordia:* entries (G-CMD01) | **DONE** |
| C-05 L1/L2/L3 taxonomy in package COMMANDS.md | **DONE** |
| C-06 `test_ordia_commands.py` in control:test | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE5_QA_REPORT.md` |

**Next:** Slice 6 — C-03 polish, C-05 inventory, Workstream E/F (docs cleanup, SPEC v0.6)

### Slice 6 completion (2026-06-14)

| Item | Status |
|---|---|
| C-03 MANIFEST.md v0.2/v0.3 + commands loader docs | **DONE** |
| C-05 `audit_command_catalog_coverage.py` + L1/L2/L3 report | **DONE** |
| F-01 [SPEC_v0.6.md](./SPEC_v0.6.md) published | **DONE** |
| F-02 [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) bumped to 0.6.0 | **DONE** |
| Package docs CLI/CHANGELOG/COMMANDS updates | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE6_QA_REPORT.md` |

**Next:** Slice 7 — E-01, E-02, E-03a–c (docs inventory + archive batch)

### Slice 7 completion (2026-06-14)

| Item | Status |
|---|---|
| E-01 `audit_docs_inventory.py` + `docs/docs_inventory.yaml` (100% classified) | **DONE** |
| E-02 `docs/README.md` navigation map | **DONE** |
| E-03a Delete `docs/ordia/templates/` | **DONE** (already absent) |
| E-03b Archive RUNTIME-SYMMETRY + PROTOCOL-HARDENING closeouts | **DONE** |
| E-03c Archive PR-K-family-regex-design | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE7_QA_REPORT.md` |

**Next:** Slice 8 — E-03d–h, E-04, E-05 (Spanish migration, links gate, governance)

### Slice 8 completion (2026-06-14)

| Item | Status |
|---|---|
| E-03d Spanish → English product docs (`ORDIA-D019`) | **DONE** |
| E-03e `docs/qa/MANUAL_QA_INDEX.md` | **DONE** |
| E-03g Historical banners on SPEC v0.1–v0.4 | **DONE** |
| E-04 `audit_docs_links.py --strict` + control:validate wire | **DONE** |
| E-05 `DOCUMENTATION_GOVERNANCE.md` full-tree policy | **DONE** |
| Evidence | `docs/archive/ordia/qa/v06/SLICE8_QA_REPORT.md` |

**v0.6 program:** Slices 1–8 complete — Phase E exit gates PASS.

---

## 9. Metrics & definition of done (v0.6)

| Metric | v0.5 actual | v0.6 target |
|---|---|---|
| Control/Ordia tests | 51 | ≥ **70** → **76** |
| Package version | 0.4.0 | **0.6.0** |
| Wheel install greenfield E2E | untested | **PASS** |
| Duplicate template paths | 2 | **0** |
| `docs/ordia/templates` hits | >0 | **0** |
| Package doc word count | ~200 | ≥ **15,000** |
| npm scripts in catalog | ~50 (no ordia) | **100%** |
| `docs/**` classified | ~60% (coordination only) | **100%** (Slice 7–8) |
| Broken links CORE/ACTIVE | unknown | **0** (Slice 8) |
| AGENTS.md Ordia version | v0.2 (wrong) | **v0.6 aligned** |
| Closure gate honest | partial | **aligned** |
| SPEC_v0.6 published | — | **done** |

**v0.6 DONE when:**

- [ ] All Phase A–F exit gates PASS (E/F partial — Slices 7–8 pending)
- [x] SPEC_v0.6.md published
- [x] ORDIA-D014–D021 recorded (2026-06-14)
- [x] `packages/ordia-core/docs/` complete per §5
- [x] `ordia commands validate` PASS
- [ ] Docs inventory 100%; archive batch complete
- [x] QA reports in `docs/archive/ordia/qa/v06/` (Slices 1–6)

---

## 10. Scope boundaries

**In scope:**

```text
packages/ordia-core/**          (code + docs/)
packages/ordia-cursor/**
scripts/ordia*.py
scripts/audit_docs*.py          (new)
scripts/commands.catalog.json   (ordia entries)
scripts/test_ordia*.py
docs/ordia/**
docs/README.md                  (new)
docs/archive/**                 (new)
docs/control/DOCUMENTATION_INVENTORY.md
docs/DOCUMENTATION_GOVERNANCE.md
AGENTS.md                       (Ordia section + links)
COMMANDS.md                     (ordia section + taxonomy note)
ordia.yaml                      (commands section if D-016 approved)
```

**Out of scope:**

```text
apps/**                         product code
IMPORT-FDL / UX30 tracks        unless docs-only cleanup
PyPI/marketplace publish execution
Renaming docs/control/
Full shell hook guard           unless D-018 approved
```

**Forbidden without explicit task:**

- Deleting CORE coordination docs
- Changing task VALIDATED status
- Mixing orchestration + implementation in one slice

---

## 11. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Docs cleanup breaks agent recovery paths | Medium | High | Archive don't delete; link redirects; audit_links gate |
| Command catalog drift | Medium | Medium | CI validate; control:test |
| Manifest v0.3 schema bump breaks greenfield | Low | High | Optional section; SUPPORTED_VERSIONS additive |
| Package doc maintenance burden | Medium | Low | Generate CLI/validator sections from docstrings where possible |
| Scope creep into enforcement perfection | High | Medium | D-018 default spike-only; document accepted risks |
| Spanish doc migration controversy | Medium | Low | D-019 user decision before E-3d |

---

## 12. Executor prompt template

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Task ID: ORDIA-V06-SLICE-<N>

You are implementing Ordia v0.6 Slice <N> per docs/ordia/IMPROVEMENT_PLAN_v0.6.md.

Objective: <workstream items>
Allowed scope: per §10 In scope
Forbidden: per §10 Out of scope

Decisions required: <ORDIA-D014–D021 if applicable>

Mandatory validation:
  npm run control:test
  npm run control:validate
  npm run help:validate          (if touching catalog)
  python scripts/ordia_cli.py validate --project

Return: verdict, files changed, tests run, metrics, risks, scope confirmation.
```

---

## 13. Related documents

| Document | Role |
|---|---|
| [IMPROVEMENT_PLAN v0.5 (archived)](../archive/ordia/specs/IMPROVEMENT_PLAN_v0.5.md) | Completed baseline |
| [SPEC_v0.5.md](./SPEC_v0.5.md) | Current spec until v0.6 ships |
| [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) | Post-v0.6 publish execution |
| [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md) | Codex MVE (unchanged) |
| [../DOCUMENTATION_GOVERNANCE.md](../DOCUMENTATION_GOVERNANCE.md) | Cleanup policy |
| [../control/COMMANDS.md](../control/COMMANDS.md) | Reference command catalog |
