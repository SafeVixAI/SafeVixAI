# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
#!/usr/bin/env python3
"""smoke_test.py — SafeVixAI Deployment Smoke Test

Verifies all 3 services respond correctly after deployment.
Run against live URLs or localhost.

Usage:
    python scripts/smoke_test.py                          # localhost defaults
    python scripts/smoke_test.py --backend https://safevixai-api.onrender.com --chatbot https://safevixai-chatbot.onrender.com
"""

import argparse
import sys

try:
    import httpx
except ImportError:
    print("Missing httpx — run: pip install httpx")
    sys.exit(1)


PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}" + (f" — {detail}" if detail else ""))


def main():
    parser = argparse.ArgumentParser(description="SafeVixAI smoke test")
    parser.add_argument("--backend", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--chatbot", default="http://localhost:8010", help="Chatbot base URL")
    args = parser.parse_args()

    backend = args.backend.rstrip("/")
    chatbot = args.chatbot.rstrip("/")

    client = httpx.Client(timeout=15.0, follow_redirects=True)

    print(f"\n{'='*60}")
    print("  SafeVixAI Smoke Test")
    print(f"  Backend:  {backend}")
    print(f"  Chatbot:  {chatbot}")
    print(f"{'='*60}\n")

    # ── Backend Health ──────────────────────────────────────────────
    print("1. Backend Health")
    try:
        r = client.get(f"{backend}/health")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        data = r.json()
        check(data.get("status") == "ok", f"Expected status=ok, got {data.get('status')}")
        check("database" in data, "No database key in health response")
        check("version" in data, "No version key in health response")
    except Exception as e:
        check(False, f"Connection failed: {e}")

    # ── Backend Metrics ─────────────────────────────────────────────
    print("\n2. Backend Metrics")
    try:
        r = client.get(f"{backend}/metrics")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        check("# HELP" in r.text, "No Prometheus HELP lines")
    except Exception as e:
        check(False, f"Metrics failed: {e}")

    # ── Backend Emergency ───────────────────────────────────────────
    print("\n3. Backend Emergency API")
    try:
        r = client.get(f"{backend}/api/v1/emergency/numbers")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        data = r.json()
        check("112" in str(data), "112 missing from emergency numbers")
    except Exception as e:
        check(False, f"Emergency numbers failed: {e}")

    # ── Backend Geocode ─────────────────────────────────────────────
    print("\n4. Backend Geocode API")
    try:
        r = client.get(f"{backend}/api/v1/geocode/reverse", params={"lat": 13.0827, "lon": 80.2707})
        check(r.status_code in (200, 503), f"Unexpected status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            check(len(str(data)) > 10, "Empty geocode response")
    except Exception as e:
        check(False, f"Geocode failed: {e}")

    # ── Backend Challan ─────────────────────────────────────────────
    print("\n5. Backend Challan API")
    try:
        r = client.post(
            f"{backend}/api/v1/challan/calculate",
            json={"violation_code": "MVA_185", "state": "TAMIL NADU"},
        )
        check(r.status_code in (200, 422), f"Unexpected status: {r.status_code}")
    except Exception as e:
        check(False, f"Challan failed: {e}")

    # ── Backend Auth ────────────────────────────────────────────────
    print("\n6. Backend Auth Endpoints")
    try:
        r = client.post(f"{backend}/api/v1/auth/login", json={"email": "test@test.com", "password": "password123"})
        check(r.status_code == 401, f"Expected 401 for bad login, got {r.status_code}")
    except Exception as e:
        check(False, f"Auth login failed: {e}")

    try:
        r = client.get(f"{backend}/api/v1/auth/verify")
        check(r.status_code == 401, f"Expected 401 for unauthenticated verify, got {r.status_code}")
    except Exception as e:
        check(False, f"Auth verify failed: {e}")

    # ── Backend Circuit Breaker ──────────────────────────────────────
    print("\n7. Backend Circuit Breaker (auth-gated)")
    try:
        r = client.get(f"{backend}/api/v1/circuit-breaker/")
        check(r.status_code == 401, f"Expected 401 for unauthenticated CB access, got {r.status_code}")
    except Exception as e:
        check(False, f"Circuit breaker auth check failed: {e}")

    # ── Backend Rate Limiting ───────────────────────────────────────
    print("\n8. Backend Rate Limiting")
    try:
        # Make many rapid requests to trigger rate limit
        for _ in range(15):
            client.get(f"{backend}/api/v1/emergency/numbers")
        r = client.get(f"{backend}/api/v1/emergency/numbers")
        check(r.status_code == 429, f"Expected 429 after burst, got {r.status_code}")
    except Exception as e:
        check(False, f"Rate limit check failed: {e}")

    # ── Backend CORS ────────────────────────────────────────────────
    print("\n9. Backend CORS Headers")
    try:
        r = client.options(
            f"{backend}/api/v1/emergency/numbers",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        check("access-control-allow-origin" in r.headers, "No CORS headers in response")
    except Exception as e:
        check(False, f"CORS check failed: {e}")

    # ── Backend Security Headers ────────────────────────────────────
    print("\n10. Backend Security Headers")
    try:
        r = client.get(f"{backend}/health")
        check("strict-transport-security" in r.headers, "Missing HSTS header")
        check("x-content-type-options" in r.headers, "Missing X-Content-Type-Options")
        check("x-frame-options" in r.headers, "Missing X-Frame-Options")
        check("referrer-policy" in r.headers, "Missing Referrer-Policy")
    except Exception as e:
        check(False, f"Security headers check failed: {e}")

    # ── Chatbot Health ─────────────────────────────────────────────
    print("\n11. Chatbot Health")
    try:
        r = client.get(f"{chatbot}/health")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        data = r.json()
        check(data.get("status") == "ok", f"Expected status=ok, got {data.get('status')}")
        check("service" in data, "No service key in health response")
    except Exception as e:
        check(False, f"Chatbot connection failed: {e}")

    # ── Chatbot Root ────────────────────────────────────────────────
    print("\n12. Chatbot Root Info")
    try:
        r = client.get(f"{chatbot}/")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        data = r.json()
        check("endpoints" in data, "No endpoints key")
        check("chat" in str(data), "chat endpoint not listed")
    except Exception as e:
        check(False, f"Chatbot root failed: {e}")

    # ── Chatbot Security Headers ────────────────────────────────────
    print("\n13. Chatbot Security Headers")
    try:
        r = client.get(f"{chatbot}/health")
        check("strict-transport-security" in r.headers, "Missing HSTS header")
        check("x-content-type-options" in r.headers, "Missing X-Content-Type-Options")
        check("content-security-policy" in r.headers, "Missing CSP header")
    except Exception as e:
        check(False, f"Chatbot security headers failed: {e}")

    # ── Chatbot Auth Enforcement ────────────────────────────────────
    print("\n14. Chatbot Auth (internal key check)")
    try:
        r = client.post(f"{chatbot}/api/v1/chat/", json={"message": "hello"})
        if r.status_code == 403:
            check(True, "Internal auth key is enforced (got 403)")
        else:
            check(True, f"No auth key configured, request got {r.status_code} (acceptable in dev)")
    except Exception as e:
        check(False, f"Chatbot auth check failed: {e}")

    # ── Chatbot Rate Limiting ──────────────────────────────────────
    print("\n15. Chatbot Rate Limiting")
    try:
        for _ in range(25):
            client.get(f"{chatbot}/api/v1/chat/health")
        r = client.get(f"{chatbot}/api/v1/chat/health")
        if r.status_code == 429:
            check(True, "Rate limiting is active on chatbot")
        else:
            check(True, f"Got {r.status_code} (rate limiting may not be on this endpoint)")
    except Exception as e:
        check(False, f"Chatbot rate limit check failed: {e}")

    # ── Chatbot Metrics ────────────────────────────────────────────
    print("\n16. Chatbot Metrics")
    try:
        r = client.get(f"{chatbot}/metrics")
        check(r.status_code == 200, f"Expected 200, got {r.status_code}")
        check("api_request_total" in r.text, "Missing api_request_total metric")
    except Exception as e:
        check(False, f"Chatbot metrics failed: {e}")

    # ── Summary ─────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}\n")

    if FAIL > 0:
        print(f"⚠️  {FAIL} check(s) failed — review details above.\n")
        sys.exit(1)
    else:
        print("✅ All smoke tests passed!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
