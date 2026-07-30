# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""extract_morth2022_tables.py
===========================
Extracts tabular accident data from the raw MoRTH 2022 PDF reports that were
downloaded into chatbot_service/data/accidents/morth_2022/.

The morth_2022 folder currently has two large PDFs but only one tabular CSV.
This script uses pdfplumber to extract all tables from those PDFs and saves
them as clean, labelled CSVs — matching the format of morth_2021/ and morth_2020/.

Run:
    pip install pdfplumber
    python scripts/extract_morth2022_tables.py

Output:
    chatbot_service/data/accidents/morth_2022/extracted_table_*.csv
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MORTH_2022_DIR = PROJECT_ROOT / "chatbot_service" / "data" / "accidents" / "morth_2022"


def _clean_cell(text: str | None) -> str:
    """Normalise whitespace in a table cell value."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def _is_empty_row(row: list[str]) -> bool:
    return all(c == "" for c in row)


def _is_header_row(row: list[str]) -> bool:
    """Heuristic: a row is a header if most cells look like labels not numbers."""
    non_empty = [c for c in row if c]
    if not non_empty:
        return False
    numeric_count = sum(1 for c in non_empty if re.match(r"^[\d,.\s]+$", c))
    return numeric_count < len(non_empty) / 2


def extract_tables_from_pdf(pdf_path: Path, output_dir: Path) -> int:
    """Extract all tables from a PDF and write them to numbered CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem[:24]  # keep filename manageable
    tables_written = 0

    print(f"\nProcessing: {pdf_path.name} ({pdf_path.stat().st_size / 1_048_576:.1f} MB)")

    with pdfplumber.open(pdf_path) as pdf:
        global_table_idx = 0
        buffer_rows: list[list[str]] = []
        buffer_header: list[str] = []

        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table:
                    continue

                cleaned = [
                    [_clean_cell(cell) for cell in row]
                    for row in table
                ]
                cleaned = [r for r in cleaned if not _is_empty_row(r)]

                if not cleaned:
                    continue

                # Detect if this page continues a previous table (no header in first row)
                first_row_looks_like_header = _is_header_row(cleaned[0])

                if first_row_looks_like_header and buffer_rows:
                    # Flush previous buffer
                    _write_table(output_dir, stem, global_table_idx, buffer_header, buffer_rows)
                    tables_written += 1
                    global_table_idx += 1
                    buffer_rows = []
                    buffer_header = []

                if first_row_looks_like_header:
                    buffer_header = cleaned[0]
                    buffer_rows = cleaned[1:]
                else:
                    # Continuation of previous table
                    buffer_rows.extend(cleaned)

        # Flush any remaining buffer
        if buffer_rows:
            _write_table(output_dir, stem, global_table_idx, buffer_header, buffer_rows)
            tables_written += 1

    return tables_written


def _write_table(
    output_dir: Path,
    stem: str,
    index: int,
    header: list[str],
    rows: list[list[str]],
) -> None:
    filename = output_dir / f"extracted_{stem}_table_{index:03d}.csv"
    with filename.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        if header:
            writer.writerow(header)
        writer.writerows(rows)
    print(f"  Wrote: {filename.name} ({len(rows)} data rows)")


def main() -> None:
    pdfs = sorted(MORTH_2022_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {MORTH_2022_DIR}")
        print("Download the MoRTH 2022 report from:")
        print("  https://morth.nic.in/road-accident-in-india")
        sys.exit(1)

    total_tables = 0
    for pdf_path in pdfs:
        n = extract_tables_from_pdf(pdf_path, MORTH_2022_DIR)
        total_tables += n
        print(f"  => {n} tables extracted from {pdf_path.name}")

    print(f"\nDone: {total_tables} total table CSVs written to {MORTH_2022_DIR}")
    print("These CSVs can now be used by seed_blackspots.py for accident data seeding.")


if __name__ == "__main__":
    main()
