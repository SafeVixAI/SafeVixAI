# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from rag.document_loader import (
    MAX_CSV_ROWS,
    MAX_TEXT_CHARS,
    LoadedDocument,
    _read_csv,
    _read_json,
    _read_pdf,
    _read_text,
    load_documents,
)


class TestReadText:
    def test_reads_text_file(self) -> None:
        path = Path(tempfile.mktemp(suffix=".txt"))
        path.write_text("Hello World", encoding="utf-8")
        result = _read_text(path)
        assert "Hello World" in result
        path.unlink()

    def test_reads_markdown_file(self) -> None:
        path = Path(tempfile.mktemp(suffix=".md"))
        path.write_text("# Title\n\nBody text", encoding="utf-8")
        result = _read_text(path)
        assert "# Title" in result
        path.unlink()


class TestReadJson:
    def test_reads_json_file(self) -> None:
        data = {"key": "value", "nested": {"a": 1}}
        path = Path(tempfile.mktemp(suffix=".json"))
        path.write_text(json.dumps(data), encoding="utf-8")
        result = _read_json(path)
        assert "key" in result
        assert "value" in result
        path.unlink()

    def test_invalid_json_raises(self) -> None:
        path = Path(tempfile.mktemp(suffix=".json"))
        path.write_text("not-json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            _read_json(path)
        path.unlink()


class TestReadCsv:
    def test_reads_csv_file(self) -> None:
        path = Path(tempfile.mktemp(suffix=".csv"))
        path.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8-sig")
        result = _read_csv(path)
        assert "Columns:" in result
        assert "Alice" in result
        path.unlink()

    def test_respects_max_csv_rows(self) -> None:
        path = Path(tempfile.mktemp(suffix=".csv"))
        lines = ["col"] + [f"row{i}" for i in range(MAX_CSV_ROWS + 10)]
        path.write_text("\n".join(lines), encoding="utf-8-sig")
        result = _read_csv(path)
        row_count = result.count("\n")
        assert row_count <= MAX_CSV_ROWS + 2
        path.unlink()

    def test_empty_csv(self) -> None:
        path = Path(tempfile.mktemp(suffix=".csv"))
        path.write_text("", encoding="utf-8-sig")
        result = _read_csv(path)
        assert result == ""
        path.unlink()


class TestReadPdf:
    def test_returns_empty_when_no_pypdf(self) -> None:
        path = Path(tempfile.mktemp(suffix=".pdf"))
        path.write_text("fake pdf content", encoding="utf-8")
        result = _read_pdf(path)
        assert result == ""
        path.unlink()


class TestLoadDocuments:
    def test_returns_empty_for_nonexistent_dir(self) -> None:
        docs = load_documents(Path("/nonexistent/path"))
        assert docs == []

    def test_loads_txt_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            content_file = base / "test.txt"
            content_file.write_text("Hello World", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 1
            assert isinstance(docs[0], LoadedDocument)
            assert "Hello World" in docs[0].text

    def test_loads_md_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            md_file = base / "readme.md"
            md_file.write_text("# Readme", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 1
            assert docs[0].category == "general"

    def test_loads_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            json_file = base / "data.json"
            json_file.write_text('{"key": "val"}', encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 1

    def test_loads_csv_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_file = base / "data.csv"
            csv_file.write_text("x,y\n1,2\n3,4\n", encoding="utf-8-sig")
            docs = load_documents(base)
            assert len(docs) == 1

    def test_skips_chromadb_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            chroma = base / "chroma_db"
            chroma.mkdir()
            (chroma / "file.txt").write_text("content", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 0

    def test_skips_unsupported_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "file.xyz").write_text("content", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 0

    def test_truncates_long_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            long_file = base / "long.txt"
            long_file.write_text("A" * (MAX_TEXT_CHARS + 1000), encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 1
            assert len(docs[0].text) <= MAX_TEXT_CHARS

    def test_uses_subdir_as_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            sub = base / "legal"
            sub.mkdir()
            (sub / "section.txt").write_text("Section content", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 1
            assert docs[0].category == "legal"

    def test_handles_load_errors_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            bad_file = base / "corrupt.json"
            bad_file.write_text("{invalid", encoding="utf-8")
            docs = load_documents(base)
            assert len(docs) == 0
