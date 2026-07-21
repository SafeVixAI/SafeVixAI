# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from middleware.allowed_hosts import AllowedHostsMiddleware, setup_allowed_hosts
from middleware.compression import setup_compression
from middleware.csrf import CSRFMiddleware, setup_csrf
from middleware.query_profiler import QueryProfilerMiddleware, setup_query_profiler
from middleware.request_id import RequestIdMiddleware, setup_request_id
from middleware.security_headers import SecurityHeadersMiddleware, setup_security_headers

__all__ = [
    "AllowedHostsMiddleware", "setup_allowed_hosts",
    "setup_compression",
    "CSRFMiddleware", "setup_csrf",
    "QueryProfilerMiddleware", "setup_query_profiler",
    "RequestIdMiddleware", "setup_request_id",
    "SecurityHeadersMiddleware", "setup_security_headers",
]
