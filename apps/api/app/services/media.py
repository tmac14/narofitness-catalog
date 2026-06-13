"""Product image storage under DATA_DIR."""

from __future__ import annotations

import asyncio
import ipaddress
import shutil
import socket
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import httpx
from fastapi import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_SCHEMES = {"javascript", "data", "file", "ftp"}
MAX_PRODUCT_IMAGE_BYTES = 5 * 1024 * 1024
MAX_EXTERNAL_URL_LENGTH = 2048
MAX_EXTERNAL_REDIRECTS = 3
EXTERNAL_CONNECT_TIMEOUT = 10.0
EXTERNAL_READ_TIMEOUT = 30.0

CONTENT_TYPE_SUFFIX = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ExternalImageError(ValueError):
    """Invalid external image URL or fetch failure."""


class ExternalImageTooLargeError(ExternalImageError):
    pass


class ExternalImageSsrfError(ExternalImageError):
    pass


def data_root() -> Path:
    root = Path(settings.data_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def product_images_dir(product_id: uuid.UUID) -> Path:
    d = data_root() / "images" / str(product_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def catalog_images_dir(catalog_id: uuid.UUID) -> Path:
    d = data_root() / "images" / "catalogs" / str(catalog_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def relative_image_path(product_id: uuid.UUID, filename: str) -> str:
    return f"images/{product_id}/{filename}"


def relative_catalog_image_path(catalog_id: uuid.UUID, filename: str) -> str:
    return f"images/catalogs/{catalog_id}/{filename}"


def absolute_image_path(relative: str) -> Path:
    return data_root() / relative


def media_url(relative: str) -> str:
    return f"/api/v1/media/{relative.replace(chr(92), '/')}"


def resolve_media_context_url(
    relative: str | None,
    *,
    for_html_preview: bool,
    api_base: str,
) -> str | None:
    if not relative:
        return None
    url = media_url(relative)
    return f"{api_base.rstrip('/')}{url}" if for_html_preview else relative


def _normalized_suffix(file: UploadFile) -> str:
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {suffix or '(none)'}")
    return suffix


async def save_product_image(product_id: uuid.UUID, file: UploadFile) -> tuple[str, str]:
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".jpg"
    content = await file.read()
    return save_product_image_bytes(product_id, content, suffix)


def save_product_image_bytes(product_id: uuid.UUID, content: bytes, suffix: str) -> tuple[str, str]:
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = product_images_dir(product_id) / filename
    dest.write_bytes(content)
    rel = relative_image_path(product_id, filename)
    return rel, media_url(rel)


async def save_catalog_image(catalog_id: uuid.UUID, file: UploadFile) -> tuple[str, str]:
    suffix = _normalized_suffix(file)
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = catalog_images_dir(catalog_id) / filename
    content = await file.read()
    dest.write_bytes(content)
    rel = relative_catalog_image_path(catalog_id, filename)
    return rel, media_url(rel)


def delete_image_file(relative: str) -> None:
    path = absolute_image_path(relative)
    if path.is_file():
        path.unlink()


def _normalize_external_url(raw: str) -> str:
    trimmed = raw.strip()
    if not trimmed:
        raise ExternalImageError("URL is required")
    if len(trimmed) > MAX_EXTERNAL_URL_LENGTH:
        raise ExternalImageError(f"URL exceeds maximum length of {MAX_EXTERNAL_URL_LENGTH}")

    parsed = urlparse(trimmed)
    scheme = (parsed.scheme or "").lower()
    if not scheme:
        raise ExternalImageError("URL must include http or https scheme")
    if scheme in BLOCKED_SCHEMES:
        raise ExternalImageError(f"URL scheme '{scheme}:' is not allowed")
    if scheme not in ALLOWED_SCHEMES:
        raise ExternalImageError(f"URL scheme '{scheme}' is not allowed; use http or https")
    if parsed.username or parsed.password:
        raise ExternalImageError("URL must not include user credentials")
    if not parsed.hostname:
        raise ExternalImageError("URL must include a host")

    normalized = urlunparse(
        (
            scheme,
            parsed.netloc.lower(),
            parsed.path or "",
            parsed.params,
            parsed.query,
            "",
        )
    )
    return normalized


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
        return True
    return ip == ipaddress.ip_address("169.254.169.254")


def normalize_external_image_url(raw: str) -> str:
    """Validate URL format/scheme; does not perform DNS/SSRF checks."""
    return _normalize_external_url(raw)


async def _resolve_host_ips_async(
    hostname: str,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    lowered = hostname.lower().strip(".")
    if lowered in {"localhost", "localhost.localdomain"}:
        return [ipaddress.ip_address("127.0.0.1")]

    try:
        return [ipaddress.ip_address(lowered)]
    except ValueError:
        pass

    def _lookup() -> list[tuple]:
        return socket.getaddrinfo(lowered, None, type=socket.SOCK_STREAM)

    results = await asyncio.to_thread(_lookup)
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for _family, _type, _proto, _canonname, sockaddr in results:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip not in ips:
            ips.append(ip)
    if not ips:
        raise ExternalImageError("Could not resolve URL host")
    return ips


async def assert_external_url_allowed(url: str) -> str:
    normalized = _normalize_external_url(url)
    parsed = urlparse(normalized)
    hostname = parsed.hostname
    if not hostname:
        raise ExternalImageError("URL must include a host")

    for ip in await _resolve_host_ips_async(hostname):
        if _is_blocked_ip(ip):
            raise ExternalImageSsrfError("URL host resolves to a blocked address")
    return normalized


def _suffix_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    base = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_SUFFIX.get(base)


def _suffix_from_url_path(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix == ".jpeg":
        return ".jpg"
    return suffix if suffix in ALLOWED_EXTENSIONS else None


def _validate_image_content_type(content_type: str | None) -> None:
    if not content_type:
        raise ExternalImageError("Remote response missing Content-Type")
    base = content_type.split(";", 1)[0].strip().lower()
    if not base.startswith("image/"):
        raise ExternalImageError(f"Remote Content-Type '{base}' is not an image")


async def _read_limited_response(response: httpx.Response) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > MAX_PRODUCT_IMAGE_BYTES:
            raise ExternalImageTooLargeError(
                f"Remote image exceeds maximum size of {MAX_PRODUCT_IMAGE_BYTES} bytes"
            )
        chunks.append(chunk)
    if total == 0:
        raise ExternalImageError("Remote image response was empty")
    return b"".join(chunks)


async def fetch_external_product_image(url: str) -> tuple[bytes, str, str]:
    """Validate URL, fetch image bytes, return (content, suffix, normalized_url)."""
    normalized = await assert_external_url_allowed(url)
    timeout = httpx.Timeout(
        connect=EXTERNAL_CONNECT_TIMEOUT, read=EXTERNAL_READ_TIMEOUT, write=10.0, pool=10.0
    )
    current = normalized

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for hop in range(MAX_EXTERNAL_REDIRECTS + 1):
            if hop > 0:
                current = await assert_external_url_allowed(current)

            response = await client.get(current)
            if response.status_code in {301, 302, 303, 307, 308}:
                if hop >= MAX_EXTERNAL_REDIRECTS:
                    raise ExternalImageError("Too many redirects")
                location = response.headers.get("location")
                if not location:
                    raise ExternalImageError("Redirect response missing Location header")
                current = str(httpx.URL(current).join(location))
                continue

            response.raise_for_status()
            _validate_image_content_type(response.headers.get("content-type"))
            content = await _read_limited_response(response)
            suffix = _suffix_from_content_type(response.headers.get("content-type"))
            if not suffix:
                suffix = _suffix_from_url_path(current)
            if not suffix:
                suffix = ".jpg"
            return content, suffix, normalized

    raise ExternalImageError("Failed to fetch remote image")


def delete_catalog_media_dir(catalog_id: uuid.UUID) -> None:
    path = data_root() / "images" / "catalogs" / str(catalog_id)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
