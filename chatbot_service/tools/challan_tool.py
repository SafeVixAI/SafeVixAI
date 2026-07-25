# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import re

from tools import BackendToolClient
from utils.ip_location import detect_state_from_ip

STATE_TO_CODE = {
    'tamil nadu': 'TN',
    'delhi': 'DL',
    'maharashtra': 'MH',
    'karnataka': 'KA',
    'uttar pradesh': 'UP',
    'west bengal': 'WB',
    'kerala': 'KL',
    'andhra pradesh': 'AP',
    'telangana': 'TS',
    'rajasthan': 'RJ',
    'gujarat': 'GJ',
}


VIOLATION_CODE_PATTERN = re.compile(r'\b(?:179|181|183|185|194B|194D)\b', re.IGNORECASE)
STATE_PATTERN = re.compile(r'\b(?:TN|DL|MH|KA|UP|WB|KL|AP|TS|RJ|GJ)\b', re.IGNORECASE)


class ChallanTool:
    def __init__(self, backend_client: BackendToolClient) -> None:
        self.backend_client = backend_client

    async def calculate(
        self,
        *,
        violation_code: str,
        vehicle_class: str,
        state_code: str,
        is_repeat: bool,
    ) -> dict | None:
        return await self.backend_client.post(
            '/api/v1/challan/calculate',
            payload={
                'violation_code': violation_code,
                'vehicle_class': vehicle_class,
                'state_code': state_code,
                'is_repeat': is_repeat,
            },
        )

    async def infer_and_calculate(self, message: str, client_ip: str | None = None) -> dict | None:
        violation_match = VIOLATION_CODE_PATTERN.search(message)
        if violation_match is None:
            return None
        state_match = STATE_PATTERN.search(message)
        vehicle_class = self._infer_vehicle_class(message)
        is_repeat = any(term in message.lower() for term in ('repeat', 'second time', 'again'))

        if state_match:
            resolved_state_code = state_match.group(0).upper()
        else:
            ip_info = await detect_state_from_ip(client_ip)
            state_name = ip_info.get('state', '').lower()
            resolved_state_code = STATE_TO_CODE.get(state_name, 'TN')

        return await self.calculate(
            violation_code=violation_match.group(0).upper(),
            vehicle_class=vehicle_class,
            state_code=resolved_state_code,
            is_repeat=is_repeat,
        )

    @staticmethod
    def _infer_vehicle_class(message: str) -> str:
        text = message.lower()
        if any(term in text for term in ('bike', 'motorcycle', 'scooter', '2w')):
            return 'two_wheeler'
        if any(term in text for term in ('truck', 'lorry', 'htv')):
            return 'heavy_vehicle'
        if any(term in text for term in ('bus', 'comm', 'commercial bus')):
            return 'bus'
        return 'light_motor_vehicle'
