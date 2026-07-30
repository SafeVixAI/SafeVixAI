# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class IssueType(str, Enum):
    bug = 'bug'
    feature_request = 'feature_request'
    feedback = 'feedback'
    performance = 'performance'
    security = 'security'
    crash = 'crash'
    ai_feedback = 'ai_feedback'
    other = 'other'


class IssueCategory(str, Enum):
    frontend = 'frontend'
    backend = 'backend'
    api = 'api'
    database = 'database'
    chatbot = 'chatbot'
    mobile = 'mobile'
    documentation = 'documentation'
    infrastructure = 'infrastructure'
    other = 'other'


class IssueSeverity(str, Enum):
    critical = 'critical'
    high = 'high'
    medium = 'medium'
    low = 'low'
    cosmetic = 'cosmetic'


class IssuePriority(str, Enum):
    urgent = 'urgent'
    high = 'high'
    normal = 'normal'
    low = 'low'


class IssueStatus(str, Enum):
    new = 'new'
    triaged = 'triaged'
    acknowledged = 'acknowledged'
    in_progress = 'in_progress'
    needs_info = 'needs_info'
    resolved = 'resolved'
    closed = 'closed'
    wont_fix = 'wont_fix'
    duplicate = 'duplicate'
    spam = 'spam'


class CreateIssueRequest(BaseModel):
    issue_type: IssueType
    category: IssueCategory = IssueCategory.other
    severity: IssueSeverity = IssueSeverity.medium
    priority: IssuePriority = IssuePriority.normal
    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=10000)
    steps_to_reproduce: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    environment: str | None = None
    browser_info: dict[str, Any] | None = None
    device_info: dict[str, Any] | None = None
    os_info: str | None = None
    app_version: str | None = None
    screenshot_urls: list[str] | None = None
    screen_recording_url: str | None = None
    logs: dict[str, Any] | None = None
    system_info: dict[str, Any] | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    milestone: str | None = None
    is_anonymous: bool = False
    reporter_name: str | None = None
    reporter_email: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Title cannot be empty')
        return stripped

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Description cannot be empty')
        return stripped


class UpdateIssueRequest(BaseModel):
    status: IssueStatus | None = None
    severity: IssueSeverity | None = None
    priority: IssuePriority | None = None
    assignee: str | None = None
    milestone: str | None = None
    labels: list[str] | None = None
    title: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=10000)


class IssueListItem(BaseModel):
    uuid: str
    tracking_number: str
    issue_type: str
    category: str
    severity: str
    priority: str
    status: str
    title: str
    labels: list[str] | None = None
    is_anonymous: bool
    is_spam: bool
    duplicate_of: str | None = None
    ai_category: str | None = None
    assignee: str | None = None
    milestone: str | None = None
    github_issue_number: int | None = None
    reporter_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class IssueDetail(BaseModel):
    uuid: str
    tracking_number: str
    issue_type: str
    category: str
    severity: str
    priority: str
    status: str
    title: str
    description: str
    steps_to_reproduce: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    environment: str | None = None
    browser_info: dict[str, Any] | None = None
    device_info: dict[str, Any] | None = None
    os_info: str | None = None
    app_version: str | None = None
    attachments: list[dict[str, Any]] | None = None
    screenshot_urls: list[str] | None = None
    screen_recording_url: str | None = None
    logs: dict[str, Any] | None = None
    system_info: dict[str, Any] | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    milestone: str | None = None
    is_anonymous: bool
    is_spam: bool
    spam_reason: str | None = None
    duplicate_of: str | None = None
    duplicate_score: float | None = None
    ai_category: str | None = None
    ai_summary: str | None = None
    ai_suggested_fix: str | None = None
    ai_confidence: float | None = None
    github_issue_url: str | None = None
    github_issue_number: int | None = None
    github_discussion_url: str | None = None
    reporter_name: str | None = None
    reporter_email: str | None = None
    sla_response_at: datetime | None = None
    sla_resolution_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TimelineEvent(BaseModel):
    event_type: str
    description: str
    actor: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class IssueListResponse(BaseModel):
    items: list[IssueListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class IssueStatsResponse(BaseModel):
    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    by_severity: dict[str, int]
    by_category: dict[str, int]
    open_count: int
    resolved_count: int
    spam_count: int
    duplicate_count: int
    avg_resolution_hours: float | None = None
    sla_breach_count: int = 0


class IssueTemplate(BaseModel):
    issue_type: IssueType
    title_placeholder: str
    description_template: str
    fields: list[dict[str, Any]]


ISSUE_TEMPLATES: list[IssueTemplate] = [
    IssueTemplate(
        issue_type=IssueType.bug,
        title_placeholder='Bug: [Short description]',
        description_template='''## Description
[Describe the bug]

## Steps to Reproduce
1.

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- App Version:
- Browser:
- OS:''',
        fields=[
            {'name': 'steps_to_reproduce', 'label': 'Steps to Reproduce', 'type': 'textarea'},
            {'name': 'expected_behavior', 'label': 'Expected Behavior', 'type': 'textarea'},
            {'name': 'actual_behavior', 'label': 'Actual Behavior', 'type': 'textarea'},
            {'name': 'environment', 'label': 'Environment', 'type': 'text'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.feature_request,
        title_placeholder='Feature: [Feature name]',
        description_template='''## Problem
[What problem does this solve?]

## Proposed Solution
[Describe your idea]

## Alternatives
[Other solutions considered]''',
        fields=[
            {'name': 'expected_behavior', 'label': 'Proposed Solution', 'type': 'textarea'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.crash,
        title_placeholder='Crash: [Location/action]',
        description_template='''## What were you doing?
[Describe the action that caused the crash]

## Error Message
[Paste any error message shown]''',
        fields=[
            {'name': 'steps_to_reproduce', 'label': 'What were you doing?', 'type': 'textarea'},
            {'name': 'logs', 'label': 'Error Logs', 'type': 'textarea'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.security,
        title_placeholder='Security: [Vulnerability description]',
        description_template='''## Vulnerability
[Describe the security issue — be specific but don\'t include exploit code]

## Impact
[What could an attacker do?]''',
        fields=[
            {'name': 'steps_to_reproduce', 'label': 'Steps to Reproduce', 'type': 'textarea'},
            {'name': 'expected_behavior', 'label': 'Expected Behavior', 'type': 'textarea'},
            {'name': 'actual_behavior', 'label': 'Actual Behavior', 'type': 'textarea'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.performance,
        title_placeholder='Performance: [Slow/Resource issue]',
        description_template='''## Issue
[Describe the performance problem]

## Metrics
- Page load time:
- API response time:
- Memory usage:''',
        fields=[
            {'name': 'environment', 'label': 'Environment', 'type': 'text'},
            {'name': 'system_info', 'label': 'System Info', 'type': 'textarea'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.ai_feedback,
        title_placeholder='AI Feedback: [Topic]',
        description_template='''## Query
[What did you ask the AI?]

## Response
[What did the AI respond?]

## Issue
[Was it incorrect, misleading, or could it be improved?]''',
        fields=[
            {'name': 'expected_behavior', 'label': 'Expected Response', 'type': 'textarea'},
            {'name': 'actual_behavior', 'label': 'Actual Response', 'type': 'textarea'},
        ],
    ),
    IssueTemplate(
        issue_type=IssueType.feedback,
        title_placeholder='Feedback: [Subject]',
        description_template='''## Feedback
[Share your thoughts, suggestions, or general feedback]

## Impact
[How would this improve the product?]''',
        fields=[],
    ),
]
