# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
CHATBOT_DATA_DIR = PROJECT_ROOT / 'chatbot_service' / 'data'


VEHICLE_CLASS_ALIASES = {
    '2W': 'two_wheeler',
    'BIKE': 'two_wheeler',
    'MOTORCYCLE': 'two_wheeler',
    'SCOOTER': 'two_wheeler',
    '4W': 'light_motor_vehicle',
    'CAR': 'light_motor_vehicle',
    'LMV': 'light_motor_vehicle',
    'AUTO': 'light_motor_vehicle',
    'HTV': 'heavy_vehicle',
    'HGV': 'heavy_vehicle',
    'TRUCK': 'heavy_vehicle',
    'BUS': 'bus',
    'COMM': 'bus',
    'COMMERCIAL': 'bus',
}


@dataclass(frozen=True, slots=True)
class ChallanRule:
    violation_code: str
    section: str
    description: str
    base_fines: dict[str, int]
    repeat_fines: dict[str, int] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()


DEFAULT_RULES: tuple[ChallanRule, ...] = (
    ChallanRule(
        violation_code='183',
        section='Section 183',
        description='Speeding beyond the notified limit.',
        base_fines={
            'two_wheeler': 1000,
            'light_motor_vehicle': 2000,
            'heavy_vehicle': 4000,
            'bus': 4000,
            'default': 2000,
        },
        repeat_fines={
            'two_wheeler': 2000,
            'light_motor_vehicle': 4000,
            'heavy_vehicle': 8000,
            'bus': 8000,
            'default': 4000,
        },
        aliases=('112/183',),
    ),
    ChallanRule(
        violation_code='185',
        section='Section 185',
        description='Driving under the influence of alcohol or drugs.',
        base_fines={'default': 10000},
        repeat_fines={'default': 15000},
        aliases=('DUI', 'DRUNK'),
    ),
    ChallanRule(
        violation_code='181',
        section='Sections 3/181',
        description='Driving without a valid driving licence.',
        base_fines={'default': 5000},
        repeat_fines={'default': 10000},
        aliases=('3/181',),
    ),
    ChallanRule(
        violation_code='194D',
        section='Sections 129/194D',
        description='Failure to wear a helmet or seat belt as required.',
        base_fines={'default': 1000},
        repeat_fines={'default': 2000},
        aliases=('194D-HELMET', '194D-SEATBELT'),
    ),
    ChallanRule(
        violation_code='194B',
        section='Section 194B',
        description='Safety gear non-compliance on a two-wheeler or while carrying a child.',
        base_fines={
            'two_wheeler': 1000,
            'light_motor_vehicle': 1000,
            'default': 1000,
        },
        repeat_fines={'default': 2000},
    ),
    ChallanRule(
        violation_code='179',
        section='Section 179',
        description='Disobedience, obstruction, or refusal to comply with lawful directions.',
        base_fines={'default': 2000},
        repeat_fines={'default': 4000},
    ),
)


RULE_COLUMNS = [
    'violation_code',
    'section',
    'description',
    'base_fine',
    'base_fine_2w',
    'base_fine_4w',
    'base_fine_htv',
    'base_fine_bus',
    'repeat_fine',
    'repeat_fine_2w',
    'repeat_fine_4w',
    'repeat_fine_htv',
    'repeat_fine_bus',
    'aliases',
]
OVERRIDE_COLUMNS = [
    'state_code',
    'violation_code',
    'vehicle_class',
    'base_fine',
    'repeat_fine',
    'section',
    'description',
    'note',
]
DEFAULT_OUTPUT_DIR = BACKEND_DIR / 'datasets' / 'challan'
RULE_SOURCE_CANDIDATES = ('violations_seed.csv', 'violations.csv')
OVERRIDE_SOURCE_CANDIDATES = ('state_overrides_seed.csv', 'state_overrides.csv')


