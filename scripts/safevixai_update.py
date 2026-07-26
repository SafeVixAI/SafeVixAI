#!/usr/bin/env python3
"""SafeVixAI Update Manager — CLI for enterprise update operations.

Usage:
  python scripts/safevixai_update.py check [--channel stable] [--json]
  python scripts/safevixai_update.py download [version] [--channel stable]
  python scripts/safevixai_update.py install [version] [--channel stable]
  python scripts/safevixai_update.py rollback [version]
  python scripts/safevixai_update.py history [--limit 20]
  python scripts/safevixai_update.py channels [--json]
  python scripts/safevixai_update.py version [--json]
  python scripts/safevixai_update.py sync
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import httpx

BACKEND_URL = os.getenv("SVIX_BACKEND_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("SVIX_AUTH_TOKEN", "")


def _headers() -> dict:
    h = {"Accept": "application/json", "User-Agent": "SafeVixAI-CLI/1.0"}
    if AUTH_TOKEN:
        h["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return h


def _get(path: str, params: dict | None = None) -> dict | list:
    url = f"{BACKEND_URL}/api/v1/updates{path}"
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, data: dict | None = None) -> dict | list:
    url = f"{BACKEND_URL}/api/v1/updates{path}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_headers(), json=data)
        resp.raise_for_status()
        return resp.json()


def cmd_version(json_output: bool) -> None:
    result = _get("/version")
    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return
    print(f"SafeVixAI Update Manager")
    print(f"Current version: v{result['current_version']}")
    if result.get("update_available"):
        print(f"Update available: v{result['latest_version']} (channel: {result['channel']})")
    else:
        print("Status: Up to date")
    print(f"Channel: {result['channel']}")
    print(f"Last checked: {result.get('last_checked_at', 'Never')}")


def cmd_check(channel: str, json_output: bool) -> None:
    result = _get("/check", {"channel": channel})
    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return
    if result["update_available"]:
        print(f"Update available: v{result['latest_version']}")
        print(f"  Current: v{result['current_version']}")
        print(f"  Channel: {result['channel']}")
        if result.get("is_mandatory"):
            print("  MANDATORY UPDATE")
        if result.get("is_security"):
            print("  Security release")
    else:
        print(f"Up to date (v{result['current_version']})")


def cmd_download(version: str | None, channel: str) -> None:
    if not version:
        check = _get("/check", {"channel": channel})
        if not check.get("update_available"):
            print("No update available")
            return
        version = check["latest_version"]
    print(f"Downloading v{version}...")
    result = _post(f"/download/{version}")
    print(f"{result['message']}")


def cmd_install(version: str | None, channel: str) -> None:
    if not version:
        check = _get("/check", {"channel": channel})
        if not check.get("update_available"):
            print("No update available")
            return
        version = check["latest_version"]
    print(f"Installing v{version}...")
    result = _post(f"/install/{version}")
    print(f"{result['message']}")


def cmd_rollback(version: str | None) -> None:
    params = f"?version={version}" if version else ""
    print("Rolling back...")
    result = _post(f"/rollback{params}")
    print(f"{result['message']}")


def cmd_history(limit: int, json_output: bool) -> None:
    result = _get("/history", {"limit": limit, "offset": 0})
    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return
    print(f"Update History (last {limit}):")
    for inst in result.get("installations", []):
        ts = inst.get("completed_at") or inst.get("created_at", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            pass
        print(f"  [{inst['status']}] v{inst['release_version']} -> {ts}")
    print(f"Total: {result.get('total', 0)}")


def cmd_channels(json_output: bool) -> None:
    result = _get("/channels")
    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return
    print("Available channels:")
    for ch in result:
        marker = " *" if ch["channel"] == "stable" else ""
        print(f"  {ch['display_name']}{marker} (v{ch['latest_version']}, {ch['release_count']} releases)")


def cmd_sync() -> None:
    print("Syncing releases from GitHub...")
    result = _post("/sync")
    print(f"{result['message']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SafeVixAI Update Manager")
    parser.add_argument("command", nargs="?", default="check",
                        choices=["check", "download", "install", "rollback", "history", "channels", "version", "sync"])
    parser.add_argument("argument", nargs="?", default="", help="Version string or limit number")
    parser.add_argument("--channel", default="stable", help="Release channel (stable/beta/nightly/pre-release)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--limit", type=int, default=20, help="History limit")

    args = parser.parse_args()

    command_map = {
        "version": lambda: cmd_version(args.json),
        "check": lambda: cmd_check(args.channel, args.json),
        "download": lambda: cmd_download(args.argument or None, args.channel),
        "install": lambda: cmd_install(args.argument or None, args.channel),
        "rollback": lambda: cmd_rollback(args.argument or None),
        "history": lambda: cmd_history(args.limit if not args.argument else int(args.argument), args.json),
        "channels": lambda: cmd_channels(args.json),
        "sync": cmd_sync,
    }

    handler = command_map.get(args.command)
    if handler:
        try:
            handler()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error: {exc.response.status_code} - {exc.response.text}", file=sys.stderr)
            sys.exit(1)
        except httpx.RequestError as exc:
            print(f"Request failed: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
