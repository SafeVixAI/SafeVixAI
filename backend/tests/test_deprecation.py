from datetime import datetime, timedelta
from unittest.mock import patch

from api.deprecation import (
    DEPRECATED_ENDPOINTS,
    get_deprecation_headers,
    mark_deprecated,
)


class TestDeprecation:
    def setup_method(self):
        DEPRECATED_ENDPOINTS.clear()

    def test_mark_deprecated_adds_endpoint(self):
        mark_deprecated('/api/v1/old', sunset_in_days=30)
        assert '/api/v1/old' in DEPRECATED_ENDPOINTS
        assert DEPRECATED_ENDPOINTS['/api/v1/old'] > datetime(2020, 1, 1)

    def test_get_deprecation_headers_returns_empty_for_unknown(self):
        assert get_deprecation_headers('/api/v1/unknown') == {}

    def test_get_deprecation_headers_returns_sunset_for_deprecated(self):
        mark_deprecated('/api/v1/old', sunset_in_days=90)
        headers = get_deprecation_headers('/api/v1/old')
        assert headers['Deprecation'] == 'true; sunset=' + DEPRECATED_ENDPOINTS['/api/v1/old'].isoformat()
        assert headers['Sunset'] == DEPRECATED_ENDPOINTS['/api/v1/old'].isoformat()