def _resolve_source(output_dir: Path, candidates: tuple[str, ...], explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    for name in candidates:
        candidate = output_dir / name
        if candidate.exists():
            return candidate
    for name in candidates:
        candidate = CHATBOT_DATA_DIR / name
        if candidate.exists():
            return candidate
    return None


def _stringify(amount: int | None) -> str:
    return '' if amount is None else str(amount)


def _rule_to_row(rule: ChallanRule) -> dict[str, str]:
    return {
        'violation_code': rule.violation_code,
        'section': rule.section,
        'description': rule.description,
        'base_fine': _stringify(rule.base_fines.get('default')),
        'base_fine_2w': _stringify(rule.base_fines.get('two_wheeler')),
        'base_fine_4w': _stringify(rule.base_fines.get('light_motor_vehicle')),
        'base_fine_htv': _stringify(rule.base_fines.get('heavy_vehicle')),
        'base_fine_bus': _stringify(rule.base_fines.get('bus')),
        'repeat_fine': _stringify(rule.repeat_fines.get('default')),
        'repeat_fine_2w': _stringify(rule.repeat_fines.get('two_wheeler')),
        'repeat_fine_4w': _stringify(rule.repeat_fines.get('light_motor_vehicle')),
        'repeat_fine_htv': _stringify(rule.repeat_fines.get('heavy_vehicle')),
        'repeat_fine_bus': _stringify(rule.repeat_fines.get('bus')),
        'aliases': '|'.join(rule.aliases),
    }


def _normalize_rule_row(row: dict[str, str]) -> dict[str, str] | None:
    raw_violation_code = (
        row.get('violation_code')
        or row.get('code')
        or row.get('violation')
        or ''
    ).strip()
    violation_code, qualifier = _split_violation_code(raw_violation_code)
    violation_code = _normalize_violation_code(
        violation_code
    )
    if not violation_code:
        return None

    section = (row.get('section') or row.get('mva_section') or '').strip() or f'Section {violation_code}'
    description = (row.get('description') or row.get('description_en') or row.get('label') or '').strip() or 'Traffic rule violation.'
    base_fines = _extract_fines(row, prefix='base_fine')
    if not base_fines:
        default_base = _parse_money(row.get('fine') or row.get('base') or row.get('amount') or '')
        if default_base is not None:
            base_fines['default'] = default_base
    seed_base = _parse_money(row.get('base_fine_inr') or '')
    seed_repeat = _parse_money(row.get('repeat_fine_inr') or '')
    seed_vehicle_class = _normalize_seed_vehicle_class(row.get('vehicle_type') or qualifier or '')
    if qualifier == 'REPEAT':
        repeat_fines = {seed_vehicle_class: seed_base} if seed_base is not None else {}
    else:
        repeat_fines = _extract_fines(row, prefix='repeat_fine')
        if seed_base is not None:
            base_fines[seed_vehicle_class] = seed_base
        if seed_repeat is not None:
            repeat_fines[seed_vehicle_class] = seed_repeat
    if not base_fines:
        return None

    if not repeat_fines:
        default_repeat = _parse_money(row.get('repeat') or row.get('repeat_amount') or '')
        if default_repeat is not None:
            repeat_fines['default'] = default_repeat

    aliases = [
        _normalize_violation_code(item)
        for item in (row.get('aliases') or row.get('alternate_codes') or '').split('|')
        if item.strip()
    ]
    return _rule_to_row(
        ChallanRule(
            violation_code=violation_code,
            section=section,
            description=description,
            base_fines=base_fines,
            repeat_fines=repeat_fines,
            aliases=tuple(aliases),
        )
    )


def _load_rule_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        rows_by_code: dict[str, dict[str, str]] = {}
        for raw in reader:
            normalized = _normalize_rule_row(raw)
            if normalized is not None:
                code = normalized['violation_code']
                existing = rows_by_code.get(code)
                rows_by_code[code] = _merge_rule_rows(existing, normalized) if existing else normalized
        return [rows_by_code[key] for key in sorted(rows_by_code)]


def _normalize_override_row(row: dict[str, str]) -> dict[str, str] | None:
    raw_state = row.get('state_code') or row.get('state') or ''
    if not raw_state.strip():
        return None
    state_code = _normalize_state_code(raw_state)
    violation_code = _normalize_violation_code(
        row.get('violation_code')
        or row.get('code')
        or row.get('violation')
        or ''
    )
    base_fine = _parse_money(
        row.get('base_fine')
        or row.get('fine')
        or row.get('amount')
        or row.get('override_fine')
        or ''
    )
    if not violation_code or base_fine is None:
        return None

    vehicle_class = (row.get('vehicle_class') or row.get('vehicle') or '').strip()
    normalized_vehicle_class = ''
    if vehicle_class:
        normalized_vehicle_class = _normalize_vehicle_class(vehicle_class)

    authority = (row.get('authority') or row.get('source_title') or '').strip()
    effective_date = (row.get('effective_date') or '').strip()
    source_url = (row.get('source_url') or '').strip()
    verified_on = (row.get('verified_on') or '').strip()
    note_parts = [
        (row.get('note') or row.get('state_override') or row.get('remarks') or '').strip(),
        authority,
        f'effective {effective_date}' if effective_date else '',
        f'verified {verified_on}' if verified_on else '',
        f'source {source_url}' if source_url else '',
    ]

    return {
        'state_code': state_code,
        'violation_code': violation_code,
        'vehicle_class': normalized_vehicle_class,
        'base_fine': str(base_fine),
        'repeat_fine': _stringify(
            _parse_money(row.get('repeat_fine') or row.get('repeat') or row.get('repeat_amount') or '')
        ),
        'section': (row.get('section') or '').strip(),
        'description': (row.get('description') or row.get('description_en') or '').strip(),
        'note': '; '.join(part for part in note_parts if part),
    }


def _extract_fines(row: dict[str, str], *, prefix: str) -> dict[str, int]:
    mapping = {
        'two_wheeler': [f'{prefix}_2w', f'{prefix}_two_wheeler'],
        'light_motor_vehicle': [f'{prefix}_4w', f'{prefix}_lmv', f'{prefix}_car'],
        'heavy_vehicle': [f'{prefix}_htv', f'{prefix}_truck', f'{prefix}_heavy_vehicle'],
        'bus': [f'{prefix}_bus', f'{prefix}_comm'],
        'default': [prefix, f'{prefix}_default'],
    }
    fines: dict[str, int] = {}
    for vehicle_class, columns in mapping.items():
        for column in columns:
            amount = _parse_money(row.get(column) or '')
            if amount is not None:
                fines[vehicle_class] = amount
                break
    return fines


def _parse_money(value: str) -> int | None:
    if not value:
        return None
    normalized = re.sub(r'[^0-9]', '', value)
    if not normalized:
        return None
    return int(normalized)


def _normalize_violation_code(value: str) -> str:
    return re.sub(r'[^A-Z0-9/]', '', value.strip().upper())


def _split_violation_code(value: str) -> tuple[str, str]:
    text = value.strip().upper()
    if not text:
        return '', ''
    parts = [part for part in re.split(r'[_\-\s]+', text) if part]
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], parts[1]


