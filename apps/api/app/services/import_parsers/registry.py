from __future__ import annotations

from typing import BinaryIO, Protocol

from app.services.import_parsers.base import ImportRow


class ImportParser(Protocol):
    def parse(self, source: bytes | BinaryIO) -> list[ImportRow]: ...


def get_parser(parser_key: str):
    if parser_key == "fdl_pdf_v1":
        from app.services.import_parsers.fdl_pdf_v1 import parse_pdf

        return parse_pdf
    raise ValueError(f"Unknown parser_key: {parser_key}")
