# Narofitness App Design System v2.0

**Owner:** Agent 1B (Global UI/UX Design System)  
**Status:** Phase A + B + C + D + E complete (dark-first theme, row tokens, polish pass)  
**Last updated:** 2026-06-08

Dark-first color system for the NaroCatalog desktop app, inspired by the Narofitness catalogue brand: carbon/graphite surfaces, white typography, controlled green accent.

---

## 1. Design principles

| Principle | Rule |
|-----------|------|
| **Dark-first** | Default app chrome is dark graphite; not a light SaaS theme |
| **Accent budget** | ~80% black/graphite neutrals, ~15% steel greys, ~5% green accent |
| **Green = brand action** | Primary buttons, active nav icon, focus ring — not large backgrounds |
| **Functional colors** | Warning = amber; error/destructive = red; success = teal-green (distinct from primary) |
| **PDF separation** | App UI is dark; preview iframe and exported PDF remain print-optimized light |

---

## 2. Brand primitives

Defined in [`apps/desktop/src/theme/narofitness-tokens.css`](../../apps/desktop/src/theme/narofitness-tokens.css).

| Token | Hex | Role |
|-------|-----|------|
| `nr-black` | `#050504` | App canvas |
| `nr-graphite` | `#111110` | Sidebar, titlebar |
| `nr-surface` | `#1A1B1A` | Cards, panels |
| `nr-surface-2` | `#272727` | Elevated surfaces, secondary buttons |
| `nr-border` | `#3B3D3E` | Default borders |
| `nr-border-soft` | `#515456` | Strong borders, table headers |
| `nr-text` | `#F2F2F2` | Primary text |
| `nr-text-muted` | `#AAABAB` | Secondary labels |
| `nr-text-subtle` | `#868786` | Placeholders, hints only |
| `nr-white` | `#F9F9F9` | Text on green buttons |
| `nr-green` | `#638B06` | Primary brand accent |
| `nr-green-bright` | `#699505` | Hover, soft accent foreground |
| `nr-green-dark` | `#2F4702` | Deep accent (sparingly) |
| `nr-green-soft-bg` | `#182208` | Selected nav, soft highlights |

---

## 3. Semantic token mapping

Tailwind/shadcn consume HSL triplets via `hsl(var(--token))`.

| Semantic | CSS variable | Maps to | Usage |
|----------|--------------|---------|-------|
| `background.app` | `--background` | nr-black | Main content area |
| `text.primary` | `--foreground` | nr-text | Body, headings |
| `background.sidebar` | `--card` | nr-graphite | Sidebar, titlebar, cards |
| `text.onCard` | `--card-foreground` | nr-text | Text on card surfaces |
| `accent.primary` | `--primary` | nr-green | Primary buttons |
| `accent.primaryForeground` | `--primary-foreground` | nr-white | Button labels |
| `button.secondary.bg` | `--secondary` | nr-surface-2 | Secondary buttons |
| `text.secondary` | `--muted-foreground` | nr-text-muted | Labels, table headers |
| `accent.soft` | `--accent` | nr-green-soft-bg | Active nav row background |
| `accent.softForeground` | `--accent-foreground` | nr-green-bright | Active nav text |
| `border.default` | `--border`, `--input` | nr-border | Dividers, inputs |
| `focus.ring` | `--ring` | nr-green-bright (lifted) | Focus-visible rings |
| `badge.success` | `--success` | teal-green | Success status (not CTA) |
| `badge.warning` | `--warning` | amber | Warnings |
| `badge.error` | `--destructive` | red | Errors, delete |

### Row / preview tokens (Phase C — wired)

| Token | Purpose | Tailwind alias |
|-------|---------|----------------|
| `--row-warning-bg` | Import review / warning rows, `.warning-panel` | `bg-row-warning` |
| `--row-error-bg` | Error / duplicate rows | `bg-row-error` |
| `--row-info-a-bg` | Price diff — only in tarifa A | `bg-row-infoA` |
| `--row-info-b-bg` | Price diff — only in tarifa B (steel neutral, not green) | `bg-row-infoB` |
| `--row-selected-bg` | Expanded / selected table rows | `bg-row-selected` |
| `--row-hover-bg` | Row hover overlay | `bg-row-hover` |
| `--preview-canvas` | PDF preview iframe (`#FFFFFF`) | `bg-preview-canvas` |

**Wired in:** `index.css` (import/diff rows, product table hover, variants zebra), `ui/table.tsx` (hover/selected), `ImportPage.tsx` (`.warning-panel`).

---

## 4. Usage rules

1. **Components use semantic Tailwind classes** (`bg-background`, `text-primary`, `border-border`) — not raw hex in TSX.
2. **Do not use green for destructive actions** — use `destructive` variant.
3. **Do not fill large table areas with green** — zebra stripes use `muted` / surface neutrals.
4. **Active navigation:** soft green background (`accent`) + green icon (`primary`) — not solid green sidebar.
5. **Success badges** (e.g. “Conexión activa”) use `success` variant, not primary button green styling.
6. **`nr-text-subtle`** only for placeholders and non-essential hints — not table cell body text.

