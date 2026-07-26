# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.document_loader import (
    EXCLUDED_DATA_DIRS,
    MAX_CSV_ROWS,
    MAX_TEXT_CHARS,
    LoadedDocument,
    _read_csv,
    _read_json,
    _read_pdf,
    _read_text,
    load_documents,
)
from rag.vectorstore import (
    EXCLUDED_INDEX_CATEGORIES,
    DocumentChunk,
    LocalVectorStore,
)


def _make_mock_path(
    suffix: str = '.txt',
    parts: tuple[str, ...] = ('data', 'file.txt'),
    stem: str = 'file',
    is_file: bool = True,
    text_content: str = 'Default content',
    relative: str | None = None,
):
    path = MagicMock(spec=Path)
    path.suffix = suffix
    path.is_file.return_value = is_file
    path.parts = parts
    path.stem = stem
    path.name = parts[-1] if parts else 'file.txt'
    path.read_text.return_value = text_content
    if relative is None:
        relative = str(Path(*parts[1:])) if len(parts) > 1 else parts[0]
    path.relative_to.return_value = Path(relative)
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# DocumentChunk
# ═══════════════════════════════════════════════════════════════════════════════

class TestDocumentChunk:
    def test_creates_with_all_fields(self):
        chunk = DocumentChunk(
            chunk_id='doc.txt:1',
            source='doc.txt',
            title='My Document',
            category='legal',
            content='Some text here',
        )
        assert chunk.chunk_id == 'doc.txt:1'
        assert chunk.source == 'doc.txt'
        assert chunk.title == 'My Document'
        assert chunk.category == 'legal'
        assert chunk.content == 'Some text here'

# ═══════════════════════════════════════════════════════════════════════════════
# LoadedDocument
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoadedDocument:
    def test_creates_with_all_fields(self):
        doc = LoadedDocument(
            source='path/to/doc.txt',
            title='My Document',
            category='legal',
            text='Full document text',
        )
        assert doc.source == 'path/to/doc.txt'
        assert doc.title == 'My Document'
        assert doc.category == 'legal'
        assert doc.text == 'Full document text'

# ═══════════════════════════════════════════════════════════════════════════════
# _read_text
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadText:
    def test_reads_text_file(self):
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = 'Hello world'
        result = _read_text(mock_path)
        assert result == 'Hello world'
        mock_path.read_text.assert_called_once_with(encoding='utf-8', errors='ignore')


# ═══════════════════════════════════════════════════════════════════════════════
# _read_csv
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadCsv:
    def test_parses_csv_with_headers_and_rows(self):
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        mock_path.open.return_value = mock_cm

        with patch('rag.document_loader.csv.DictReader') as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['col1', 'col2']
            mock_reader.__iter__.return_value = iter([
                {'col1': 'a', 'col2': 'b'},
                {'col1': 'c', 'col2': 'd'},
            ])
            mock_reader_cls.return_value = mock_reader
            result = _read_csv(mock_path)

        assert 'Columns: col1, col2' in result
        assert 'Row 1: col1=a; col2=b' in result
        assert 'Row 2: col1=c; col2=d' in result

    def test_empty_csv_returns_just_columns_line(self):
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        mock_path.open.return_value = mock_cm

        with patch('rag.document_loader.csv.DictReader') as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['col1']
            mock_reader.__iter__.return_value = iter([])
            mock_reader_cls.return_value = mock_reader
            result = _read_csv(mock_path)

        assert result == 'Columns: col1'
        assert 'Row' not in result

    def test_skips_empty_values_in_row(self):
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        mock_path.open.return_value = mock_cm

        with patch('rag.document_loader.csv.DictReader') as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['col1', 'col2']
            mock_reader.__iter__.return_value = iter([
                {'col1': 'a', 'col2': ''},
            ])
            mock_reader_cls.return_value = mock_reader
            result = _read_csv(mock_path)

        assert 'col2=' not in result
        assert 'col1=a' in result

    def test_respects_max_csv_rows(self):
        mock_path = MagicMock(spec=Path)
        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        mock_path.open.return_value = mock_cm

        many_rows = [{f'col{k}': f'val{k}'} for k in range(MAX_CSV_ROWS + 50)]

        with patch('rag.document_loader.csv.DictReader') as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['col0']
            mock_reader.__iter__.return_value = iter(many_rows)
            mock_reader_cls.return_value = mock_reader
            result = _read_csv(mock_path)

        row_count = result.count('Row ')
        assert row_count == MAX_CSV_ROWS


