# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import csv
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from core.metrics import challan_calculation_total
from models.challan import ChallanRule, StateChallanOverride
from models.schemas import ChallanQuery, ChallanResponse
from services.exceptions import ExternalServiceError, ServiceValidationError

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

INDIAN_STATE_CODE_ALIASES = {
    'ANDHRAPRADESH': 'AP',
    'ARUNACHALPRADESH': 'AR',
    'ASSAM': 'AS',
    'BIHAR': 'BR',
    'CHHATTISGARH': 'CG',
    'GOA': 'GA',
    'GUJARAT': 'GJ',
    'HARYANA': 'HR',
    'HIMACHALPRADESH': 'HP',
    'JHARKHAND': 'JH',
    'KARNATAKA': 'KA',
    'KERALA': 'KL',
    'MADHYAPRADESH': 'MP',
    'MAHARASHTRA': 'MH',
    'MANIPUR': 'MN',
    'MEGHALAYA': 'ML',
    'MIZORAM': 'MZ',
    'NAGALAND': 'NL',
    'ODISHA': 'OD',
    'ORISSA': 'OD',
    'PUNJAB': 'PB',
    'RAJASTHAN': 'RJ',
    'SIKKIM': 'SK',
    'TAMILNADU': 'TN',
    'TELANGANA': 'TS',
    'TRIPURA': 'TR',
    'UTTARPRADESH': 'UP',
    'UTTARAKHAND': 'UK',
    'WESTBENGAL': 'WB',
    'ANDAMANANDNICOBARISLANDS': 'AN',
    'CHANDIGARH': 'CH',
    'DADRAANDNAGARHAVELIANDDAMANANDDIU': 'DN',
    'DELHI': 'DL',
    'NATIONALCAPITALTERRITORYOFDELHI': 'DL',
    'JAMMUANDKASHMIR': 'JK',
    'LADAKH': 'LA',
    'LAKSHADWEEP': 'LD',
    'PUDUCHERRY': 'PY',
    'PONDICHERRY': 'PY',
}

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


