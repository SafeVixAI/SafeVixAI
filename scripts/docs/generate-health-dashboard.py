# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Generate docs-health.json with key metrics for enterprise dashboard.

Produces docs/wiki/meta/docs-health.json consumed by MkDocs extras.
Metrics: coverage %, staleness, mermaid count, link health, git context.
"""

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

WIKI_DIR = Path("docs/wiki")
META_DIR = WIKI_DIR / "meta"
TOTAL_TARGET = 375


def count_files(directory: Path, pattern: str = "*.md") -> int:
    return len(list(directory.rglob(pattern)))


def staleness_check(stale_days: int = 90):
    fresh = stale = undated = 0
    for f in WIKI_DIR.rglob("*.md"):
        content = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?:generated|Generated):\s*(\d{4}-\d{2}-\d{2})", content)
        if m:
            gen_date = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
            age = (datetime.now(UTC) - gen_date).days
            if age >= stale_days:
                stale += 1
            else:
                fresh += 1
        else:
            undated += 1
            fresh += 1  # No date = assume fresh (matches wiki_manager.py)
    return fresh, stale, undated


def ownership_coverage():
    """Count pages with owner: field in frontmatter."""
    total = owned = 0
    owners = {}
    for f in WIKI_DIR.rglob("*.md"):
        total += 1
        content = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^owner:\s*(.+)$", content, re.MULTILINE)
        if m:
            owned += 1
            o = m.group(1).strip()
            owners[o] = owners.get(o, 0) + 1
    return total, owned, owners


def count_mermaid() -> int:
    count = 0
    for f in WIKI_DIR.rglob("*.md"):
        content = f.read_text(encoding="utf-8", errors="replace")
        count += len(re.findall(r"```\s*mermaid", content))
    return count


def check_link_results() -> dict:
    try:
        lines = Path("scripts/docs/check-links.py.out").read_text().strip().splitlines()
        total = broken = 0
        broken_files = []
        for line in lines:
            if "-> BROKEN" in line or "broken" in line.lower():
                broken += 1
                broken_files.append(line.strip())
            total += 1
        return {"total_links": total, "broken_links": broken, "broken_files": broken_files}
    except (FileNotFoundError, OSError):
        return {"total_links": 0, "broken_links": 0, "broken_files": []}


def main():
    META_DIR.mkdir(parents=True, exist_ok=True)

    total = count_files(WIKI_DIR)
    fresh, stale, undated = staleness_check()
    mermaid_count = count_mermaid()
    links = check_link_results()
    owned_total, owned_count, owners = ownership_coverage()

    health = {
        "generated_at": datetime.now(UTC).isoformat(),
        "schema_version": 2,
        "wiki": {
            "total_files": total,
            "coverage_pct": round((total / TOTAL_TARGET) * 100, 1),
            "coverage_target": TOTAL_TARGET,
            "fresh": fresh,
            "stale": stale,
            "undated": undated,
            "freshness_pct": round((fresh / total) * 100, 1) if total else 0.0,
            "stale_pct": round((stale / total) * 100, 1) if total else 0.0,
            "stale_threshold_days": 90,
            "mermaid_blocks": mermaid_count,
            "ownership_pct": round((owned_count / owned_total) * 100, 1) if owned_total else 0.0,
            "owned_files": owned_count,
            "owners": owners,
        },
        "links": links,
        "git": {
            "branch": os.environ.get("GITHUB_REF_NAME", "local"),
            "sha": os.environ.get("GITHUB_SHA", "local"),
        },
    }

    output = META_DIR / "docs-health.json"
    output.write_text(json.dumps(health, indent=2))
    print(f"Health dashboard written to {output}")

    if stale > 0:
        msg = f"Docs health: {stale} stale file(s) found (>=90 days old)"
        if "GITHUB_ACTIONS" in os.environ:
            print(f"::warning::{msg}")
        else:
            print(f"WARNING: {msg}")

    return 1 if stale > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