# ═══════════════════════════════════════════════════════════════════════════════
# _read_json
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadJson:
    def test_parses_json_content(self):
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = '{"key": "value", "num": 42}'
        result = _read_json(mock_path)
        parsed = json.loads(result)
        assert parsed['key'] == 'value'
        assert parsed['num'] == 42

    def test_pretty_printed(self):
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = '{"a":1,"b":2}'
        result = _read_json(mock_path)
        assert '  ' in result
        assert '\n' in result


# ═══════════════════════════════════════════════════════════════════════════════
# _read_pdf
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadPdf:
    def test_pdfreader_unavailable_returns_empty_string(self):
        mock_path = MagicMock(spec=Path)
        with patch('rag.document_loader.PdfReader', None):
            result = _read_pdf(mock_path)
        assert result == ''

    def test_pdfreader_available_extracts_text(self):
        mock_path = MagicMock(spec=Path)
        mock_pdf_reader_cls = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = 'Page content here'
        mock_pdf_reader = MagicMock()
        mock_pdf_reader.pages = [mock_page]
        mock_pdf_reader_cls.return_value = mock_pdf_reader

        with patch('rag.document_loader.PdfReader', mock_pdf_reader_cls):
            result = _read_pdf(mock_path)
        assert 'Page 1: Page content here' in result


