# B3B Profile Eligibility Audit

**Status:** `B3B_PROFILE_ELIGIBILITY_AUDIT_COMPLETE`

## Categories without profile
| Slug | Variants | Classification |
|------|----------|----------------|
| material-de-estudio | 269 | PROFILE_READY_LOW_RISK |
| elipticas | 5 | PROFILE_NOT_USEFUL |
| soportes-y-mancuerneros | 1 | PROFILE_NOT_USEFUL |

## Low-risk candidates

- **material-de-estudio**: peso_kg persisted on 57/269 variants (21.2%)
  - `{"category_slug": "material-de-estudio", "spec_key": "peso_kg", "is_variant_axis_candidate": true, "is_required": false, "is_highlight": false, "sort_order": 10, "print_group": "variant"}`

## Taxonomy without FDL products

See `taxonomy_empty_categories.json`. **musculacion**, home, agarres, boxeo, suelos, racks, repuestos, and several cardio subcats have **0 importables** in Tarifa 2026.

## Previously cited candidates

| Category | Verdict |
|----------|---------|
| material-de-estudio | PROFILE_READY_LOW_RISK (peso_kg only) |
| elipticas | PROFILE_NOT_USEFUL (0 specs; 5 singletons) |
| musculacion | NO_PROFILE_NEEDED (0 products in catalog) |

## Color on material-de-estudio

65 variants persist `color` but printable discovery currently surfaces only `peso`. Adding `color` to profile → PROFILE_NEEDS_COMMERCIAL_DECISION (not approved in this audit).