---

## 5. Accessibility notes

| Pairing | Est. contrast | Use |
|---------|---------------|-----|
| `#F2F2F2` on `#1A1B1A` | ~14.5:1 | Primary body text |
| `#AAABAB` on `#111110` | ~7:1 | Labels, table headers |
| `#868786` on dark surfaces | ~4.1:1 | Placeholders only — not body copy |
| `#F9F9F9` on `#638B06` | ~5.1:1 | Primary button labels (AA) |
| Focus ring | `--ring` on `--background` offset | Must remain visible on all interactive elements |

Disabled controls: combine reduced opacity with `text-muted-foreground`.

---

## 6. PDF / export separation

| Surface | Theme | Owner |
|---------|-------|-------|
| App shell (Layout, sidebar) | Dark v2 | Agent 1B |
| PreviewWorkspace toolbar | Dark v2 (inherits tokens) | Agent 1B / 1A |
| Preview iframe (`.preview-workspace-frame`) | `--preview-canvas` white | Agent 1B |
| Generated PDF (`apps/api/app/pdf/templates/`) | Print light theme | **Agent 6 — not modified by v2 app theme** |

The dark app theme must **not** be forced into A4 PDF export. Future branded PDF styling is a separate Agent 6 track using brand greens on white paper.

---

## 7. Implementation phases

| Phase | Status | Scope |
|-------|--------|-------|
| **A** | Done | Token file + this document |
| **B** | Done | Shell dark flip, Sonner dark, color-scheme |
| **C** | Done | Row token wiring, warning panel, table hover/selected, badge borders |
| **D** | Done | Visual QA polish across app routes (inherited surfaces) |
| **E** | Done | Focus/disabled/form contrast, toasts, docs, SHARED-3 release ready |

## 9. Phase D/E polish (2026-06-08)

| Area | Change |
|------|--------|
| Form fields | `input`, `textarea`, `select` → `bg-secondary`, focus ring offset, disabled text |
| Buttons | Outline → `bg-card`; disabled opacity + muted text |
| Tabs | Active tab → `bg-card` + border (not black-on-muted) |
| Dialog | Close icon `text-muted-foreground` + hover |
| Badges | Default variant border; status borders (Phase C) retained |
| Toasts | `richColors` + semantic borders for success/error/warning |
| Error/empty states | Destructive border ring; explicit title foreground |
| Import steps card | Removed heavy green tint → neutral card |
| Focus | Checkbox/radio `accent-color`; skip-link ring offset |
| Sortable headers | Focus ring offset on dark backgrounds |

---

## 10. Related files

- [`apps/desktop/src/theme/narofitness-tokens.css`](../../apps/desktop/src/theme/narofitness-tokens.css)
- [`apps/desktop/src/index.css`](../../apps/desktop/src/index.css)
- [`apps/desktop/tailwind.config.cjs`](../../apps/desktop/tailwind.config.cjs)
- [`docs/coordination/TASK_HISTORY.md`](../coordination/TASK_HISTORY.md) — durable closure and recovery history
- [`docs/coordination/APP_WIDE_UX_SCOPE.md`](../coordination/APP_WIDE_UX_SCOPE.md) — Theme v2 implementation record

**Coordination closure (Agent 3, 2026-06-08):** Phases A–E complete; Agent 1A smoke PASS; 70/70 tests; PDF/export untouched (Agent 6). Presentation features (`show_description_column`, covers, paginated preview) are **out of scope** for v2 theme — separate Agent 2 → 6 → 1A/4 track.

---

## 11. App Status Bar (SHARED-4 Phase 1 / 1.1)

| Token | Value | Usage |
|-------|-------|-------|
| `--statusbar-height` | `2rem` | Fixed footer height |
| `--statusbar-bg` | `var(--nr-green)` | Center + right zones |
| `--statusbar-zone-system-bg` | `var(--nr-green-dark)` | Left/API anchor zone |
| `--statusbar-fg` | `var(--nr-white)` | Bar text and icons |
| `--statusbar-outer-border` | `rgba(5,5,4,0.92)` | Top outer border (visible against app canvas) |
| `--statusbar-separator` | `rgba(255,255,255,0.22)` | Vertical zone dividers |
| `--statusbar-highlight` | `rgba(255,255,255,0.08)` | Subtle inset top highlight |

**Zone layout:** left = system/API (darker green); center = operational message (main green); right = summary/chips (main green). Warnings use compact chips only.

Process Center panel uses dark `bg-card` graphite — not green.

Phase 2+ will add job registry; Phase 1 shows API/PDF health only.
