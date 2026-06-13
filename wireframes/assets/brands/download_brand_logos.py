#!/usr/bin/env python3
"""Descarga temporal de logos de marcas FDL para wireframes."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

BRANDS: list[dict[str, str]] = [
    {
        "slug": "xebex",
        "filename": "xebex.png",
        "url": "https://xebexfitness.com/wp-content/uploads/xebex.png",
        "source": "xebexfitness.com",
    },
    {
        "slug": "reebok",
        "filename": "reebok.png",
        "url": "https://www.reebok.eu/cdn/shop/files/Reebok-Logo-300x300.png",
        "source": "reebok.eu",
    },
    {
        "slug": "reebok",
        "filename": "reebok.svg",
        "url": "https://news.reebok.com/dist/images/reebok-logo-header.svg",
        "source": "news.reebok.com",
    },
    {
        "slug": "adidas",
        "filename": "adidas.svg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Adidas_2022_logo.svg",
        "source": "wikimedia-commons (vector basado en adidas.com; sin kit de prensa público directo)",
    },
    {
        "slug": "horizon",
        "filename": "horizon.png",
        "url": "https://www.horizonfitness.com/cdn/shop/files/Type_Lockup_Color_White_35e324c8-6b1a-426c-8af0-6d10a4bf23d7.png?v=1749684038&width=1100",
        "source": "horizonfitness.com",
    },
    {
        "slug": "nexo",
        "filename": "nexo.png",
        "url": "https://nexostrength.com/wp-content/uploads/2025/01/NEXO_st_ultimo.png",
        "source": "nexostrength.com",
    },
    {
        "slug": "fdl",
        "filename": "fdl.png",
        "url": "https://fitnessdeluxe.es/wp-content/uploads/2021/02/fdl-logo-pie01.png",
        "source": "fitnessdeluxe.es",
    },
]


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            dest.write_bytes(resp.read())


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []

    for item in BRANDS:
        dest = ROOT / item["filename"]
        try:
            download(item["url"], dest)
            status = "ok"
            error = ""
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            status = "error"
            error = str(exc)

        manifest.append(
            {
                "slug": item["slug"],
                "filename": item["filename"],
                "url": item["url"],
                "source": item["source"],
                "status": status,
                "error": error,
                "bytes": dest.stat().st_size if dest.exists() else 0,
            }
        )
        print(f"[{status}] {item['filename']} <- {item['url']}")
        if error:
            print(f"       {error}")

    (ROOT / "sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if all(m["status"] == "ok" for m in manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
