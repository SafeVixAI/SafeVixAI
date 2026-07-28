# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

from rag.embeddings import normalize_text  # noqa: E402

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency at runtime
    PdfReader = None


MAX_TEXT_CHARS = 120_000
MAX_CSV_ROWS = 250
EXCLUDED_DATA_DIRS = {
    'chroma_db',
    'qa_pairs',
    'pothole_training',
    'speech_finetuning',
}


@dataclass(slots=True)
class LoadedDocument:
    source: str
    title: str
    category: str
    text: str


def load_documents(data_dir: Path) -> list[LoadedDocument]:
    documents: list[LoadedDocument] = []
    if not data_dir.exists():
        return documents
    for path in sorted(data_dir.rglob('*')):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DATA_DIRS for part in path.parts):
            continue
        loader = _LOADER_BY_SUFFIX.get(path.suffix.lower())
        if loader is None:
            continue
        try:
            text = loader(path)
        except (OSError, FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load document %s: %s", path, exc)
            continue
        text = normalize_text(text)[:MAX_TEXT_CHARS]
        if not text:
            continue
        relative = path.relative_to(data_dir)
        category = relative.parts[0] if len(relative.parts) > 1 else 'general'
        documents.append(
            LoadedDocument(
                source=str(relative).replace('\\', '/'),
                title=path.stem.replace('_', ' ').strip(),
                category=category,
                text=text,
            )
        )
    return documents


def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def _read_json(path: Path) -> str:
    payload = json.loads(path.read_text(encoding='utf-8'))
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _read_csv(path: Path) -> str:
    lines: list[str] = []
    with path.open('r', encoding='utf-8-sig', errors='ignore', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            lines.append(f'Columns: {", ".join(reader.fieldnames)}')
        for index, row in enumerate(reader, start=1):
            if index > MAX_CSV_ROWS:
                break
            parts = [f'{key}={value}' for key, value in row.items() if value not in (None, '')]
            if parts:  # pragma: no branch
                lines.append(f'Row {index}: ' + '; '.join(parts))
    return '\n'.join(lines)


def _read_pdf(path: Path) -> str:
    if PdfReader is None:
        return ''
    try:
        reader = PdfReader(str(path))
    except Exception:
        logger.warning("Failed to read PDF: %s", path)
        return ''
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text = normalize_text(page.extract_text() or '')
        except Exception:
            page_text = ''
        if page_text:
            pages.append(f'Page {index}: {page_text}')
    return '\n'.join(pages)


_LOADER_BY_SUFFIX = {
    '.txt': _read_text,
    '.md': _read_text,
    '.json': _read_json,
    '.csv': _read_csv,
    '.pdf': _read_pdf,
}
