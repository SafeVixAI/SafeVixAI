# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
CHATBOT_SERVICE_DIR = PROJECT_ROOT / 'chatbot_service'

if str(CHATBOT_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_SERVICE_DIR))


from rag.document_loader import LoadedDocument, load_documents  # noqa: E402
from rag.embeddings import normalize_text  # noqa: E402

DEFAULT_PERSIST_DIR = BACKEND_DIR / 'data' / 'chroma_db'


@dataclass(slots=True)
class IndexedChunk:
    chunk_id: str
    source: str
    title: str
    category: str
    content: str


def _default_source_dirs() -> list[Path]:
    return [
        BACKEND_DIR / 'datasets' / 'legal',
        CHATBOT_SERVICE_DIR / 'data' / 'legal',
        CHATBOT_SERVICE_DIR / 'data' / 'medical',
    ]


def _origin_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace('\\', '/')
    except ValueError:
        return str(path.resolve()).replace('\\', '/')


def _merged_category(origin: Path, document: LoadedDocument) -> str:
    base_category = origin.name.lower() or 'general'
    if document.category and document.category != 'general':
        return f'{base_category}/{document.category}'
    return base_category


def _chunk_document(document: LoadedDocument, *, origin_label: str, category: str) -> list[IndexedChunk]:
    paragraphs = [normalize_text(item) for item in document.text.split('\n') if normalize_text(item)]
    if not paragraphs:
        paragraphs = [document.text]

    chunks: list[IndexedChunk] = []
    current: list[str] = []
    current_length = 0
    chunk_index = 1
    source = f'{origin_label}/{document.source}'
    for paragraph in paragraphs:
        if current and current_length + len(paragraph) > 900:
            chunks.append(
                IndexedChunk(
                    chunk_id=f'{source}:{chunk_index}',
                    source=source,
                    title=document.title,
                    category=category,
                    content='\n'.join(current),
                )
            )
            chunk_index += 1
            current = []
            current_length = 0
        current.append(paragraph)
        current_length += len(paragraph)

    if current:
        chunks.append(
            IndexedChunk(
                chunk_id=f'{source}:{chunk_index}',
                source=source,
                title=document.title,
                category=category,
                content='\n'.join(current),
            )
        )
    return chunks


def _collect_chunks(source_dirs: list[Path]) -> tuple[list[IndexedChunk], dict[str, int]]:
    chunks: list[IndexedChunk] = []
    source_counts: dict[str, int] = {}
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        origin_label = _origin_label(source_dir)
        documents = load_documents(source_dir)
        source_counts[origin_label] = len(documents)
        for document in documents:
            category = _merged_category(source_dir, document)
            chunks.extend(_chunk_document(document, origin_label=origin_label, category=category))
    return chunks, source_counts


def _write_index(persist_dir: Path, chunks: list[IndexedChunk], source_counts: dict[str, int]) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    index_path = persist_dir / 'simple_index.json'
    manifest_path = persist_dir / 'manifest.json'
    index_path.write_text(
        json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    manifest_path.write_text(
        json.dumps(
            {
                'chunk_count': len(chunks),
                'category_count': len({chunk.category for chunk in chunks}),
                'sources': source_counts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Build a lightweight local document index for backend legal and medical datasets.',
    )
    parser.add_argument(
        '--source-dir',
        action='append',
        type=Path,
        help='Optional source directory. Repeat to include multiple directories. Defaults to backend legal plus chatbot legal/medical data.',
    )
    parser.add_argument(
        '--persist-dir',
        type=Path,
        default=DEFAULT_PERSIST_DIR,
        help=f'Directory for the generated JSON index. Defaults to {DEFAULT_PERSIST_DIR}',
    )
    parser.add_argument(
        '--mirror-chatbot-index',
        action='store_true',
        help='Also copy the generated index into chatbot_service/data/chroma_db.',
    )
    args = parser.parse_args()

    source_dirs = args.source_dir or _default_source_dirs()
    chunks, source_counts = _collect_chunks(source_dirs)
    if not chunks:
        raise SystemExit(
            'No supported documents were found. Add PDFs, CSVs, JSON, TXT, or MD files to one of: '
            + ', '.join(str(path) for path in source_dirs)
        )

    _write_index(args.persist_dir, chunks, source_counts)
    print(
        f'Indexed {len(chunks)} chunks from {sum(source_counts.values())} documents '
        f'into {args.persist_dir / "simple_index.json"}'
    )

    if args.mirror_chatbot_index:
        mirror_dir = CHATBOT_SERVICE_DIR / 'data' / 'chroma_db'
        _write_index(mirror_dir, chunks, source_counts)
        print(f'Mirrored the index to {mirror_dir / "simple_index.json"}')


if __name__ == '__main__':
    main()
