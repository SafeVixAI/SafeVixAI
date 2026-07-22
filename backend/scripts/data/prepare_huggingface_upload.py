# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Prepare all civic intelligence data for HuggingFace Hub upload.

Usage:
    python scripts/data/prepare_huggingface_upload.py
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data' / 'civic_intel'


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.1f} MB'


def count_records(filepath: Path) -> int:
    """Count records in a data file."""
    try:
        if filepath.suffix == '.json':
            data = json.loads(filepath.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                if 'features' in data:
                    return len(data['features'])
                return len(data)
        elif filepath.suffix == '.csv':
            with open(filepath, encoding='utf-8') as f:
                return sum(1 for _ in csv.reader(f)) - 1
        elif filepath.suffix == '.geojson':
            data = json.loads(filepath.read_text(encoding='utf-8'))
            return len(data.get('features', []))
    except Exception:
        logger.debug("Suppressed exception", exc_info=True)
    return 0


def main():
    print('\n' + '=' * 60)
    print('  SafeVixAI Civic Intelligence - HuggingFace Prep')
    print('=' * 60)

    if not DATA_DIR.exists():
        print(f'  ERROR: {DATA_DIR} not found')
        return

    # Build file manifest
    manifest = {
        'name': 'SafeVixAI Civic Intelligence Dataset',
        'version': '1.0.0',
        'description': 'Comprehensive Indian civic infrastructure and municipal data for AI-powered road safety and citizen grievance systems.',
        'license': 'MIT',
        'exported_at': datetime.now(UTC).isoformat(),
        'source': 'SafeVixAI Project (IIT Madras Road Safety Hackathon 2026)',
        'categories': {},
        'files': {},
        'totals': {
            'total_files': 0,
            'total_records': 0,
            'total_size_bytes': 0,
        }
    }

    # Walk directory
    categories = {
        'boundaries': 'GeoJSON administrative boundaries (states, districts)',
        'osm_features': 'OpenStreetMap civic infrastructure features',
        'seed_data': 'Static reference datasets (LGD, road categories, grievances)',
        'municipalities': 'Municipal corporation directory',
    }
    manifest['categories'] = categories

    for filepath in sorted(DATA_DIR.rglob('*')):
        if filepath.is_dir():
            continue

        rel = str(filepath.relative_to(DATA_DIR)).replace('\\', '/')
        size = filepath.stat().st_size
        records = count_records(filepath)

        manifest['files'][rel] = {
            'size_bytes': size,
            'size_human': _human_size(size),
            'records': records,
            'format': filepath.suffix.lstrip('.'),
        }
        manifest['totals']['total_files'] += 1
        manifest['totals']['total_records'] += records
        manifest['totals']['total_size_bytes'] += size

    manifest['totals']['total_size_human'] = _human_size(manifest['totals']['total_size_bytes'])

    # Save manifest
    manifest_file = DATA_DIR / 'metadata.json'
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

    # Generate README.md dataset card
    readme = f"""---
license: mit
language:
  - en
  - hi
  - ta
  - te
  - kn
  - ml
  - mr
  - bn
  - gu
  - pa
tags:
  - india
  - civic
  - geospatial
  - road-safety
  - municipal
  - gis
  - hackathon
size_categories:
  - 10K<n<100K
---

# SafeVixAI Civic Intelligence Dataset

Comprehensive Indian civic infrastructure and municipal data powering the SafeVixAI AI-powered road safety platform.

## Dataset Description

This dataset contains:

| Category | Description | Format |
|----------|-------------|--------|
| **Administrative Boundaries** | State and district boundary polygons for all 36 states/UTs | GeoJSON |
| **OSM Civic Features** | Streetlights, traffic signals, bus stops, CCTV, speed bumps across 36 Indian cities | CSV |
| **LGD Directory** | Local Government Directory hierarchy (states, districts) with Census 2011 data | JSON |
| **Municipal Directory** | {len([f for f in manifest['files'] if 'municipalities' in f])} files with municipal corporation profiles | JSON |
| **Road Categories** | Road classification to authority mapping (Municipal/PWD/NHAI) | JSON |
| **Grievance Taxonomy** | 52-category civic grievance classification system | JSON |

## Statistics

- **Total Files**: {manifest['totals']['total_files']}
- **Total Records**: {manifest['totals']['total_records']:,}
- **Total Size**: {manifest['totals']['total_size_human']}
- **Coverage**: All 36 Indian states and UTs
- **Cities**: 36 major metros and state capitals

## Data Sources

| Source | Type | License |
|--------|------|---------|
| [LGD Directory](https://lgdirectory.gov.in/) | Government | Open Government Data |
| [OpenStreetMap](https://www.openstreetmap.org/) | Community | ODbL |
| [Census of India 2011](https://censusindia.gov.in/) | Government | Open |
| [India Maps Data](https://github.com/udit-001/india-maps-data) | Community | MIT |
| SafeVixAI Project | Original | MIT |

## Usage

```python
import json

# Load municipalities
with open('municipalities_seed.json') as f:
    municipalities = json.load(f)

# Load road categories
with open('road_categories.json') as f:
    road_map = json.load(f)

# Load OSM features
import csv
import logging
logger = logging.getLogger(__name__)
with open('osm_features/chennai_streetlight.csv') as f:
    lights = list(csv.DictReader(f))
```

## Citation

```bibtex
@misc{{safevixai2026,
  title={{SafeVixAI Civic Intelligence Dataset}},
  author={{SafeVixAI Team}},
  year={{2026}},
  publisher={{HuggingFace}},
  url={{https://huggingface.co/datasets/SafeVixHub/civic-intel-india}}
}}
```

## License

MIT License. See individual data source licenses for attribution requirements.
"""
    readme_file = DATA_DIR / 'README.md'
    readme_file.write_text(readme, encoding='utf-8')

    # Print summary
    print(f'\n  Files: {manifest["totals"]["total_files"]}')
    print(f'  Records: {manifest["totals"]["total_records"]:,}')
    print(f'  Size: {manifest["totals"]["total_size_human"]}')
    print()

    # Group by directory
    dirs = {}
    for rel, info in manifest['files'].items():
        d = rel.split('/')[0] if '/' in rel else 'root'
        dirs.setdefault(d, {'files': 0, 'records': 0, 'size': 0})
        dirs[d]['files'] += 1
        dirs[d]['records'] += info['records']
        dirs[d]['size'] += info['size_bytes']

    for d, stats in sorted(dirs.items()):
        print(f'  {d:25s}  {stats["files"]:>3} files  {stats["records"]:>8,} records  {_human_size(stats["size"]):>10s}')

    print('\n  Generated:')
    print(f'    {manifest_file}')
    print(f'    {readme_file}')
    print('\n  Upload to HuggingFace:')
    print('    huggingface-cli upload SafeVixHub/civic-intel-india \\')
    print(f'      {DATA_DIR} .')
    print()


if __name__ == '__main__':
    main()
