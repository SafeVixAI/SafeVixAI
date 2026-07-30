# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

from services.ai_issue_service import AIIssueService


@pytest.fixture
def ai_service() -> AIIssueService:
    return AIIssueService()


@pytest.mark.asyncio
async def test_categorize_ui_bug(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='Submit button not working',
        description='The CSS layout is broken and the button overlaps the footer.',
    )
    assert result['category'] == 'ui_bug'
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_categorize_api_error(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='API returning 500 errors',
        description='The /api/v1/chat endpoint keeps timing out.',
    )
    assert result['category'] == 'api_error'
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_categorize_auth(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='Cannot login',
        description='Getting 401 unauthorized on every request.',
    )
    assert result['category'] == 'auth'
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_categorize_performance(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='App is very slow',
        description='The dashboard takes 10 seconds to load. High memory usage.',
    )
    assert result['category'] == 'performance'
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_categorize_crash(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='App crashes on startup',
        description='Fatal exception when loading the map component.',
    )
    assert result['category'] == 'crash'
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_categorize_other(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='Color scheme suggestion',
        description='The app would look better with warmer colors.',
    )
    assert result['category'] == 'other'
    assert result['confidence'] < 0.5


@pytest.mark.asyncio
async def test_summarize_short(ai_service: AIIssueService) -> None:
    summary = await ai_service.summarize(
        title='Bug',
        description='The button is broken.',
        max_words=10,
    )
    assert len(summary) > 0
    assert len(summary.split()) <= 10


@pytest.mark.asyncio
async def test_summarize_long(ai_service: AIIssueService) -> None:
    description = 'The submit button on the profile page does not work when clicked. ' * 20
    summary = await ai_service.summarize(
        title='Button bug',
        description=description,
        max_words=30,
    )
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_suggest_fix_by_category(ai_service: AIIssueService) -> None:
    fix = await ai_service.suggest_fix(
        title='Broken layout',
        description='CSS is overlapping',
        category='ui_bug',
    )
    assert fix is not None
    assert 'cache' in fix.lower()


@pytest.mark.asyncio
async def test_suggest_fix_by_text(ai_service: AIIssueService) -> None:
    fix = await ai_service.suggest_fix(
        title='Login error 403',
        description='Getting forbidden error',
    )
    assert fix is not None


@pytest.mark.asyncio
async def test_suggest_fix_none(ai_service: AIIssueService) -> None:
    fix = await ai_service.suggest_fix(
        title='General question',
        description='How does this work?',
    )
    assert fix is None


@pytest.mark.asyncio
async def test_categorize_network(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='No connection',
        description='The app shows offline when I have internet.',
    )
    assert result['category'] == 'network'


@pytest.mark.asyncio
async def test_categorize_data_loss(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='Data missing after refresh',
        description='My profile data disappeared after page reload.',
    )
    assert result['category'] == 'data_loss'


@pytest.mark.asyncio
async def test_categorize_security(ai_service: AIIssueService) -> None:
    result = await ai_service.categorize(
        title='Potential XSS vulnerability',
        description='User input is not sanitized, possible injection.',
    )
    assert result['category'] == 'security'
