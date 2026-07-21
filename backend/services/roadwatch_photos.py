# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Photo validation, EXIF stripping, and upload helpers for RoadWatch."""

from __future__ import annotations

import contextlib
import io
import logging
from pathlib import Path

import aiofiles
import httpx
from fastapi import UploadFile

try:
    from PIL import Image, UnidentifiedImageError
    HAS_PIL = True
except ModuleNotFoundError:
    HAS_PIL = False

from services.exceptions import ServiceValidationError

logger = logging.getLogger(__name__)


# ── Content type → file extension mapping ─────────────────────────────────
UPLOAD_EXTENSION_BY_CONTENT_TYPE: dict[str, str] = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}

# Known image file signatures (magic bytes)
_IMAGE_MAGIC_SIGNATURES: list[bytes] = [
    b'\xff\xd8\xff',                     # JPEG
    b'\x89PNG\r\n\x1a\n',               # PNG
    b'RIFF',                             # WebP (RIFF....WEBP)
]


def is_valid_image_magic(header: bytes) -> bool:
    """Returns True if the first bytes match a known image format signature."""
    for sig in _IMAGE_MAGIC_SIGNATURES:
        if header.startswith(sig):
            if sig == b'RIFF' and header[8:12] != b'WEBP':
                continue
            return True
    return False


def strip_exif(payload: bytes, content_type: str | None = None) -> bytes:
    """Strip EXIF metadata by re-saving the image without EXIF kwarg."""
    if not HAS_PIL:
        logger.warning("PIL not available; skipping EXIF stripping")
        return payload
    try:
        with Image.open(io.BytesIO(payload)) as img:
            if img.mode in ("RGBA", "P") and content_type == "image/jpeg":
                img = img.convert("RGB")
            output = io.BytesIO()
            fmt = img.format or "JPEG"
            img.save(output, format=fmt)
            return output.getvalue()
    except (OSError, ValueError, UnidentifiedImageError) as e:
        logger.warning("Failed to strip EXIF data; proceeding with original payload. Error: %s", e)
        return payload


class UploadedPhotoUrl(str):
    """A photo URL with optional AI confidence and YOLOv8 detection metadata."""

    def __new__(cls, value: str, ai_confidence: float | None = None, yolov8_result: dict | None = None):
        obj = super().__new__(cls, value)
        obj.ai_confidence = ai_confidence
        obj.yolov8_result = yolov8_result
        return obj


async def read_upload_chunks(photo: UploadFile, max_bytes: int) -> tuple[list[bytes], int]:
    """Read UploadFile chunks, validate magic bytes, enforce size limit.

    Returns (chunks, total_written). Raises ServiceValidationError on invalid
    image or oversized upload.
    """
    written = 0
    chunks: list[bytes] = []
    first_chunk = True

    while True:
        chunk = await photo.read(1024 * 1024)
        if not chunk:
            break
        if first_chunk:
            first_chunk = False
            if not is_valid_image_magic(chunk[:12]):
                raise ServiceValidationError(
                    'Uploaded file does not appear to be a valid JPEG, PNG, or WebP image.'
                )
        written += len(chunk)
        if written > max_bytes:
            raise ServiceValidationError(
                f'Photo exceeds max upload size of {max_bytes // (1024 * 1024)} MB'
            )
        chunks.append(chunk)

    return chunks, written


async def save_photo_to_disk(target: Path, payload: bytes) -> None:
    """Write photo payload to local disk."""
    target.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target, 'wb') as handle:
        await handle.write(payload)


async def validate_photo_ai(
    payload: bytes,
    chatbot_url: str | None,
    internal_key: str | None,
) -> dict | None:
    """Call the chatbot service YOLO validation endpoint.

    Returns JSON response dict on success, None on failure or missing URL.
    """
    if not chatbot_url:
        return None

    url = f"{chatbot_url}/ai/validate-image"
    headers: dict[str, str] = {}
    if internal_key:
        headers["X-Internal-API-Key"] = internal_key

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            files = {"file": ("image.jpg", payload, "image/jpeg")}
            response = await client.post(url, files=files, headers=headers)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "AI image validation endpoint returned status code %d: %s",
                response.status_code, response.text,
            )
    except Exception as exc:
        logger.warning("Failed to call AI image validation service: %s", exc)
    return None


async def upload_photo_to_supabase(
    *,
    supabase_url: str | None,
    service_key: str | None,
    bucket: str,
    file_name: str,
    content_type: str,
    payload: bytes,
) -> str | None:
    """Upload photo to Supabase Storage bucket. Falls back silently on failure."""
    base_url = (supabase_url or '').rstrip('/')
    if not base_url or not service_key:
        return None

    object_path = f'roadwatch/{file_name}'
    upload_url = f'{base_url}/storage/v1/object/{bucket}/{object_path}'
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                upload_url,
                content=payload,
                headers={
                    'Authorization': f'Bearer {service_key}',
                    'apikey': service_key,
                    'Content-Type': content_type,
                    'x-upsert': 'false',
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning('Supabase Storage upload failed; falling back to local upload: %s', exc)
        return None

    return f'{base_url}/storage/v1/object/public/{bucket}/{object_path}'


def compose_photo_url(
    local_upload_base_url: str | None,
    file_name: str,
) -> str:
    """Build the public-facing URL for a locally stored photo."""
    if local_upload_base_url:
        return f'{local_upload_base_url}/{file_name}'
    return f'/uploads/{file_name}'


def cleanup_temp_file(path: str | Path) -> None:
    """Safely delete a temporary file, ignoring missing-file errors."""
    with contextlib.suppress(FileNotFoundError):
        Path(path).unlink(missing_ok=True)


class PhotoService:
    """Enterprise photo validation and upload service.

    Wraps the module-level photo helpers into a single injectable service
    for app.state wiring in main.py.
    """

    async def validate_and_save(
        self,
        photo: UploadFile,
        upload_dir: Path,
        max_bytes: int = 10 * 1024 * 1024,
        min_bytes: int = 256,
    ) -> str | None:
        """Read, validate, strip EXIF, and persist a photo upload.

        Returns the public URL path or *None* if validation fails.
        """
        chunks, total = await read_upload_chunks(photo, max_bytes)
        if total < min_bytes:
            return None
        payload = b"".join(chunks)
        header = payload[:32]
        if not is_valid_image_magic(header):
            return None
        safe = strip_exif(payload, photo.content_type)
        file_name = f"{uuid.uuid4().hex}{Path(photo.filename or 'upload.jpg').suffix}"
        dest = upload_dir / file_name
        await save_photo_to_disk(dest, safe)
        return compose_photo_url(file_name)

    async def validate_ai(self, photo: UploadFile) -> dict:
        """Run AI-powered validation on a photo upload."""
        import json
        header = await photo.read(64)
        await photo.seek(0)
        if not is_valid_image_magic(header):
            return {"valid": False, "reason": "invalid_image_magic"}
        return await validate_photo_ai(photo)

    async def upload_to_storage(self, photo: UploadFile, bucket: str = "roadwatch") -> str | None:
        """Upload photo to Supabase Storage, returning public URL or None."""
        return await upload_photo_to_supabase(photo, bucket)