def _normalize_vehicle_class(value: str) -> str:
    normalized = re.sub(r'[^A-Z0-9_ ]', '', value.strip().upper()).replace(' ', '_')
    if not normalized:
        raise ValueError('vehicle_class is required')
    return VEHICLE_CLASS_ALIASES.get(normalized, normalized.lower())


def _normalize_seed_vehicle_class(value: str) -> str:
    normalized = re.sub(r'[^A-Z0-9_ ]', '', value.strip().upper()).replace(' ', '_')
    if not normalized or normalized == 'ALL' or normalized == 'FIRST' or normalized == 'REPEAT':
        return 'default'
    if normalized in {'LMV', '4W', 'CAR', 'LIGHT_MOTOR_VEHICLE'}:
        return 'light_motor_vehicle'
    if normalized in {'HMV', 'HTV', 'HEAVY_VEHICLE', 'GOODS_VEHICLE'}:
        return 'heavy_vehicle'
    if normalized in {'BUS', 'SCHOOL_VEHICLE', 'TRANSPORT_VEHICLE'}:
        return 'bus'
    if normalized in {'2W', 'BIKE', 'MOTORCYCLE', 'TWO_WHEELER'}:
        return 'two_wheeler'
    return _normalize_vehicle_class(normalized)


def _merge_rule_rows(existing: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    merged = dict(existing)
    for column in RULE_COLUMNS:
        if column == 'aliases':
            aliases = {
                item.strip()
                for item in (merged.get('aliases') or '').split('|') + (incoming.get('aliases') or '').split('|')
                if item.strip()
            }
            merged['aliases'] = '|'.join(sorted(aliases))
            continue
        if incoming.get(column):
            merged[column] = incoming[column]
    return merged


def _normalize_state_code(value: str) -> str:
    cleaned = value.strip().upper()
    if not cleaned:
        raise ValueError('state_code is required')
    if '(' in cleaned and ')' in cleaned:
        inside = cleaned.split('(')[-1].split(')')[0].strip()
        if inside:
            cleaned = inside
    if len(cleaned) > 2:
        compact = re.sub(r'[^A-Z]', '', cleaned)
        if len(compact) >= 2:
            cleaned = compact[:2]
    return cleaned


def _load_override_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        rows: list[dict[str, str]] = []
        for raw in reader:
            normalized = _normalize_override_row(raw)
            if normalized is not None:
                rows.append(normalized)
        return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Normalize challan seed data into the backend CSVs used by the challan service.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f'Directory that receives violations.csv and state_overrides.csv. Defaults to {DEFAULT_OUTPUT_DIR}',
    )
    parser.add_argument(
        '--rules-source',
        type=Path,
        help='Optional source CSV to normalize into violations.csv.',
    )
    parser.add_argument(
        '--overrides-source',
        type=Path,
        help='Optional source CSV to normalize into state_overrides.csv.',
    )
    parser.add_argument(
        '--defaults-only',
        action='store_true',
        help='Ignore source files and emit only the backend built-in challan rules.',
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    rules_path = output_dir / 'violations.csv'
    overrides_path = output_dir / 'state_overrides.csv'

    rule_map: dict[str, dict[str, str]] = {
        rule.violation_code: _rule_to_row(rule)
        for rule in DEFAULT_RULES
    }

    source_rules = None if args.defaults_only else _resolve_source(output_dir, RULE_SOURCE_CANDIDATES, args.rules_source)
    if source_rules and source_rules.exists():
        for row in _load_rule_rows(source_rules):
            existing = rule_map.get(row['violation_code'])
            rule_map[row['violation_code']] = _merge_rule_rows(existing, row) if existing else row

    override_rows: list[dict[str, str]] = []
    source_overrides = None if args.defaults_only else _resolve_source(output_dir, OVERRIDE_SOURCE_CANDIDATES, args.overrides_source)
    if source_overrides and source_overrides.exists():
        override_rows = _load_override_rows(source_overrides)

    sorted_rules = [rule_map[key] for key in sorted(rule_map)]
    sorted_overrides = sorted(
        override_rows,
        key=lambda row: (row['state_code'], row['violation_code'], row['vehicle_class']),
    )

    _write_csv(rules_path, RULE_COLUMNS, sorted_rules)
    _write_csv(overrides_path, OVERRIDE_COLUMNS, sorted_overrides)

    print(
        f'Wrote {len(sorted_rules)} challan rules to {rules_path} '
        f'and {len(sorted_overrides)} state overrides to {overrides_path}'
    )


if __name__ == '__main__':
    main()
