#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import compute_stats, parse_pdf

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
    },
}

DEFAULT_PDF = ROOT / "temp" / "FDL .. Tarifa Mayorista 01-Febr-2026.pdf"


def main() -> int:
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    rows = parse_pdf(pdf_path)
    rows = apply_grouping(rows, FDL_CONFIG)
    stats = compute_stats(rows)
    keys = {}
    for r in rows:
        if r.master_key:
            keys.setdefault(r.master_key, []).append(r.sku)
    multi = {k: v for k, v in keys.items() if len(v) > 1}
    ok = stats.get("ok", 0)
    print(f"OK rate: {ok}/{len(rows)}")
    print(f"Masters with 2+ variants: {len(multi)}")
    if len(rows) > 0:
        assert ok / len(rows) >= 0.88, f"OK rate too low: {ok}/{len(rows)}"
    nexo = [r for r in rows if r.sku and r.sku.startswith("DOBNEXO") and "N" in (r.sku or "")]
    if len(nexo) >= 2:
        keys_nexo = {r.master_key for r in nexo}
        assert "DOBNEXON" in keys_nexo, f"Expected DOBNEXON grouping, got {keys_nexo}"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
