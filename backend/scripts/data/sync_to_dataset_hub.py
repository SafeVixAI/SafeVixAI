# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Copy civic intelligence data to SafeVixAI-Dataset-Hub for HuggingFace upload.

Usage:
    python scripts/data/sync_to_dataset_hub.py
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CIVIC_DATA = PROJECT_ROOT / 'data' / 'civic_intel'
FRONTEND_OFFLINE = PROJECT_ROOT.parent / 'frontend' / 'public' / 'offline-data'

HUB_ROOT = PROJECT_ROOT.parent.parent / 'SafeVixAI-Dataset-Hub'
HUB_CIVIC = HUB_ROOT / 'data' / 'backend' / 'data' / 'civic_intel'
HUB_SCRIPTS = HUB_ROOT / 'scripts' / 'backend' / 'data'


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.1f} MB'


def copy_tree(src: Path, dst: Path, label: str) -> tuple[int, int]:
    """Copy directory tree, return (files_copied, bytes_copied)."""
    dst.mkdir(parents=True, exist_ok=True)
    files = 0
    total_bytes = 0

    for item in sorted(src.rglob('*')):
        if item.is_dir():
            continue
        if item.name.startswith('.') or '__pycache__' in str(item):
            continue

        rel = item.relative_to(src)
        dest = dst / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        files += 1
        total_bytes += item.stat().st_size

    print(f'  {label}: {files} files, {_human_size(total_bytes)}')
    return files, total_bytes


def main():
    print('\n' + '=' * 60)
    print('  SafeVixAI -> Dataset Hub Sync')
    print('=' * 60)

    if not HUB_ROOT.exists():
        print(f'  ERROR: Hub not found at {HUB_ROOT}')
        return

    if not CIVIC_DATA.exists():
        print(f'  ERROR: Civic data not found at {CIVIC_DATA}')
        return

    total_files = 0
    total_bytes = 0

    # 1. Copy civic_intel data
    print('\n  [1] Copying civic_intel data...')
    f, b = copy_tree(CIVIC_DATA, HUB_CIVIC, 'civic_intel')
    total_files += f
    total_bytes += b

    # 2. Copy civic data scripts
    print('\n  [2] Copying civic data scripts...')
    scripts_src = PROJECT_ROOT / 'scripts' / 'data'
    civic_scripts = [
        'fetch_lgd_hierarchy.py',
        'fetch_osm_civic_features.py',
        'fetch_datameet_boundaries.py',
        'validate_civic_data.py',
        'prepare_huggingface_upload.py',
        'generate_frontend_civic_summary.py',
        'fix_boundaries.py',
    ]
    HUB_SCRIPTS.mkdir(parents=True, exist_ok=True)
    for script_name in civic_scripts:
        src = scripts_src / script_name
        if src.exists():
            dst = HUB_SCRIPTS / script_name
            shutil.copy2(src, dst)
            total_files += 1
            total_bytes += src.stat().st_size
            print(f'    {script_name}')
        else:
            print(f'    SKIP {script_name} (not found)')

    # 3. Copy frontend offline bundles
    print('\n  [3] Copying frontend offline bundles...')
    frontend_hub = HUB_ROOT / 'data' / 'frontend' / 'offline-data'
    civic_frontend_files = [
        'municipalities_bundle.json',
        'civic_features_summary.json',
    ]
    frontend_hub.mkdir(parents=True, exist_ok=True)
    for fname in civic_frontend_files:
        src = FRONTEND_OFFLINE / fname
        if src.exists():
            shutil.copy2(src, frontend_hub / fname)
            total_files += 1
            total_bytes += src.stat().st_size
            print(f'    {fname}: {_human_size(src.stat().st_size)}')
        else:
            print(f'    SKIP {fname} (not found)')

    # 4. Generate sync manifest
    manifest = {
        'synced_at': datetime.now(UTC).isoformat(),
        'source': str(PROJECT_ROOT),
        'destination': str(HUB_ROOT),
        'total_files': total_files,
        'total_bytes': total_bytes,
        'total_size_human': _human_size(total_bytes),
    }
    manifest_path = HUB_CIVIC / '_sync_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    print(f'\n{"=" * 60}')
    print('  SYNC COMPLETE')
    print(f'{"=" * 60}')
    print(f'  Files: {total_files}')
    print(f'  Size: {_human_size(total_bytes)}')
    print(f'  Destination: {HUB_ROOT}')
    print('\n  Next steps:')
    print(f'    cd {HUB_ROOT}')
    print('    git add .')
    print('    git commit -m "feat: add civic intelligence data"')
    print('    git push')
    print()


if __name__ == '__main__':
    main()
