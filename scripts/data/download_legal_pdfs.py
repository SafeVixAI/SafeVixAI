# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""download_legal_pdfs.py
======================
Downloads the three critical RAG knowledge-base PDFs from official government
and WHO sources. All URLs are verified working as of April 2026.

Run:
    python scripts/download_legal_pdfs.py

The three placeholder files will be replaced with real PDFs.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHATBOT_DATA = PROJECT_ROOT / "chatbot_service" / "data"

TARGETS: list[dict] = [
    {
        "name": "Motor Vehicles Act 1988",
        "destinations": [CHATBOT_DATA / "legal" / "motor_vehicles_act_1988.pdf"],
        "sources": [
            # indiacode.nic.in — official government portal
            "https://indiacode.nic.in/bitstream/123456789/15577/1/the_motor_vehicles_act_1988.pdf",
            # legislative.gov.in — Ministry of Law fallback
            "https://legislative.gov.in/sites/default/files/A1988-59.pdf",
        ],
    },
    {
        "name": "Motor Vehicles Amendment Act 2019",
        "destinations": [CHATBOT_DATA / "legal" / "mv_amendment_act_2019.pdf"],
        "sources": [
            # gazette of India official notification
            "https://egazette.nic.in/WriteReadData/2019/210355.pdf",
            # MoRTH official page
            "https://morth.nic.in/sites/default/files/MV_Amendment_Act_2019.pdf",
        ],
    },
    {
        "name": "WHO Emergency Care Systems Guidelines (Trauma)",
        "destinations": [CHATBOT_DATA / "medical" / "who_trauma_care_guidelines.pdf"],
        "sources": [
            # WHO publications — direct PDF download
            "https://iris.who.int/bitstream/handle/10665/350523/9789240052215-eng.pdf",
            # Alternative WHO trauma care document
            "https://www.who.int/publications/i/item/9789241548526",
        ],
    },
]

PLACEHOLDER_MARKERS = {
    b"# Placeholder",
    b"Placeholder",
}


def is_placeholder(path: Path) -> bool:
    """Return True if the file is one of the tiny text placeholder stubs."""
    if not path.exists():
        return True
    if path.stat().st_size < 256:
        try:
            preview = path.read_bytes()[:64]
            return any(marker in preview for marker in PLACEHOLDER_MARKERS)
        except OSError:
            return True
    return False


def download_first_working(sources: list[str], destination: Path) -> bool:
    """Try each source URL in order; return True on the first successful download."""
    for url in sources:
        print(f"  Trying: {url}")
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (SafeVixAI-DataPipeline/1.0; +https://github.com)"
                },
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
            if len(data) < 1024:
                print(f"    Response too small ({len(data)} bytes) — likely not a PDF, skipping")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            print(f"    Downloaded: {len(data):,} bytes -> {destination.name}")
            return True
        except urllib.error.HTTPError as exc:
            print(f"    HTTP {exc.code}: {exc.reason}")
        except urllib.error.URLError as exc:
            print(f"    Network error: {exc.reason}")
        except Exception as exc:
            print(f"    Unexpected error: {exc}")
    return False


def main() -> None:
    failed: list[str] = []

    for target in TARGETS:
        name: str = target["name"]
        destinations: list[Path] = target["destinations"]
        sources: list[str] = target["sources"]

        print(f"\n{'='*60}")
        print(f"  {name}")

        placeholder_paths = [p for p in destinations if is_placeholder(p)]
        if not placeholder_paths:
            real_paths = [p for p in destinations if p.exists()]
            sizes = ", ".join(f"{p.name} ({p.stat().st_size:,}B)" for p in real_paths)
            print(f"  Already present: {sizes} — skipping")
            continue

        print("  Placeholder detected — downloading real PDF...")
        success = download_first_working(sources, destinations[0])

        if success and len(destinations) > 1:
            # Mirror to additional destination paths
            base = destinations[0]
            for extra_dest in destinations[1:]:
                extra_dest.parent.mkdir(parents=True, exist_ok=True)
                extra_dest.write_bytes(base.read_bytes())
                print(f"  Mirrored to: {extra_dest}")

        if not success:
            failed.append(name)
            print(
                f"\n  !!! DOWNLOAD FAILED for: {name}\n"
                f"  Manual steps:\n"
                f"    1. Open a browser and go to one of these URLs:\n"
                + "\n".join(f"       {url}" for url in sources)
                + f"\n    2. Save the PDF to: {destinations[0]}"
            )

    print(f"\n{'='*60}")
    if failed:
        print(f"RESULT: {len(TARGETS) - len(failed)}/{len(TARGETS)} downloaded successfully")
        print(f"Manual download required for: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"RESULT: All {len(TARGETS)} PDFs downloaded successfully")
        print("RAG pipeline now has real legal and medical knowledge.")


if __name__ == "__main__":
    main()
