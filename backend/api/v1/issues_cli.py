# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
SafeVixAI Issue Reporting CLI — Report issues from the command line.

Usage:
    python -m api.v1.issues_cli report --type bug --title "Button not working" --desc "The submit button does nothing"
    python -m api.v1.issues_cli report --type feature --title "Dark mode toggle"
    python -m api.v1.issues_cli list --status open
    python -m api.v1.issues_cli get <tracking-number>
    python -m api.v1.issues_cli stats
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

import httpx

API_BASE = 'http://localhost:8000/api/v1'


def _print_json(data: Any) -> None:
    pass


async def _cmd_report(args: argparse.Namespace) -> None:
    payload = {
        'issue_type': args.type,
        'category': args.category or 'other',
        'severity': args.severity or 'medium',
        'priority': args.priority or 'normal',
        'title': args.title,
        'description': args.desc,
        'steps_to_reproduce': args.steps,
        'environment': args.env,
        'labels': args.labels.split(',') if args.labels else None,
        'is_anonymous': args.anonymous,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f'{API_BASE}/issues', json=payload)
        if resp.status_code == 201:
            data = resp.json()
            if _detail := data.get('duplicate_of'):
                pass
            if _spam := data.get('is_spam'):
                pass
        else:
            sys.exit(1)


async def _cmd_list(args: argparse.Namespace) -> None:
    params = {'page': args.page, 'page_size': args.page_size}
    if args.status:
        params['status'] = args.status
    if args.type:
        params['issue_type'] = args.type

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f'{API_BASE}/issues', params=params)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', [])
            for _item in items:
                pass
            if not items:
                pass
        else:
            sys.exit(1)


async def _cmd_get(args: argparse.Namespace) -> None:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f'{API_BASE}/issues/tracking/{args.tracking}')
        if resp.status_code == 200:
            data = resp.json()
            if data.get('steps_to_reproduce'):
                pass
            if data.get('github_issue_url'):
                pass
        else:
            sys.exit(1)


async def _cmd_stats(args: argparse.Namespace) -> None:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f'{API_BASE}/issues/stats')
        if resp.status_code == 200:
            data = resp.json()
            if data.get('avg_resolution_hours'):
                pass
            for _t, _c in data.get('by_type', {}).items():
                pass
            for _s, _c in data.get('by_status', {}).items():
                pass
        else:
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description='SafeVixAI Issue Reporting CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    report_parser = subparsers.add_parser('report', help='Report a new issue')
    report_parser.add_argument('--type', required=True, choices=['bug', 'feature_request', 'feedback', 'performance', 'security', 'crash', 'ai_feedback'])
    report_parser.add_argument('--title', required=True)
    report_parser.add_argument('--desc', required=True)
    report_parser.add_argument('--category')
    report_parser.add_argument('--severity', choices=['critical', 'high', 'medium', 'low', 'cosmetic'])
    report_parser.add_argument('--priority', choices=['urgent', 'high', 'normal', 'low'])
    report_parser.add_argument('--steps')
    report_parser.add_argument('--env')
    report_parser.add_argument('--labels')
    report_parser.add_argument('--anonymous', action='store_true')

    list_parser = subparsers.add_parser('list', help='List issues')
    list_parser.add_argument('--status')
    list_parser.add_argument('--type')
    list_parser.add_argument('--page', type=int, default=1)
    list_parser.add_argument('--page-size', type=int, default=20)

    get_parser = subparsers.add_parser('get', help='Get issue by tracking number')
    get_parser.add_argument('tracking')

    subparsers.add_parser('stats', help='Show issue statistics')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'report':
        asyncio.run(_cmd_report(args))
    elif args.command == 'list':
        asyncio.run(_cmd_list(args))
    elif args.command == 'get':
        asyncio.run(_cmd_get(args))
    elif args.command == 'stats':
        asyncio.run(_cmd_stats(args))


if __name__ == '__main__':
    main()
