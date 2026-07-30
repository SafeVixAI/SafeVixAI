# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

import pytest

from services.github_integration import GitHubIntegration


@pytest.fixture
def github() -> GitHubIntegration:
    return GitHubIntegration(token='test-token', repo_owner='test', repo_name='test-repo')


@pytest.mark.asyncio
async def test_disabled_no_token() -> None:
    gh = GitHubIntegration(token=None)
    result = await gh.create_issue(title='Test', body='Body')
    assert result is None


@pytest.mark.asyncio
async def test_create_issue_success(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        'number': 42,
        'html_url': 'https://github.com/test/test-repo/issues/42',
        'title': 'Test Issue',
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.create_issue(title='Test Issue', body='Body', labels=['bug'])

    assert result is not None
    assert result['number'] == 42


@pytest.mark.asyncio
async def test_create_issue_failure(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 422

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.create_issue(title='Test', body='Body')

    assert result is None


@pytest.mark.asyncio
async def test_create_issue_timeout(github: GitHubIntegration) -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.side_effect = httpx.TimeoutException('Timeout')

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.create_issue(title='Test', body='Body')

    assert result is None


@pytest.mark.asyncio
async def test_update_issue_success(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'number': 42, 'state': 'closed'}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.patch.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.update_issue(issue_number=42, state='closed')

    assert result is not None


@pytest.mark.asyncio
async def test_add_comment_success(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 123, 'body': 'Thanks!'}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.add_comment(issue_number=42, body='Thanks!')

    assert result is not None


@pytest.mark.asyncio
async def test_close_issue(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'number': 42, 'state': 'closed'}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.patch.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await github.close_issue(issue_number=42)

    assert result is not None


@pytest.mark.asyncio
async def test_get_labels(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {'name': 'bug', 'color': 'd73a4a'},
        {'name': 'enhancement', 'color': 'a2eeef'},
    ]

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        labels = await github.get_labels()

    assert len(labels) == 2


@pytest.mark.asyncio
async def test_get_labels_empty_on_failure(github: GitHubIntegration) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        labels = await github.get_labels()

    assert labels == []


def test_label_color() -> None:
    assert GitHubIntegration._label_color('bug') == 'd73a4a'
    assert GitHubIntegration._label_color('feature') == 'a2eeef'
    assert GitHubIntegration._label_color('security') == 'cf0a2c'
    assert GitHubIntegration._label_color('unknown-category') == 'ededed'


def test_verify_webhook_no_secret() -> None:
    gh = GitHubIntegration(token='test', webhook_secret=None)
    assert gh.verify_webhook(b'test', 'signature') is True


def test_verify_webhook_valid() -> None:
    import hmac
    gh = GitHubIntegration(token='test', webhook_secret='mysecret')
    payload = b'{"test": true}'
    expected = hmac.new(b'mysecret', payload, 'sha256').hexdigest()
    assert gh.verify_webhook(payload, f'sha256={expected}')
