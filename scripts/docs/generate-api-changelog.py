# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Generate API changelog by diffing OpenAPI specs against the main branch.

Compares current backend/openapi.json and chatbot_service/openapi.json with
their versions on the main git branch. Produces docs/api/changelog.md.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = ROOT / "docs" / "api"
SPECS = [
    ("Backend API", ROOT / "backend" / "openapi.json"),
    ("Chatbot API", ROOT / "chatbot_service" / "openapi.json"),
]


def get_old_spec(path: Path, ref: str = "origin/main"):
    """Retrieve spec from git history at given ref."""
    try:
        rel = path.relative_to(ROOT).as_posix()
        result = subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        pass
    return None


def extract_endpoints(spec: dict) -> dict:
    """Extract {method: [path, ...]} from OpenAPI spec."""
    endpoints = {}
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method in ("get", "post", "put", "delete", "patch"):
            if method in methods:
                key = f"{method.upper()} {path}"
                endpoints[key] = {
                    "summary": methods[method].get("summary", ""),
                    "deprecated": methods[method].get("deprecated", False),
                }
    return endpoints


def diff_endpoints(old: dict, new: dict) -> dict:
    """Compare two endpoint dicts, return changes."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    return {
        "added": sorted(new_keys - old_keys),
        "removed": sorted(old_keys - new_keys),
        "deprecated": [k for k, v in new.items() if v["deprecated"]],
    }


def format_changelog(name: str, changes: dict, old_commit: str) -> str:
    """Format changelog section in markdown."""
    lines = [f"## {name}\n"]

    if not any(changes.values()):
        lines.append("_No changes detected._\n")
        return "\n".join(lines)

    lines.append(f"Compared against: `{old_commit}`\n")

    if changes["added"]:
        lines.append(f"### Added ({len(changes['added'])})\n")
        for ep in changes["added"]:
            lines.append(f"- `{ep}`")
        lines.append("")

    if changes["removed"]:
        lines.append(f"### Removed ({len(changes['removed'])})\n")
        for ep in changes["removed"]:
            lines.append(f"- `{ep}`")
        lines.append("")

    if changes["deprecated"]:
        lines.append(f"### Deprecated ({len(changes['deprecated'])})\n")
        for ep in changes["deprecated"]:
            lines.append(f"- `{ep}`")
        lines.append("")

    return "\n".join(lines)


def get_current_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=ROOT,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except subprocess.CalledProcessError:
        return "unknown"


def main():
    API_DIR.mkdir(parents=True, exist_ok=True)
    current_commit = get_current_commit()
    has_changes = False

    sections = [
        "---",
        "title: API Changelog",
        "description: Auto-generated diff of OpenAPI specification changes",
        f"generated: {datetime.now().strftime('%Y-%m-%d')}",
        f"commit: {current_commit}",
        "---",
        "",
        "# API Changelog",
        "",
        f"Auto-generated from OpenAPI spec diff at `{current_commit}`.",
        "Changes are detected by comparing the current spec against the `origin/main` branch.\n",
    ]

    for name, spec_path in SPECS:
        if not spec_path.exists():
            sections.append(f"## {name}\n\n_Spec file not found._\n")
            continue

        try:
            new_spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            sections.append(f"## {name}\n\n_Failed to parse current spec._\n")
            continue

        old_spec = get_old_spec(spec_path)
        if old_spec is None:
            sections.append(f"## {name}\n\n_No previous spec found (first build)._"
                            f" Current: {len(extract_endpoints(new_spec))} endpoints._\n")
            continue

        old_commit = "origin/main"
        changes = diff_endpoints(extract_endpoints(old_spec), extract_endpoints(new_spec))
        sections.append(format_changelog(name, changes, old_commit))
        if any(changes.values()):
            has_changes = True

    output = API_DIR / "changelog.md"
    output.write_text("\n".join(sections), encoding="utf-8")
    print(f"API changelog written to {output}")

    if has_changes:
        print("API changes detected — changelog updated.")
    else:
        print("No API changes detected.")

    return 0 if "CI" in os.environ else 0


if __name__ == "__main__":
    sys.exit(main())
