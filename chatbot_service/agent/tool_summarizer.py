# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolPayloadSummarizer:
    """Summarizes and compresses raw JSON payloads from tools to save LLM tokens."""

    @staticmethod
    def _summarize_weather(data: dict[str, Any]) -> str:
        """Compress Open-Meteo or weather data."""
        try:
            if 'current' in data:
                current = data['current']
                units = data.get('current_units', {})
                temp = f"{current.get('temperature_2m', 'N/A')}{units.get('temperature_2m', '°C')}"
                wind = f"{current.get('wind_speed_10m', 'N/A')}{units.get('wind_speed_10m', 'km/h')}"
                return f"Weather: {temp}, Wind: {wind}, Precipitation: {current.get('precipitation', 0)}mm"
            elif 'weather' in data and isinstance(data['weather'], list) and data['weather']:
                # OpenWeatherMap style
                w = data['weather'][0]
                main = data.get('main', {})
                return f"Weather: {w.get('description', 'Unknown')}, Temp: {main.get('temp', 'N/A')}K"
            return json.dumps(data)
        except Exception as e:
            logger.warning("Error summarizing weather: %s", e)
            return json.dumps(data)

    @staticmethod
    def _summarize_geocoding(data: dict[str, Any]) -> str:
        """Compress OpenCage or Nominatim data."""
        try:
            if 'results' in data and isinstance(data['results'], list) and data['results']:
                res = data['results'][0]
                addr = res.get('formatted', res.get('display_name', 'Unknown Address'))
                components = res.get('components', {})
                city = components.get('city', components.get('town', components.get('village', 'Unknown')))
                state = components.get('state', 'Unknown')
                return f"Location: {addr} (City: {city}, State: {state})"
            elif 'display_name' in data:
                return f"Location: {data['display_name']}"
            return json.dumps(data)
        except Exception as e:
            logger.warning("Error summarizing geocoding: %s", e)
            return json.dumps(data)

    @staticmethod
    def _summarize_w3w(data: dict[str, Any]) -> str:
        """Compress What3Words data."""
        try:
            if 'words' in data:
                return f"What3Words: ///{data['words']}"
            return json.dumps(data)
        except Exception as e:
            logger.warning("Error summarizing w3w: %s", e)
            return json.dumps(data)

    def summarize(self, tool_name: str, payload: Any) -> str:
        """Route to specific summarizers based on heuristic matching of payload or tool name."""
        if not payload:
            return "No data"

        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                return payload[:500] + "..." if len(payload) > 500 else payload
        elif isinstance(payload, dict):
            data = payload
        else:
            data = {"data": str(payload)}

        tool_name_lower = tool_name.lower()
        if 'weather' in tool_name_lower or 'meteo' in tool_name_lower:
            return self._summarize_weather(data)
        if 'geo' in tool_name_lower or 'location' in tool_name_lower:
            return self._summarize_geocoding(data)
        if 'w3w' in tool_name_lower or 'what3words' in tool_name_lower:
            return self._summarize_w3w(data)

        # Fallback JSON compression
        compressed = json.dumps(data, separators=(',', ':'))
        if len(compressed) > 1000:
            return compressed[:1000] + "... [truncated]"
        return compressed
