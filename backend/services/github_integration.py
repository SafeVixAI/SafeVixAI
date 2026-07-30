# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import hmac
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GitHubIntegration:
    def __init__(
        self,
        *,
        token: str | None = None,
        repo_owner: str = 'safevixai',
        repo_name: str = 'SafeVixAI',
        webhook_secret: str | None = None,
    ) -> None:
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.webhook_secret = webhook_secret
        self._enabled = bool(token)

    @property
    def api_base(self) -> str:
        return f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}'

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SafeVixAI/1.0',
        }

    async def create_issue(
        self,
        *,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignee: str | None = None,
        milestone: int | None = None,
    ) -> dict[str, Any] | None:
        if not self._enabled:
            logger.info('GitHub integration disabled — skipping issue creation')
            return None

        payload: dict[str, Any] = {'title': title, 'body': body}
        if labels:
            payload['labels'] = labels
        if assignee:
            payload['assignees'] = [assignee]
        if milestone:
            payload['milestone'] = milestone

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    f'{self.api_base}/issues',
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code in (201, 200):
                    data = resp.json()
                    logger.info('GitHub issue created: #%d — %s', data['number'], data['html_url'])
                    return data
                logger.error('GitHub issue creation failed: %d %s', resp.status_code, resp.text[:500])
                return None
            except httpx.TimeoutException:
                logger.error('GitHub API timeout creating issue')
                return None
            except httpx.RequestError as exc:
                logger.error('GitHub API request error: %s', exc)
                return None

    async def update_issue(
        self,
        *,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: list[str] | None = None,
        assignee: str | None = None,
        milestone: int | None = None,
    ) -> dict[str, Any] | None:
        if not self._enabled:
            return None

        payload: dict[str, Any] = {}
        if title:
            payload['title'] = title
        if body:
            payload['body'] = body
        if state:
            payload['state'] = state
        if labels is not None:
            payload['labels'] = labels
        if assignee is not None:
            payload['assignees'] = [assignee] if assignee else []
        if milestone is not None:
            payload['milestone'] = milestone

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.patch(
                    f'{self.api_base}/issues/{issue_number}',
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code in (200,):
                    return resp.json()
                logger.error('GitHub issue update failed: %d %s', resp.status_code, resp.text[:500])
                return None
            except httpx.TimeoutException:
                logger.error('GitHub API timeout updating issue #%d', issue_number)
                return None
            except httpx.RequestError as exc:
                logger.error('GitHub API request error: %s', exc)
                return None

    async def add_comment(self, *, issue_number: int, body: str) -> dict[str, Any] | None:
        if not self._enabled:
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    f'{self.api_base}/issues/{issue_number}/comments',
                    headers=self._headers(),
                    json={'body': body},
                )
                if resp.status_code in (201, 200):
                    return resp.json()
                logger.error('GitHub comment failed: %d %s', resp.status_code, resp.text[:500])
                return None
            except httpx.RequestError as exc:
                logger.error('GitHub API request error: %s', exc)
                return None

    async def create_discussion(
        self,
        *,
        title: str,
        body: str,
        category: str = 'Ideas',
    ) -> dict[str, Any] | None:
        if not self._enabled:
            return None

        query = '''
        mutation($repoId: ID!, $title: String!, $body: String!, $categoryId: ID!) {
            createDiscussion(input: {
                repositoryId: $repoId,
                title: $title,
                body: $body,
                categoryId: $categoryId
            }) {
                discussion { id url }
            }
        }
        '''

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                repo_resp = await client.get(
                    f'{self.api_base}',
                    headers=self._headers(),
                )
                if repo_resp.status_code != 200:
                    logger.error('Failed to fetch repo info: %d', repo_resp.status_code)
                    return None
                repo_data = repo_resp.json()
                repo_node_id = repo_data.get('node_id')

                cat_resp = await client.get(
                    f'{self.api_base}/discussions/categories',
                    headers=self._headers(),
                )
                if cat_resp.status_code != 200:
                    logger.error('Failed to fetch discussion categories')
                    return None
                cats = cat_resp.json()
                category_id = None
                for cat in cats:
                    if cat.get('name', '').lower() == category.lower():
                        category_id = cat.get('id')
                        break
                if not category_id and cats:
                    category_id = cats[0].get('id')

                if not repo_node_id or not category_id:
                    logger.error('Missing repo node ID or category ID for discussion')
                    return None

                graphql_resp = await client.post(
                    'https://api.github.com/graphql',
                    headers={
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'query': query,
                        'variables': {
                            'repoId': repo_node_id,
                            'title': title,
                            'body': body,
                            'categoryId': category_id,
                        },
                    },
                )
                if graphql_resp.status_code == 200:
                    data = graphql_resp.json()
                    discussion = data.get('data', {}).get('createDiscussion', {}).get('discussion')
                    if discussion:
                        logger.info('GitHub discussion created: %s', discussion['url'])
                        return discussion
                    logger.error('GraphQL mutation returned no discussion: %s', data)
                    return None
                logger.error('GraphQL request failed: %d %s', graphql_resp.status_code, graphql_resp.text[:500])
                return None
            except httpx.RequestError as exc:
                logger.error('GitHub GraphQL request error: %s', exc)
                return None

    async def get_labels(self) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    f'{self.api_base}/labels',
                    headers=self._headers(),
                )
                if resp.status_code == 200:
                    return resp.json()
                return []
            except httpx.RequestError:
                return []

    async def ensure_labels(self, labels: list[str]) -> None:
        if not self._enabled:
            return
        existing = await self.get_labels()
        existing_names = {lbl['name'] for lbl in existing}

        async with httpx.AsyncClient(timeout=15.0) as client:
            for label in labels:
                if label not in existing_names:
                    color = self._label_color(label)
                    try:
                        await client.post(
                            f'{self.api_base}/labels',
                            headers=self._headers(),
                            json={'name': label, 'color': color},
                        )
                    except httpx.RequestError as exc:
                        logger.warning('Failed to create label %s: %s', label, exc)

    async def close_issue(self, *, issue_number: int) -> dict[str, Any] | None:
        return await self.update_issue(issue_number=issue_number, state='closed')

    async def reopen_issue(self, *, issue_number: int) -> dict[str, Any] | None:
        return await self.update_issue(issue_number=issue_number, state='open')

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return True
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            'sha256',
        ).hexdigest()
        return hmac.compare_digest(f'sha256={expected}', signature)

    @staticmethod
    def _label_color(name: str) -> str:
        palette = {
            'bug': 'd73a4a',
            'feature': 'a2eeef',
            'enhancement': 'a2eeef',
            'security': 'cf0a2c',
            'performance': '0e8a16',
            'crash': 'b60205',
            'feedback': 'd4c5f9',
            'question': 'd876e3',
            'documentation': '0075ca',
            'duplicate': 'cfd3d7',
            'wontfix': 'ffffff',
            'needs-info': 'f9d0c4',
            'spam': '000000',
        }
        return palette.get(name.lower(), 'ededed')
