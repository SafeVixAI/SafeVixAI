import os
import re
import sys

HEADER_PY = "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 SafeVixAI Team\n"
HEADER_TS = "// SPDX-License-Identifier: MIT\n// Copyright (c) 2026 SafeVixAI Team\n"
HEADER_HTML = "<!-- SPDX-License-Identifier: MIT -->\n<!-- Copyright (c) 2026 SafeVixAI Team -->\n"
HEADER_YAML = "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 SafeVixAI Team\n"
HEADER_SH = "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 SafeVixAI Team\n"
HEADER_TF = "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 SafeVixAI Team\n"
HEADER_CSS = "/* SPDX-License-Identifier: MIT */\n/* Copyright (c) 2026 SafeVixAI Team */\n"
HEADER_TOML = "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 SafeVixAI Team\n"
HEADER_MD = "<!-- SPDX-License-Identifier: MIT -->\n<!-- Copyright (c) 2026 SafeVixAI Team -->\n"

EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".venv", ".git", ".next",
    ".pytest_cache", "dist", "build", "coverage", ".terraform",
    "playwright-report", "test-results", ".turbo",
}

EXCLUDE_FILES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    ".DS_Store", "*.min.js", "*.min.css",
}

SPDX_PATTERN = re.compile(r"SPDX-License-Identifier:")

HEADER_MAP = {
    ".py": HEADER_PY,
    ".ts": HEADER_TS,
    ".tsx": HEADER_TS,
    ".js": HEADER_TS,
    ".jsx": HEADER_TS,
    ".html": HEADER_HTML,
    ".htm": HEADER_HTML,
    ".yaml": HEADER_YAML,
    ".yml": HEADER_YAML,
    ".sh": HEADER_SH,
    ".tf": HEADER_TF,
    ".css": HEADER_CSS,
    ".scss": HEADER_CSS,
    ".toml": HEADER_TOML,
    ".md": HEADER_MD,
}


def should_exclude(path: str) -> bool:
    parts = path.replace(os.sep, "/").split("/")
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    for pat in EXCLUDE_FILES:
        if pat.startswith("*") and path.endswith(pat[1:]):
            return True
    return False


def has_spdx(content: str) -> bool:
    return bool(SPDX_PATTERN.search(content))


def get_header(filepath: str) -> str | None:
    ext = os.path.splitext(filepath)[1].lower()
    return HEADER_MAP.get(ext)


def add_header(filepath: str, header: str) -> bool:
    with open(filepath, encoding="utf-8", errors="replace") as f:
        content = f.read()

    if has_spdx(content):
        return False

    # Strip leading blank lines
    content = content.lstrip("\n\r")

    new_content = header + "\n" + content
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    services = ["backend", "chatbot_service", "frontend"]
    count = 0
    skipped = 0
    errors = 0

    for service in services:
        service_dir = os.path.join(root, service)
        if not os.path.isdir(service_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(service_dir):
            # Prune excluded dirs
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for filename in filenames:
                fpath = os.path.join(dirpath, filename)
                if should_exclude(fpath):
                    continue
                header = get_header(fpath)
                if header is None:
                    continue
                try:
                    if add_header(fpath, header):
                        print(f"  + {fpath}")
                        count += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"  ! {fpath}: {e}", file=sys.stderr)
                    errors += 1

    print(f"\nDone: {count} files annotated, {skipped} already had SPDX, {errors} errors")


if __name__ == "__main__":
    main()
