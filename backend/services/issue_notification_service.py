# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class IssueNotificationService:
    def __init__(
        self,
        *,
        webhook_urls: list[str] | None = None,
        slack_webhook_url: str | None = None,
        discord_webhook_url: str | None = None,
        email_config: dict[str, str] | None = None,
    ) -> None:
        self.webhook_urls = webhook_urls or []
        self.slack_webhook_url = slack_webhook_url
        self.discord_webhook_url = discord_webhook_url
        self.email_config = email_config or {}

    async def notify_issue_created(self, issue: dict[str, Any]) -> None:
        tasks = []
        if self.slack_webhook_url:
            tasks.append(self._send_slack(issue))
        if self.discord_webhook_url:
            tasks.append(self._send_discord(issue))
        for url in self.webhook_urls:
            tasks.append(self._send_webhook(url, issue))
        if self.email_config:
            tasks.append(self._send_email(issue))

        results = []
        for task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as exc:
                logger.error('Notification task failed: %s', exc)

        return results

    async def _send_slack(self, issue: dict[str, Any]) -> bool:
        blocks = [
            {
                'type': 'header',
                'text': {'type': 'plain_text', 'text': f'🚨 New Issue: {issue["title"][:80]}'},
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f'*Type:* {issue["issue_type"]}'},
                    {'type': 'mrkdwn', 'text': f'*Severity:* {issue["severity"]}'},
                    {'type': 'mrkdwn', 'text': f'*Status:* {issue["status"]}'},
                    {'type': 'mrkdwn', 'text': f'*Tracking:* `{issue["tracking_number"]}`'},
                ],
            },
            {
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': f'```{issue["description"][:500]}```'},
            },
        ]
        if issue.get('labels'):
            labels = ' '.join(f'`{l}`' for l in issue['labels'])
            blocks.append({'type': 'context', 'elements': [{'type': 'mrkdwn', 'text': f'Labels: {labels}'}]})

        payload = {
            'text': f'New {issue["issue_type"]}: {issue["title"]}',
            'blocks': blocks,
        }
        return await self._post_webhook(self.slack_webhook_url, payload)

    async def _send_discord(self, issue: dict[str, Any]) -> bool:
        embed = {
            'title': issue['title'][:256],
            'description': issue['description'][:2048],
            'color': self._severity_color(issue.get('severity', 'medium')),
            'fields': [
                {'name': 'Type', 'value': issue.get('issue_type', 'unknown'), 'inline': True},
                {'name': 'Severity', 'value': issue.get('severity', 'medium'), 'inline': True},
                {'name': 'Status', 'value': issue.get('status', 'new'), 'inline': True},
                {'name': 'Tracking', 'value': issue.get('tracking_number', '-'), 'inline': True},
            ],
            'footer': {'text': 'SafeVixAI Issue Reporter'},
            'timestamp': issue.get('created_at', ''),
        }
        if issue.get('labels'):
            embed['fields'].append({
                'name': 'Labels',
                'value': ', '.join(issue['labels']),
                'inline': False,
            })
        payload = {'embeds': [embed]}
        return await self._post_webhook(self.discord_webhook_url, payload)

    async def _send_webhook(self, url: str, issue: dict[str, Any]) -> bool:
        return await self._post_webhook(url, {
            'event': 'issue.created',
            'issue': issue,
            'timestamp': issue.get('created_at', ''),
        })

    async def _send_email(self, issue: dict[str, Any]) -> bool:
        logger.info('Email notification configured — would send to %s', self.email_config.get('to'))
        return True

    async def _post_webhook(self, url: str | None, payload: dict[str, Any]) -> bool:
        if not url:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code < 300:
                    logger.debug('Webhook delivered to %s: %d', url[:50], resp.status_code)
                    return True
                logger.warning('Webhook failed %s: %d %s', url[:50], resp.status_code, resp.text[:200])
                return False
        except httpx.RequestError as exc:
            logger.warning('Webhook request error %s: %s', url[:50], exc)
            return False

    def _severity_color(self, severity: str) -> int:
        colors = {'critical': 0xDC143C, 'high': 0xFF4500, 'medium': 0xFFA500, 'low': 0x3CB371, 'cosmetic': 0x87CEEB}
        return colors.get(severity, 0x808080)
