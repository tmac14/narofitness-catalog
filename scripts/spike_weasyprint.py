#!/usr/bin/env python3

"""Spike: generate sample catalog PDF via WeasyPrint (required)."""



from __future__ import annotations



import sys

from datetime import datetime

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "apps" / "api"))



from app.services.pdf_export import (  # noqa: E402

    PdfEngineError,

    export_catalog_pdf,

    pdf_engine_status,

    require_pdf_engine,

)



OUT = ROOT / "temp" / "spike_output.pdf"





def main() -> int:

    engine, error = pdf_engine_status()

    if not engine:

        print(f"ERROR: {error}", file=sys.stderr)

        return 1

    try:

        require_pdf_engine()

    except PdfEngineError as exc:

        print(f"ERROR: {exc}", file=sys.stderr)

        return 1



    sample = {

        "catalog_name": "Spike — Mayorista +20%",

        "generated_at": datetime.now().isoformat(),

        "iva_disclaimer": "Los precios indicados no incluyen el IVA",

        "catalog_template": "branded",

        "categories": [

            {

                "name": "CARDIO XEBEX",

                "products": [

                    {

                        "sku": "BIC010",

                        "name": "Bicicleta Air Bike 1000 Eco Xebex",

                        "brand": "Xebex",

                        "ean": None,

                        "image_url": None,

                        "price_display": "656,56 €",

                    }

                ],

            }

        ],

    }

    OUT.parent.mkdir(parents=True, exist_ok=True)

    engine_name, data = export_catalog_pdf(sample, OUT)

    print(f"Engine: {engine_name}")

    print(f"Output: {OUT} ({OUT.stat().st_size} bytes, {len(data)} bytes read)")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

