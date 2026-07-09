# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import json

from agent.tool_summarizer import ToolPayloadSummarizer


class TestToolPayloadSummarizer:
    def setup_method(self):
        self.summarizer = ToolPayloadSummarizer()

    def test_summarize_weather_open_meteo(self):
        data = {
            "current": {"temperature_2m": 32, "wind_speed_10m": 15, "precipitation": 0},
            "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"}
        }
        result = self.summarizer._summarize_weather(data)
        assert "32°C" in result
        assert "15km/h" in result
        assert "0mm" in result

    def test_summarize_weather_openweathermap(self):
        data = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 305}
        }
        result = self.summarizer._summarize_weather(data)
        assert "clear sky" in result
        assert "305K" in result

    def test_summarize_weather_fallback(self):
        data = {"foo": "bar"}
        result = self.summarizer._summarize_weather(data)
        assert result == json.dumps(data)

    def test_summarize_weather_exception(self):
        class ExplodingDict(dict):
            def get(self, key, default=None):
                raise RuntimeError("boom")
        result = self.summarizer._summarize_weather({"current": ExplodingDict({"temperature_2m": 32})})
        assert "boom" not in result

    def test_summarize_geocoding_opencage(self):
        data = {
            "results": [{
                "formatted": "Chennai, Tamil Nadu, India",
                "components": {"city": "Chennai", "state": "Tamil Nadu"}
            }]
        }
        result = self.summarizer._summarize_geocoding(data)
        assert "Chennai" in result
        assert "Tamil Nadu" in result

    def test_summarize_geocoding_nominatim(self):
        data = {"display_name": "Chennai, Tamil Nadu, India"}
        result = self.summarizer._summarize_geocoding(data)
        assert "Chennai" in result
        assert "Tamil Nadu" in result

    def test_summarize_geocoding_fallback(self):
        data = {"foo": "bar"}
        result = self.summarizer._summarize_geocoding(data)
        assert result == json.dumps(data)

    def test_summarize_geocoding_exception(self):
        class ExplodingDict(dict):
            def get(self, key, default=None):
                raise RuntimeError("boom")
        result = self.summarizer._summarize_geocoding({"results": [ExplodingDict({"components": {}})]})
        assert "boom" not in result

    def test_summarize_w3w(self):
        data = {"words": "filled.soap.lemon"}
        result = self.summarizer._summarize_w3w(data)
        assert "///filled.soap.lemon" in result

    def test_summarize_w3w_fallback(self):
        data = {"foo": "bar"}
        result = self.summarizer._summarize_w3w(data)
        assert result == json.dumps(data)

    def test_summarize_w3w_exception(self):
        class ExplodingDict(dict):
            def __getitem__(self, key):
                raise RuntimeError("boom")
        result = self.summarizer._summarize_w3w(ExplodingDict({"words": "filled.soap.lemon"}))
        assert "boom" not in result

    def test_summarize_none_payload(self):
        result = self.summarizer.summarize("weather", None)
        assert result == "No data"

    def test_summarize_empty_payload(self):
        result = self.summarizer.summarize("weather", "")
        assert result == "No data"

    def test_summarize_string_json(self):
        data = json.dumps({"current": {"temperature_2m": 32}})
        result = self.summarizer.summarize("weather", data)
        assert "32" in result

    def test_summarize_invalid_json_string(self):
        result = self.summarizer.summarize("weather", "not json")
        assert "not json" in result

    def test_summarize_long_string_truncated(self):
        long_str = "a" * 1000
        result = self.summarizer.summarize("weather", long_str)
        assert len(result) <= 504

    def test_summarize_dict_non_string(self):
        result = self.summarizer.summarize("weather", [1, 2, 3])
        assert '"data"' in result

    def test_summarize_weather_routing(self):
        data = {"current": {"temperature_2m": 32, "wind_speed_10m": 10, "precipitation": 0}, "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"}}
        result = self.summarizer.summarize("open_meteo", data)
        assert "32°C" in result

    def test_summarize_geocoding_routing(self):
        data = {"results": [{"formatted": "Chennai", "components": {"city": "Chennai", "state": "TN"}}]}
        result = self.summarizer.summarize("geocoding", data)
        assert "Chennai" in result

    def test_summarize_w3w_routing(self):
        data = {"words": "filled.soap.lemon"}
        result = self.summarizer.summarize("what3words", data)
        assert "///filled.soap.lemon" in result

    def test_summarize_fallback_compression_short(self):
        data = {"key": "value"}
        result = self.summarizer.summarize("unknown_tool", data)
        assert "value" in result

    def test_summarize_fallback_compression_truncated(self):
        data = {"large": "x" * 2000}
        result = self.summarizer.summarize("unknown_tool", data)
        assert "... [truncated]" in result
