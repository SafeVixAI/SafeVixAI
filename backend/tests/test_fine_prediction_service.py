# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import pathlib
import re
from unittest.mock import mock_open, patch

import services.fine_prediction_service as _fps
from models.schemas import FinePredictionRequest, TelemetryDataPoint

FinePredictionService = _fps.FinePredictionService
DEFAULT_FINES = _fps.DEFAULT_FINES

_fps.re = re


def _payload(vehicle_number="TN-01-AB-1234", state_code="DL",
             speeding_events=0, harsh_braking_events=0,
             night_driving_minutes=0):
    return FinePredictionRequest(
        vehicle_number=vehicle_number,
        state_code=state_code,
        telemetry=TelemetryDataPoint(
            speeding_events=speeding_events,
            harsh_braking_events=harsh_braking_events,
            night_driving_minutes=night_driving_minutes,
        )
    )


class TestLoadStateFineOverrides:
    def test_returns_default_when_no_csv(self):
        with patch.object(pathlib.Path, "exists", return_value=False):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines == DEFAULT_FINES

    def test_parses_matching_state(self):
        csv_data = "state_code,violation_code,base_fine\nDL,183,2500\nDL,185,12000\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["183"] == 2500
        assert fines["185"] == 12000
        assert fines["184"] == 1000

    def test_state_not_in_csv(self):
        csv_data = "state_code,violation_code,base_fine\nDL,183,2500\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("MH")
        assert fines["183"] == 2000

    def test_code_column_alias(self):
        csv_data = "state_code,code,base_fine\nKA,183,2200\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("KA")
        assert fines["183"] == 2200

    def test_fine_column_alias(self):
        csv_data = "state_code,violation_code,fine\nTN,183,1800\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("TN")
        assert fines["183"] == 1800

    def test_strips_hyphens_in_violation_code(self):
        csv_data = "state_code,violation_code,base_fine\nDL,MVA-183,3000\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["183"] == 3000

    def test_parses_184_violation_code(self):
        csv_data = "state_code,violation_code,base_fine\nDL,184,5000\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["184"] == 5000

    def test_parses_194D_violation_code(self):
        csv_data = "state_code,violation_code,base_fine\nDL,194D,2000\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["194D"] == 2000

    def test_parses_181_violation_code(self):
        csv_data = "state_code,violation_code,base_fine\nDL,181,8000\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["181"] == 8000

    def test_value_error_parsing_is_ignored(self):
        csv_data = "state_code,violation_code,base_fine\nDL,183,not_a_number\n"
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines["183"] == 2000  # unchanged default

    def test_general_exception_in_loading_is_logged(self):
        with patch.object(pathlib.Path, "exists", return_value=True), \
             patch("builtins.open", side_effect=PermissionError("denied")):
            fines = FinePredictionService._load_state_fine_overrides("DL")
        assert fines == DEFAULT_FINES


class TestPredictLiability:
    @staticmethod
    def _mock_fines(overrides=None):
        f = DEFAULT_FINES.copy()
        if overrides:
            f.update(overrides)
        return patch.object(FinePredictionService, "_load_state_fine_overrides", return_value=f)

    def test_low_risk_profile(self):
        payload = _payload(speeding_events=0, harsh_braking_events=0,
                           night_driving_minutes=10, state_code="DL")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_level == "low"
        assert result.risk_score < 3.0
        assert "Excellent" in result.recommendations[0]

    def test_medium_risk_slight_overspeed(self):
        payload = _payload(speeding_events=2, harsh_braking_events=0,
                           night_driving_minutes=20, state_code="DL")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_level == "medium"
        assert 3.0 <= result.risk_score < 7.0

    def test_high_risk_night_overspeed_braking(self):
        payload = _payload(speeding_events=8, harsh_braking_events=4,
                           night_driving_minutes=200, state_code="UP")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_level == "high"
        assert result.risk_score >= 7.0
        assert "Immediate warning" in result.recommendations[0]
        assert result.predicted_violations_count >= 8

    def test_regional_risk_amplifies_score(self):
        telemetry = dict(speeding_events=4, harsh_braking_events=2,
                         night_driving_minutes=90)
        payload_up = _payload(state_code="UP", **telemetry)
        payload_dl = _payload(state_code="DL", **telemetry)
        with self._mock_fines():
            r_up = FinePredictionService.predict_liability(payload_up)
            r_dl = FinePredictionService.predict_liability(payload_dl)
        assert r_up.risk_score >= r_dl.risk_score

    def test_no_events_lowest_risk(self):
        payload = _payload(speeding_events=0, harsh_braking_events=0,
                           night_driving_minutes=0, state_code="DL")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_level == "low"
        assert result.risk_score == 0.0
        assert result.predicted_violations_count == 0

    def test_night_liability_applied_when_high_risk(self):
        payload = _payload(speeding_events=6, harsh_braking_events=2,
                           night_driving_minutes=180, state_code="KA")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_score >= 6.0
        assert result.estimated_annual_liability > 0

    def test_calibrated_tn_baseline(self):
        payload = FinePredictionRequest(
            vehicle_number="TN-01-AB-1234",
            state_code="TN",
            telemetry=TelemetryDataPoint(
                speeding_events=5, harsh_braking_events=2,
                night_driving_minutes=180,
            )
        )
        result = FinePredictionService.predict_liability(payload)
        assert result.risk_score == 10.0
        assert result.risk_level == "high"
        assert result.predicted_violations_count == 6
        assert result.estimated_annual_liability == 30000

    def test_risk_score_clamped_at_max_10(self):
        payload = _payload(speeding_events=50, harsh_braking_events=20,
                           night_driving_minutes=600, state_code="UP")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_score <= 10.0
        assert result.risk_level == "high"

    def test_recommendations_mention_state(self):
        payload = _payload(speeding_events=2, harsh_braking_events=0,
                           night_driving_minutes=20, state_code="GJ")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_level == "medium"
        assert "GJ" in result.recommendations[-1]

    def test_missing_state_defaults_to_1x_factor(self):
        payload = _payload(speeding_events=4, harsh_braking_events=2,
                           night_driving_minutes=90, state_code="XX")
        with self._mock_fines():
            result = FinePredictionService.predict_liability(payload)
        assert result.risk_score > 0
        assert result.risk_level in ("medium", "high")
