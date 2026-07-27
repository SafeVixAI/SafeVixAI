# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestValidateImageEndpoint:
    def test_router_prefix(self) -> None:
        from api.ai import router
        assert router.prefix == "/api/v1/ai"

    def test_max_image_bytes_constant(self) -> None:
        from api.ai import MAX_IMAGE_BYTES
        assert MAX_IMAGE_BYTES == 5 * 1024 * 1024

    def test_validate_image_success(self, client: TestClient) -> None:
        mock_result = {"anomaly_detected": True, "confidence": 0.85, "boxes": [], "success": True}
        with patch("api.ai.PotholeValidator.validate_image", return_value=mock_result):
            response = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["anomaly_detected"] is True

    def test_validate_image_model_not_found(self, client: TestClient) -> None:
        mock_result = {"anomaly_detected": False, "confidence": 0.0, "success": False, "error": "Model not found"}
        with patch("api.ai.PotholeValidator.validate_image", return_value=mock_result):
            response = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("test.jpg", b"img", "image/jpeg")},
            )
            assert response.status_code == 200
            assert response.json()["success"] is False

    def test_validate_image_exception_returns_500(self, client: TestClient) -> None:
        with patch("api.ai.PotholeValidator.validate_image", side_effect=RuntimeError("model crash")):
            response = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("test.jpg", b"data", "image/jpeg")},
            )
            assert response.status_code == 500

    def test_validate_image_non_image_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ai/validate-image",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400
        assert "Only image files" in response.text

    def test_validate_image_empty_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ai/validate-image",
            files={"file": ("test.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400
        assert "Empty file" in response.text

    def test_validate_image_too_large_returns_413(self, client: TestClient) -> None:
        large_data = b"x" * (6 * 1024 * 1024)
        response = client.post(
            "/api/v1/ai/validate-image",
            files={"file": ("test.jpg", large_data, "image/jpeg")},
        )
        assert response.status_code == 413
        assert "too large" in response.text.lower()