# ═══════════════════════════════════════════════════════════════════════════════
# load_documents
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoadDocuments:
    def test_empty_data_dir_returns_empty_list(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = False
        assert load_documents(data_dir) == []

    def test_non_existent_dir_returns_empty_list(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = False
        assert load_documents(data_dir) == []

    def test_loads_txt_files(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        txt_path = _make_mock_path('.txt', ('data', 'doc.txt'), 'doc', text_content='Hello world',
                                   relative='doc.txt')
        data_dir.rglob.return_value = [txt_path]

        with patch('rag.document_loader.normalize_text', side_effect=lambda x: x):
            docs = load_documents(data_dir)

        assert len(docs) == 1
        assert docs[0].source == 'doc.txt'
        assert docs[0].text == 'Hello world'
        assert docs[0].category == 'general'

    def test_loads_md_files(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        md_path = _make_mock_path('.md', ('data', 'readme.md'), 'readme', text_content='# Markdown',
                                  relative='readme.md')
        data_dir.rglob.return_value = [md_path]

        with patch('rag.document_loader.normalize_text', side_effect=lambda x: x):
            docs = load_documents(data_dir)

        assert len(docs) == 1
        assert docs[0].source == 'readme.md'

    def test_loads_json_files(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        json_path = _make_mock_path('.json', ('data', 'data.json'), 'data',
                                    text_content='{"key":"val"}', relative='data.json')
        data_dir.rglob.return_value = [json_path]

        with patch('rag.document_loader.normalize_text', side_effect=lambda x: x):
            docs = load_documents(data_dir)

        assert len(docs) == 1
        assert docs[0].source == 'data.json'

    def test_loads_csv_files(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        csv_path = _make_mock_path('.csv', ('data', 'data.csv'), 'data', text_content='',
                                   relative='data.csv')
        data_dir.rglob.return_value = [csv_path]

        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        csv_path.open.return_value = mock_cm

        with (
            patch('rag.document_loader.normalize_text', side_effect=lambda x: x),
            patch('rag.document_loader.csv.DictReader') as mock_reader_cls,
        ):
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['a']
            mock_reader.__iter__.return_value = iter([{'a': '1'}])
            mock_reader_cls.return_value = mock_reader
            docs = load_documents(data_dir)

        assert len(docs) == 1
        assert docs[0].source == 'data.csv'

    def test_csv_max_rows_limit(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        csv_path = _make_mock_path('.csv', ('data', 'big.csv'), 'big', text_content='',
                                   relative='big.csv')
        data_dir.rglob.return_value = [csv_path]

        mock_file = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_file
        csv_path.open.return_value = mock_cm

        many_rows = [{f'col{k}': f'val{k}'} for k in range(MAX_CSV_ROWS + 50)]

        with (
            patch('rag.document_loader.normalize_text', side_effect=lambda x: x),
            patch('rag.document_loader.csv.DictReader') as mock_reader_cls,
        ):
            mock_reader = MagicMock()
            mock_reader.fieldnames = ['col0']
            mock_reader.__iter__.return_value = iter(many_rows)
            mock_reader_cls.return_value = mock_reader
            docs = load_documents(data_dir)

        assert len(docs) == 1
        # Should contain MAX_CSV_ROWS rows, not more
        row_count = docs[0].text.count('Row ')
        assert row_count == MAX_CSV_ROWS

    def test_skips_excluded_dirs(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True

        for excluded in EXCLUDED_DATA_DIRS:
            excluded_path = _make_mock_path('.txt', (excluded, 'file.txt'), 'file',
                                            text_content='Should be excluded',
                                            relative=f'{excluded}/file.txt')
            data_dir.rglob.return_value = [excluded_path]

            with patch('rag.document_loader.normalize_text', side_effect=lambda x: x):
                docs = load_documents(data_dir)
            assert len(docs) == 0, f'Expected 0 docs for excluded dir {excluded}'

    def test_oserror_skipped_and_logged(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        bad_path = _make_mock_path('.txt', ('data', 'bad.txt'), 'bad', text_content='',
                                   relative='bad.txt')
        data_dir.rglob.return_value = [bad_path]

        err_loader = MagicMock(side_effect=OSError('Permission denied'))
        with (
            patch('rag.document_loader.normalize_text', side_effect=lambda x: x),
            patch.dict('rag.document_loader._LOADER_BY_SUFFIX', {'.txt': err_loader}),
        ):
            docs = load_documents(data_dir)
        assert len(docs) == 0

    def test_empty_text_skipped(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        empty_path = _make_mock_path('.txt', ('data', 'empty.txt'), 'empty', text_content='   ',
                                     relative='empty.txt')
        data_dir.rglob.return_value = [empty_path]

        docs = load_documents(data_dir)
        assert len(docs) == 0

    def test_category_from_relative_path(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        nested = _make_mock_path('.txt', ('legal', 'mva.txt'), 'mva', text_content='Rules',
                                 relative='legal/mva.txt')
        data_dir.rglob.return_value = [nested]

        with patch('rag.document_loader.normalize_text', side_effect=lambda x: x):
            docs = load_documents(data_dir)

        assert len(docs) == 1
        assert docs[0].category == 'legal'
        assert docs[0].source == 'legal/mva.txt'

    def test_max_text_chars_truncation(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        long_text = 'A' * (MAX_TEXT_CHARS + 5000)
        long_path = _make_mock_path('.txt', ('data', 'long.txt'), 'long', text_content=long_text,
                                    relative='long.txt')
        data_dir.rglob.return_value = [long_path]

        docs = load_documents(data_dir)
        assert len(docs) == 1
        assert len(docs[0].text) == MAX_TEXT_CHARS

    def test_unknown_suffix_ignored(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        unknown = _make_mock_path('.xyz', ('data', 'file.xyz'), 'file', text_content='xyz',
                                  relative='file.xyz')
        data_dir.rglob.return_value = [unknown]
        docs = load_documents(data_dir)
        assert len(docs) == 0

    def test_non_file_paths_skipped(self):
        data_dir = MagicMock(spec=Path)
        data_dir.exists.return_value = True
        dir_path = _make_mock_path('', ('data', 'subdir'), 'subdir', is_file=False)
        data_dir.rglob.return_value = [dir_path]
        docs = load_documents(data_dir)
        assert len(docs) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# LocalVectorStore
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalVectorStoreConstructor:
    def test_stores_database_url_data_dir_and_embedding_model(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        assert store.database_url == 'postgresql://user:pass@localhost:5432/db'
        assert store.data_dir == Path('/fake/data')
        assert store.embedding_model == 'hash'


class TestLocalVectorStoreInitDb:
    @pytest.mark.asyncio
    async def test_init_db_creates_table_and_index(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        store._pool = mock_pool

        await store.init_db()

        assert mock_conn.execute.call_count >= 2
        calls = [c.args[0] for c in mock_conn.execute.call_args_list]
        assert any("CREATE TABLE IF NOT EXISTS safevixai_rag" in c for c in calls)
        assert any("CREATE INDEX IF NOT EXISTS safevixai_rag_embedding_idx" in c for c in calls)


class TestLocalVectorStoreEnsureIndex:
    @pytest.mark.asyncio
    async def test_already_loaded_returns_cached_chunks(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        cached = [DocumentChunk('a', 's', 't', 'c', 'x')]
        store._chunks = cached
        result = await store.ensure_index()
        assert result is cached

    @pytest.mark.asyncio
    async def test_not_loaded_fetches_from_db(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = 1

        mock_row = {
            "chunk_id": "a:1", "source": "a", "title": "t", "category": "c", "content": "x"
        }
        mock_conn.fetch.return_value = [mock_row]
        store._pool = mock_pool

        result = await store.ensure_index()
        assert len(result) == 1
        assert result[0].chunk_id == "a:1"
        assert store._chunks == result


class TestLocalVectorStoreBuildIndex:
    @pytest.mark.asyncio
    async def test_build_index_processes_documents_and_upserts(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_docs = [LoadedDocument('a', 't', 'c', 'x')]
        mock_chunks = [DocumentChunk('a:1', 'a', 't', 'c', 'x')]

        store.init_db = AsyncMock()
        store._upsert_pg = AsyncMock()

        with patch('rag.vectorstore.load_documents', return_value=mock_docs):
            with patch.object(LocalVectorStore, '_chunk_document', return_value=mock_chunks):
                result = await store.build_index(force=True)

        store.init_db.assert_called_once()
        store._upsert_pg.assert_called_once_with(mock_chunks)
        assert result == mock_chunks
        assert store._chunks == mock_chunks


class TestLocalVectorStoreSearch:
    @pytest.mark.asyncio
    async def test_search_returns_document_chunks_and_scores(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mock_row = {
            "chunk_id": "a:1", "source": "a", "title": "t", "category": "c", "content": "x", "score": 0.1
        }
        mock_conn.fetch.return_value = [mock_row]
        store._pool = mock_pool

        results = await store.search("query text", top_k=5)

        assert len(results) == 1
        chunk, score = results[0]
        assert chunk.chunk_id == "a:1"
        assert score == 0.1


class TestLocalVectorStoreStats:
    @pytest.mark.asyncio
    async def test_stats_returns_metrics(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mock_conn.fetchval.side_effect = [100, 5]
        store._pool = mock_pool
        store._chunks = [1]*100

        stats = await store.stats()

        assert stats["chunks"] == 100
        assert stats["categories"] == 5
        assert stats["database"] == "pgvector"
        assert stats["embedding_model"] == "hash"


class TestLocalVectorStoreChunkDocument:
    def test_chunks_at_900_char_boundary(self):
        paras = ['A' * 500, 'B' * 500]
        doc = LoadedDocument('test.txt', 'Test', 'legal', '\n'.join(paras))
        chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) == 2

    def test_single_paragraph_single_chunk(self):
        doc = LoadedDocument('test.txt', 'Test', 'legal', 'Short text')
        chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) == 1
        assert chunks[0].content == 'Short text'
        assert chunks[0].chunk_id == 'test.txt:1'

    def test_empty_paragraphs_falls_back_to_full_text(self):
        doc = LoadedDocument('test.txt', 'Test', 'legal', '')
        with patch('rag.vectorstore.normalize_text', side_effect=lambda x: ''):
            chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) == 1
        assert chunks[0].content == ''

    def test_multiple_paragraphs_within_900(self):
        doc = LoadedDocument('test.txt', 'Test', 'legal', 'Para1\n\nPara2\n\nPara3')
        with patch('rag.vectorstore.normalize_text', side_effect=lambda x: x.strip()):
            chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) == 1
        assert 'Para1' in chunks[0].content

    def test_chunk_ids_sequential(self):
        paras = ['X' * 600, 'Y' * 600, 'Z' * 600]
        doc = LoadedDocument('multi.txt', 'Multi', 'general', '\n'.join(paras))
        with patch('rag.vectorstore.normalize_text', side_effect=lambda x: x.strip()):
            chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) >= 2
        for i, chunk in enumerate(chunks, start=1):
            assert chunk.chunk_id == f'multi.txt:{i}'