class ChallanService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.rules = list(DEFAULT_RULES)
        self.state_overrides: list[StateChallanOverride] = []
        self._load_optional_files()

    def calculate(self, query: ChallanQuery) -> ChallanResponse:
        violation_code = self._normalize_violation_code(query.violation_code)
        vehicle_class = self._normalize_vehicle_class(query.vehicle_class)
        state_code = self._normalize_state_code(query.state_code)

        rule = self._find_rule(violation_code)
        if rule is None:
            msg = (
                f'Unsupported violation code "{query.violation_code}". '
                'Known examples include 183, 185, 181, 194D, 194B, and 179.'
            )
            raise ServiceValidationError(
                msg
            )

        base_fine = rule.fine_for_vehicle(vehicle_class)
        repeat_fine = rule.repeat_fine_for_vehicle(vehicle_class)
        override_note = None

        override = self._find_override(
            state_code=state_code,
            violation_code=rule.violation_code,
            vehicle_class=vehicle_class,
        )
        if override is not None:
            base_fine = override.base_fine
            repeat_fine = override.repeat_fine if override.repeat_fine is not None else repeat_fine
            if override.section or override.description:
                rule = ChallanRule(
                    violation_code=rule.violation_code,
                    section=override.section or rule.section,
                    description=override.description or rule.description,
                    base_fines={vehicle_class: base_fine, 'default': base_fine},
                    repeat_fines={vehicle_class: repeat_fine, 'default': repeat_fine or base_fine},
                    aliases=rule.aliases,
                )
            override_note = override.note or f'{state_code} override applied'

        amount_due = repeat_fine if query.is_repeat and repeat_fine is not None else base_fine
        challan_calculation_total.labels(violation_code=rule.violation_code, source='csv').inc()
        return ChallanResponse(
            violation_code=rule.violation_code,
            vehicle_class=vehicle_class,
            state_code=state_code,
            base_fine=base_fine,
            repeat_fine=repeat_fine,
            amount_due=amount_due,
            section=rule.section,
            description=rule.description,
            state_override=override_note,
        )

    async def calculate_with_db(self, query: ChallanQuery, *, db: AsyncSession) -> ChallanResponse:
        violation_code = self._normalize_violation_code(query.violation_code)
        vehicle_class = self._normalize_vehicle_class(query.vehicle_class)
        state_code = self._normalize_state_code(query.state_code)

        try:
            result = await db.execute(
                text("""
                    SELECT violation_code, vehicle_class, section, description, base_fine, repeat_fine
                    FROM traffic_violations
                    WHERE is_active = true
                      AND (violation_code = :violation_code OR :violation_code = ANY(aliases))
                      AND (vehicle_class = :vehicle_class OR vehicle_class = 'default')
                    ORDER BY CASE WHEN vehicle_class = :vehicle_class THEN 0 ELSE 1 END
                    LIMIT 1
                """),
                {"violation_code": violation_code, "vehicle_class": vehicle_class},
            )
            row = result.mappings().first()
        except (SQLAlchemyError, DBAPIError, AttributeError, RuntimeError) as exc:
            msg = 'Challan database lookup is unavailable'
            raise ExternalServiceError(msg) from exc

        if row is None:
            msg = f'Unsupported or unseeded violation code "{query.violation_code}" for vehicle "{query.vehicle_class}".'
            raise ServiceValidationError(
                msg
            )

        base_fine = int(row["base_fine"])
        repeat_fine = int(row["repeat_fine"]) if row["repeat_fine"] is not None else None
        section = str(row["section"])
        description = str(row["description"])
        override_note = None

        override_result = await db.execute(
            text("""
                SELECT base_fine, repeat_fine, section, description, note
                FROM state_fine_overrides
                WHERE state_code = :state_code
                  AND violation_code = :violation_code
                  AND (vehicle_class = :vehicle_class OR vehicle_class IS NULL OR vehicle_class = 'default')
                ORDER BY CASE WHEN vehicle_class = :vehicle_class THEN 0 ELSE 1 END
                LIMIT 1
            """),
            {
                "state_code": state_code,
                "violation_code": row["violation_code"],
                "vehicle_class": vehicle_class,
            },
        )
        override = override_result.mappings().first()
        if override is not None:
            base_fine = int(override["base_fine"])
            repeat_fine = int(override["repeat_fine"]) if override["repeat_fine"] is not None else repeat_fine
            section = str(override["section"] or section)
            description = str(override["description"] or description)
            override_note = override["note"] or f'{state_code} override applied'

        amount_due = repeat_fine if query.is_repeat and repeat_fine is not None else base_fine
        return ChallanResponse(
            violation_code=str(row["violation_code"]),
            vehicle_class=vehicle_class,
            state_code=state_code,
            base_fine=base_fine,
            repeat_fine=repeat_fine,
            amount_due=amount_due,
            section=section,
            description=description,
            state_override=override_note,
        )

    def _load_optional_files(self) -> None:
        for candidate in self._candidate_data_dirs():
            violations_csv = candidate / 'violations.csv'
            overrides_csv = candidate / 'state_overrides.csv'
            if violations_csv.exists():
                self._load_rules_csv(violations_csv)
            if overrides_csv.exists():
                self._load_state_overrides_csv(overrides_csv)

    def _candidate_data_dirs(self) -> list[Path]:
        project_root = Path(__file__).resolve().parents[2]
        return [
            self.settings.data_dir / 'challan',
            project_root / 'frontend' / 'public' / 'offline-data',
            project_root / 'backend' / 'datasets' / 'challan',
        ]

    def _load_rules_csv(self, csv_path: Path) -> None:
        try:
            with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    return
                loaded_rules: list[ChallanRule] = []
                for row in reader:
                    violation_code = self._normalize_violation_code(row.get('violation_code') or row.get('code') or '')
                    if not violation_code:
                        continue
                    section = (row.get('section') or row.get('mva_section') or '').strip() or f'Section {violation_code}'
                    description = (row.get('description') or row.get('label') or '').strip() or 'Traffic rule violation.'
                    base_fines = self._extract_fines(row, prefix='base_fine')
                    if not base_fines:
                        default_base = self._parse_money(row.get('fine') or row.get('base') or '')
                        if default_base is not None:
                            base_fines['default'] = default_base
                    if not base_fines:
                        continue
                    repeat_fines = self._extract_fines(row, prefix='repeat_fine')
                    aliases = tuple(
                        self._normalize_violation_code(item)
                        for item in (row.get('aliases') or '').split('|')
                        if item.strip()
                    )
                    loaded_rules.append(
                        ChallanRule(
                            violation_code=violation_code,
                            section=section,
                            description=description,
                            base_fines=base_fines,
                            repeat_fines=repeat_fines,
                            aliases=aliases,
                        )
                    )
                if loaded_rules:
                    self.rules = loaded_rules
        except OSError:
            return

    def _load_state_overrides_csv(self, csv_path: Path) -> None:
        try:
            with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    return
                for row in reader:
                    violation_code = self._normalize_violation_code(row.get('violation_code') or row.get('code') or '')
                    raw_state_code = row.get('state_code') or row.get('state') or ''
                    if not raw_state_code.strip():
                        continue
                    state_code = self._normalize_state_code(raw_state_code)
                    base_fine = self._parse_money(row.get('base_fine') or row.get('fine') or '')
                    if not violation_code or not state_code or base_fine is None:
                        continue
                    vehicle_value = row.get('vehicle_class') or row.get('vehicle') or ''
                    self.state_overrides.append(
                        StateChallanOverride(
                            state_code=state_code,
                            violation_code=violation_code,
                            vehicle_class=self._normalize_vehicle_class(vehicle_value) if vehicle_value.strip() else None,
                            base_fine=base_fine,
                            repeat_fine=self._parse_money(row.get('repeat_fine') or ''),
                            section=(row.get('section') or '').strip() or None,
                            description=(row.get('description') or '').strip() or None,
                            note=(row.get('note') or row.get('state_override') or '').strip() or None,
                        )
                    )
        except OSError:
            return

    def _find_rule(self, violation_code: str) -> ChallanRule | None:
        for rule in self.rules:
            if rule.matches(violation_code):
                return rule
        return None

    def _find_override(
        self,
        *,
        state_code: str,
        violation_code: str,
        vehicle_class: str,
    ) -> StateChallanOverride | None:
        for override in self.state_overrides:
            if override.matches(
                state_code=state_code,
                violation_code=violation_code,
                vehicle_class=vehicle_class,
            ):
                return override
        return None

    @staticmethod
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
                amount = ChallanService._parse_money(row.get(column) or '')
                if amount is not None:
                    fines[vehicle_class] = amount
                    break
        return fines

    @staticmethod
    def _parse_money(value: str) -> int | None:
        if not value:
            return None
        normalized = re.sub(r'[^0-9]', '', value)
        if not normalized:
            return None
        return int(normalized)

    @staticmethod
    def _normalize_violation_code(value: str) -> str:
        return re.sub(r'[^A-Z0-9/]', '', value.strip().upper())

    @staticmethod
    def _normalize_vehicle_class(value: str) -> str:
        normalized = re.sub(r'[^A-Z0-9_ ]', '', value.strip().upper()).replace(' ', '_')
        if not normalized:
            msg = 'vehicle_class is required'
            raise ServiceValidationError(msg)
        return VEHICLE_CLASS_ALIASES.get(normalized, normalized.lower())

    @staticmethod
    def _normalize_state_code(value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            msg = 'state_code is required'
            raise ServiceValidationError(msg)
        if '(' in cleaned and ')' in cleaned:
            inside = cleaned.split('(')[-1].split(')')[0].strip()
            if inside:
                cleaned = inside
        if len(cleaned) > 2:
            compact = re.sub(r'[^A-Z]', '', cleaned)
            if compact in INDIAN_STATE_CODE_ALIASES:
                return INDIAN_STATE_CODE_ALIASES[compact]
            if len(compact) >= 2:
                cleaned = compact[:2]
        return cleaned
