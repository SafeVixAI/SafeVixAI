# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.pothole_validator import PotholeValidator


class TestPotholeValidator:
    def teardown_method(self) -> None:
        PotholeValidator._model = None

    def test_get_model_file_not_found(self) -> None:
        with patch("os.path.exists", return_value=False):
            with patch("services.pothole_validator.YOLO"):
                with pytest.raises(FileNotFoundError):
                    PotholeValidator.get_model()

    def test_get_model_loads_correctly(self) -> None:
        mock_model = MagicMock()
        with patch("os.path.exists", return_value=True):
            with patch("services.pothole_validator.YOLO", return_value=mock_model):
                model = PotholeValidator.get_model()
                assert model is mock_model

    def test_get_model_uses_cache(self) -> None:
        mock_model = MagicMock()
        PotholeValidator._model = mock_model
        model = PotholeValidator.get_model()
        assert model is mock_model

    def test_validate_image_no_model(self) -> None:
        PotholeValidator._model = None
        with patch("os.path.exists", return_value=False):
            result = PotholeValidator.validate_image(b"fake-image")
            assert result["success"] is False
            assert "error" in result

    def test_validate_image_anomaly_detected(self) -> None:
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_box = MagicMock()
        mock_box.conf = [0.85]
        mock_box.cls = [0]
        mock_box.xyxy = MagicMock()
        mock_box.xyxy.__getitem__.return_value = MagicMock()
        mock_box.xyxy.__getitem__.return_value.tolist.return_value = [10, 20, 100, 200]
        mock_result.boxes = [mock_box]
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "pothole"}

        with patch.object(PotholeValidator, "get_model", return_value=mock_model):
            with patch("PIL.Image.open"):
                result = PotholeValidator.validate_image(b"fake-image-bytes")
                assert result["anomaly_detected"] is True
                assert result["confidence"] == 0.85
                assert len(result["boxes"]) == 1
                assert result["success"] is True

    def test_validate_image_low_confidence_skipped(self) -> None:
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_box = MagicMock()
        mock_box.conf = [0.10]
        mock_box.cls = [0]
        mock_box.xyxy = MagicMock()
        mock_box.xyxy.__getitem__.return_value = MagicMock()
        mock_box.xyxy.__getitem__.return_value.tolist.return_value = [10, 20, 100, 200]
        mock_result.boxes = [mock_box]
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "pothole"}

        with patch.object(PotholeValidator, "get_model", return_value=mock_model):
            with patch("PIL.Image.open"):
                result = PotholeValidator.validate_image(b"fake-image-bytes")
                assert result["anomaly_detected"] is False
                assert result["confidence"] == 0.0
                assert len(result["boxes"]) == 0

    def test_validate_image_multiple_detections_max_confidence(self) -> None:
        mock_model = MagicMock()
        mock_result = MagicMock()
        box1 = MagicMock()
        box1.conf = [0.50]
        box1.cls = [0]
        box1.xyxy = MagicMock()
        box1.xyxy.__getitem__.return_value = MagicMock()
        box1.xyxy.__getitem__.return_value.tolist.return_value = [0, 0, 10, 10]
        box2 = MagicMock()
        box2.conf = [0.90]
        box2.cls = [1]
        box2.xyxy = MagicMock()
        box2.xyxy.__getitem__.return_value = MagicMock()
        box2.xyxy.__getitem__.return_value.tolist.return_value = [5, 5, 20, 20]
        mock_result.boxes = [box1, box2]
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "pothole", 1: "crack"}

        with patch.object(PotholeValidator, "get_model", return_value=mock_model):
            with patch("PIL.Image.open"):
                result = PotholeValidator.validate_image(b"fake-image-bytes")
                assert result["anomaly_detected"] is True
                assert result["confidence"] == 0.90
                assert len(result["boxes"]) == 2

    def test_validate_image_yolo_throws_exception(self) -> None:
        with patch.object(PotholeValidator, "get_model", side_effect=FileNotFoundError("model missing")):
            result = PotholeValidator.validate_image(b"fake")
            assert result["success"] is False
            assert "error" in result

    def test_validate_image_generic_exception(self) -> None:
        mock_model = MagicMock()
        mock_model.side_effect = RuntimeError("OOM")
        with patch.object(PotholeValidator, "get_model", return_value=mock_model):
            with patch("PIL.Image.open", side_effect=RuntimeError("OOM")):
                result = PotholeValidator.validate_image(b"data")
                assert result["success"] is False

    def test_get_model_first_valid_path(self) -> None:
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = [True, False, False, False]
            with patch("services.pothole_validator.YOLO") as mock_yolo:
                mock_yolo.return_value = MagicMock()
                model = PotholeValidator.get_model()
                assert model is not None
