# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from unittest.mock import patch, MagicMock
import json


try:
    from config import get_settings
    PORT = get_settings().service_port
except Exception:
    PORT = 8010

BASE_URL = f"http://localhost:{PORT}"



class TestConcurrentLoad:
    @patch("urllib.request.urlopen")
    def test_health_under_concurrent_load(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        def fetch_health():
            try:
                with urllib.request.urlopen(f"{BASE_URL}/health", timeout=5) as resp:
                    return resp.status
            except urllib.error.URLError:
                return None

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch_health) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]

        assert all(r == 200 for r in results), f"Not all health checks returned 200: {results}"

    @patch("urllib.request.urlopen")
    def test_openapi_schema_concurrent(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"openapi": "3.1.0"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        def fetch_openapi():
            try:
                with urllib.request.urlopen(f"{BASE_URL}/openapi.json", timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    return ("openapi" in data, resp.status)
            except urllib.error.URLError:
                return (False, None)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch_openapi) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]

        assert all(r[0] for r in results), "Not all responses contained valid OpenAPI schema"
        assert all(r[1] == 200 for r in results), f"Not all requests returned 200: {[r[1] for r in results]}"
