"""Heuristics for variant candidates that were not grouped correctly."""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

WEIGHT_IN_NAME = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?", re.I)

ONE_PER_SKU_REASONS = frozenset(
    {
        "one_per_sku",
        "one_per_sku_fallback",
        "explicit_one_per_sku",
    }
)

FALLBACK_REASONS = ONE_PER_SKU_REASONS | {"regex_fallback_1_1"}

PREFIX_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("DOP4A", re.compile(r"^DOP4A(?P<size>\d{3})$", re.I)),
    ("DOPH", re.compile(r"^DOPH(?P<size>\d{3})$", re.I)),
    ("DOP", re.compile(r"^DOP(?P<size>\d{3})$", re.I)),
    ("DNG", re.compile(r"^DNG(?P<size>\d{3})$", re.I)),
    ("MPS", re.compile(r"^MPS(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("MH", re.compile(r"^MH(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("MU", re.compile(r"^MU(?P<size>\d{3})$", re.I)),
    ("MP", re.compile(r"^MP(?P<size>\d{3})$", re.I)),
    ("DOBN", re.compile(r"^DOBN(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$", re.I)),
    ("DOB", re.compile(r"^DOB(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$", re.I)),
]

SKU_FAMILY_REGEX = re.compile(
    r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    re.I,
)
REPUESTO_SKU_RE = re.compile(r"^REPUESTO-\d+$", re.I)


def _alpha_prefix(sku: str, min_len: int = 3) -> str | None:
    upper = (sku or "").upper()
    alpha = "".join(c for c in upper if c.isalpha())
    if len(alpha) < min_len:
        return None
    return alpha[:8]


def _match_family_prefix(sku: str) -> str | None:
    upper = (sku or "").upper()
    for name, pattern in PREFIX_PATTERNS:
        if pattern.match(upper):
            return name
    m = SKU_FAMILY_REGEX.match(upper)
    if m:
        return f"{m.group('prefix')}{m.group('suffix')}"
    return None


def _name_stem(name: str) -> str:
    stem = WEIGHT_IN_NAME.sub("", name or "").strip().lower()
    return re.sub(r"\s+", " ", stem)


def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _name_stem(a), _name_stem(b)).ratio()


def _weights_in_name(name: str) -> list[str]:
    return WEIGHT_IN_NAME.findall(name or "")


def detect_suspicious_variants(
    audited_rows: list[dict[str, Any]],
    *,
    grouping_config: dict[str, Any],
    unparsed_by_page: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[int, list[str]]]:
    """Return suspicious candidates and per-row suspicion flag map."""
    suspicion_flags: dict[int, list[str]] = defaultdict(list)
    candidates: list[dict[str, Any]] = []
    candidate_id = 0

    rows_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in audited_rows:
        page = row.get("page_number") or 0
        rows_by_page[page].append(row)

    sku_master_regex = grouping_config.get(
        "sku_master_regex",
        r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    )
    family_re = re.compile(sku_master_regex, re.I)

    # SamePageSkuFamily
    for page, page_rows in rows_by_page.items():
        prefix_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in page_rows:
            sku = row.get("normalized_sku") or ""
            prefix = _alpha_prefix(sku)
            if prefix and re.search(r"\d", sku):
                prefix_groups[prefix].append(row)

        for prefix, group in prefix_groups.items():
            if len(group) < 2:
                continue
            master_keys = {r.get("proposed_master_key") for r in group}
            if len(master_keys) <= 1:
                continue
            skus = [r.get("normalized_sku") for r in group]
            if all(REPUESTO_SKU_RE.match(sku or "") for sku in skus):
                continue
            candidate_id += 1
            sid = f"S-{candidate_id:04d}"
            for r in group:
                idx = r.get("source_row_index")
                if idx is not None:
                    suspicion_flags[idx].append("SamePageSkuFamily")
            candidates.append(
                {
                    "suspicion_id": sid,
                    "heuristic": "SamePageSkuFamily",
                    "page_numbers": [page],
                    "skus": skus,
                    "current_master_keys": [r.get("proposed_master_key") for r in group],
                    "expected_master_key": prefix,
                    "grouping_reasons": [r.get("grouping_reason") for r in group],
                    "possible_false_negative": True,
                }
            )

    # RegexFamilyMismatch
    for row in audited_rows:
        sku = row.get("normalized_sku") or ""
        if not sku:
            continue
        grouping_reason = row.get("grouping_reason") or ""
        if grouping_reason.startswith("fdl_sku_family:") or grouping_reason.startswith(
            "numeric_suffix_family:"
        ):
            continue
        if grouping_reason.startswith("false_family:"):
            continue
        if (
            grouping_reason not in FALLBACK_REASONS
            and "regex_fallback" not in (row.get("review_reasons") or [])
            and grouping_reason not in ONE_PER_SKU_REASONS
        ):
            continue

        expected: str | None = None
        m = family_re.match(sku)
        expected = f"{m.group('prefix')}{m.group('suffix')}" if m else _match_family_prefix(sku)

        if not expected or row.get("proposed_master_key") == expected:
            continue

        candidate_id += 1
        sid = f"S-{candidate_id:04d}"
        idx = row.get("source_row_index")
        if idx is not None:
            suspicion_flags[idx].append("RegexFamilyMismatch")
        candidates.append(
            {
                "suspicion_id": sid,
                "heuristic": "RegexFamilyMismatch",
                "page_numbers": [row.get("page_number")],
                "skus": [sku],
                "current_master_keys": [row.get("proposed_master_key")],
                "expected_master_key": expected,
                "grouping_reasons": [grouping_reason],
                "possible_false_negative": True,
            }
        )

    # NumericSuffixSplit
    numeric_re = re.compile(
        grouping_config.get(
            "numeric_suffix_family_regex",
            r"^(?P<prefix>DOP4A|DOPH|DNG|DOP|MPS|MU|MP)(?P<size>\d{3})$",
        ),
        re.I,
    )
    prefix_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audited_rows:
        sku = row.get("normalized_sku") or ""
        m = numeric_re.match(sku)
        if m:
            prefix_groups[m.group("prefix").upper()].append(row)

    for prefix, group in prefix_groups.items():
        if len(group) < 2:
            continue
        master_keys = {r.get("proposed_master_key") for r in group}
        if len(master_keys) == 1 and prefix in master_keys:
            continue
        if all(r.get("proposed_master_key") == r.get("normalized_sku") for r in group):
            candidate_id += 1
            sid = f"S-{candidate_id:04d}"
            for r in group:
                idx = r.get("source_row_index")
                if idx is not None:
                    suspicion_flags[idx].append("NumericSuffixSplit")
            candidates.append(
                {
                    "suspicion_id": sid,
                    "heuristic": "NumericSuffixSplit",
                    "page_numbers": sorted({r.get("page_number") for r in group}),
                    "skus": [r.get("normalized_sku") for r in group],
                    "current_master_keys": [r.get("proposed_master_key") for r in group],
                    "expected_master_key": prefix,
                    "grouping_reasons": [r.get("grouping_reason") for r in group],
                    "possible_false_negative": True,
                }
            )

    # NameWeightLadder
    name_groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in audited_rows:
        page = row.get("page_number") or 0
        stem = _name_stem(row.get("normalized_name") or "")
        if stem and _weights_in_name(row.get("normalized_name") or ""):
            name_groups[(page, stem[:40])].append(row)

    for (_page, _stem), group in name_groups.items():
        if len(group) < 2:
            continue
        weights = set()
        for r in group:
            weights.update(_weights_in_name(r.get("normalized_name") or ""))
        if len(weights) < 2:
            continue
        missing_spec = any(
            not (r.get("inferred_attributes") or {}).get("variant_specs", {}).get("peso_kg")
            for r in group
        )
        master_keys = {r.get("proposed_master_key") for r in group}
        if len(master_keys) <= 1 and not missing_spec:
            continue
        candidate_id += 1
        sid = f"S-{candidate_id:04d}"
        for r in group:
            idx = r.get("source_row_index")
            if idx is not None:
                suspicion_flags[idx].append("NameWeightLadder")
        candidates.append(
            {
                "suspicion_id": sid,
                "heuristic": "NameWeightLadder",
                "page_numbers": sorted({r.get("page_number") for r in group}),
                "skus": [r.get("normalized_sku") for r in group],
                "current_master_keys": [r.get("proposed_master_key") for r in group],
                "expected_master_key": None,
                "grouping_reasons": [r.get("grouping_reason") for r in group],
                "possible_false_negative": len(master_keys) > 1 or missing_spec,
            }
        )

    # OrphanSibling
    for row in audited_rows:
        page = row.get("page_number") or 0
        sku = row.get("normalized_sku") or ""
        prefix = _alpha_prefix(sku)
        if not prefix:
            continue
        orphans = unparsed_by_page.get(page, [])
        orphan_prefixes = set()
        for orphan in orphans:
            text = orphan.get("text", "")
            for token in text.split():
                if token.upper().startswith(prefix[:3]) and re.search(r"\d", token):
                    orphan_prefixes.add(token.upper())
        if not orphan_prefixes:
            continue
        if row.get("normalized_sku") in orphan_prefixes:
            continue
        candidate_id += 1
        sid = f"S-{candidate_id:04d}"
        idx = row.get("source_row_index")
        if idx is not None:
            suspicion_flags[idx].append("OrphanSibling")
        candidates.append(
            {
                "suspicion_id": sid,
                "heuristic": "OrphanSibling",
                "page_numbers": [page],
                "skus": [sku],
                "current_master_keys": [row.get("proposed_master_key")],
                "expected_master_key": prefix,
                "grouping_reasons": [row.get("grouping_reason")],
                "orphan_lines": list(orphan_prefixes)[:5],
                "possible_false_negative": True,
            }
        )

    return candidates, dict(suspicion_flags)


def build_groups_detected(audited_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_master: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audited_rows:
        mk = row.get("proposed_master_key")
        if mk:
            by_master[mk].append(row)

    groups = []
    for master_key, members in sorted(by_master.items()):
        if len(members) < 2:
            continue
        groups.append(
            {
                "proposed_master_key": master_key,
                "member_count": len(members),
                "skus": [m.get("normalized_sku") for m in members],
                "pages": sorted({m.get("page_number") for m in members}),
                "grouping_reason": members[0].get("grouping_reason"),
                "variant_axes": members[0].get("variant_axes") or [],
                "all_confirmable": all(
                    (m.get("final_decision") or {}).get("can_confirm") for m in members
                ),
            }
        )
    return groups
