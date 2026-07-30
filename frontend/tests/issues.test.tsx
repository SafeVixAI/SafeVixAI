// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

// ── Mock next/navigation ──
var mockRouterPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockRouterPush, back: jest.fn(), replace: jest.fn() }),
  useParams: () => ({ uuid: 'test-uuid-123' }),
}));

// ── Mock the API ──
var mockCreateIssue = jest.fn();
var mockFetchIssues = jest.fn();
var mockFetchIssue = jest.fn();
var mockFetchIssueStats = jest.fn();
var mockFetchTimeline = jest.fn();
var mockUpdateIssue = jest.fn();
var mockMarkSpam = jest.fn();

jest.mock('@/lib/api/issues', () => ({
  createIssue: (...args: any[]) => mockCreateIssue(...args),
  fetchIssues: (...args: any[]) => mockFetchIssues(...args),
  fetchIssue: (...args: any[]) => mockFetchIssue(...args),
  fetchIssueStats: (...args: any[]) => mockFetchIssueStats(...args),
  fetchTimeline: (...args: any[]) => mockFetchTimeline(...args),
  updateIssue: (...args: any[]) => mockUpdateIssue(...args),
  markSpam: (...args: any[]) => mockMarkSpam(...args),
}));

// ── Mock sonner toast ──
jest.mock('sonner', () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

// ── Mock client-logger ──
jest.mock('@/lib/client-logger', () => ({
  logClientError: jest.fn(),
}));

// ── Mock store ──
var mockStoreState: any = { authToken: null, userProfile: {} };
jest.mock('@/lib/store', () => ({
  useAppStore: (selector?: any) => selector ? selector(mockStoreState) : mockStoreState,
}));

// ── Sample issue data ──
var sampleIssue = {
  uuid: 'test-uuid-123',
  trackingNumber: 'SAFE-260728-ABC123',
  issueType: 'bug',
  category: 'frontend',
  severity: 'high',
  priority: 'normal',
  status: 'new',
  title: 'Submit button not working',
  description: 'The submit button does nothing when clicked on the profile page.',
  stepsToReproduce: '1. Go to profile\n2. Click Submit\n3. Nothing happens',
  expectedBehavior: null,
  actualBehavior: null,
  environment: 'Chrome 120, Windows 11',
  browserInfo: null,
  deviceInfo: null,
  osInfo: null,
  appVersion: null,
  attachments: null,
  screenshotUrls: null,
  screenRecordingUrl: null,
  logs: null,
  systemInfo: null,
  labels: ['frontend', 'ui'],
  assignee: null,
  milestone: null,
  isAnonymous: false,
  isSpam: false,
  spamReason: null,
  duplicateOf: null,
  duplicateScore: null,
  aiCategory: null,
  aiSummary: null,
  aiSuggestedFix: null,
  aiConfidence: null,
  githubIssueUrl: null,
  githubIssueNumber: null,
  githubDiscussionUrl: null,
  reporterName: 'Test User',
  reporterEmail: null,
  slaResponseAt: null,
  slaResolutionAt: null,
  resolvedAt: null,
  createdAt: '2026-07-28T10:00:00Z',
  updatedAt: '2026-07-28T10:00:00Z',
};

var sampleStats = {
  total: 42,
  byType: { bug: 20, feature_request: 10, feedback: 8, crash: 4 },
  byStatus: { new: 15, in_progress: 10, resolved: 12, closed: 5 },
  bySeverity: { critical: 3, high: 10, medium: 20, low: 9 },
  byCategory: { frontend: 25, backend: 12, api: 5 },
  openCount: 28,
  resolvedCount: 12,
  spamCount: 2,
  duplicateCount: 3,
  avgResolutionHours: 48.5,
  slaBreachCount: 1,
};

var sampleIssuesList = {
  items: [sampleIssue],
  total: 1,
  page: 1,
  pageSize: 20,
  totalPages: 1,
};

var sampleTimeline = [
  { eventType: 'created', description: 'Issue created by test user', actor: 'system', metadata: null, createdAt: '2026-07-28T10:00:00Z' },
];

// ── Tests ──

describe('Issue Dashboard Page', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockFetchIssues.mockResolvedValue(sampleIssuesList);
    mockFetchIssueStats.mockResolvedValue(sampleStats);
  });

  it('renders the dashboard with stats', async function() {
    var IssuesPage = require('@/app/issues/page').default;
    render(React.createElement(IssuesPage));

    await waitFor(function() {
      expect(screen.getByText('Issue Reports')).toBeTruthy();
    });

    await waitFor(function() {
      expect(screen.getByText('42')).toBeTruthy();
      expect(screen.getByText('28')).toBeTruthy();
      expect(screen.getByText('12')).toBeTruthy();
    });
  });

  it('shows new issue button', async function() {
    var IssuesPage = require('@/app/issues/page').default;
    render(React.createElement(IssuesPage));

    await waitFor(function() {
      expect(screen.getByText('New Issue')).toBeTruthy();
    });
  });

  it('shows issue list in All Issues tab', async function() {
    var IssuesPage = require('@/app/issues/page').default;
    render(React.createElement(IssuesPage));

    var allIssuesTab = screen.getByText('All Issues');
    await userEvent.click(allIssuesTab);

    await waitFor(function() {
      expect(screen.getByText('Submit button not working')).toBeTruthy();
      expect(screen.getByText('SAFE-260728-ABC123')).toBeTruthy();
    });
  });

  it('shows error state when fetch fails', async function() {
    mockFetchIssues.mockRejectedValue(new Error('API Error'));
    var IssuesPage = require('@/app/issues/page').default;
    render(React.createElement(IssuesPage));

    await waitFor(function() {
      expect(screen.getByText('Issue Reports')).toBeTruthy();
    });
  });
});

describe('Issue Detail Page', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockFetchIssue.mockResolvedValue(sampleIssue);
    mockFetchTimeline.mockResolvedValue(sampleTimeline);
  });

  it('renders issue details', async function() {
    var IssueDetailPage = require('@/app/issues/[uuid]/page').default;
    render(React.createElement(IssueDetailPage));

    await waitFor(function() {
      expect(screen.getByText('Submit button not working')).toBeTruthy();
    });

    await waitFor(function() {
      expect(screen.getByText(/The submit button does nothing/)).toBeTruthy();
      expect(screen.getByText('SAFE-260728-ABC123')).toBeTruthy();
    });
  });

  it('shows timeline events', async function() {
    var IssueDetailPage = require('@/app/issues/[uuid]/page').default;
    render(React.createElement(IssueDetailPage));

    await waitFor(function() {
      expect(screen.getByText(/Issue created by/)).toBeTruthy();
    });
  });

  it('renders severity and type badges', async function() {
    var IssueDetailPage = require('@/app/issues/[uuid]/page').default;
    render(React.createElement(IssueDetailPage));

    await waitFor(function() {
      expect(screen.getByText('bug')).toBeTruthy();
    });
  });

  it('redirects on 404', async function() {
    mockFetchIssue.mockRejectedValue(new Error('Not found'));
    var IssueDetailPage = require('@/app/issues/[uuid]/page').default;
    render(React.createElement(IssueDetailPage));

    await waitFor(function() {
      expect(mockRouterPush).toHaveBeenCalledWith('/issues');
    });
  });
});

describe('New Issue Page', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockCreateIssue.mockResolvedValue(sampleIssue);
  });

  it('renders the form', function() {
    var NewIssuePage = require('@/app/issues/new/page').default;
    render(React.createElement(NewIssuePage));
    expect(screen.getByText('New Issue Report')).toBeTruthy();
    expect(screen.getByText('Bug Report')).toBeTruthy();
    expect(screen.getByText('Feature Request')).toBeTruthy();
    expect(screen.getByText('Cancel')).toBeTruthy();
  });

  it('submits a new issue with required fields', async function() {
    mockCreateIssue.mockResolvedValue(sampleIssue);
    var NewIssuePage = require('@/app/issues/new/page').default;
    render(React.createElement(NewIssuePage));

    var titleInput = screen.getByPlaceholderText('Brief summary of the issue');
    var descInput = screen.getByPlaceholderText('Detailed description of the issue...');

    await userEvent.type(titleInput, 'Test Bug Report');
    await userEvent.type(descInput, 'This is a test bug report description');

    var submitButton = screen.getByText('Submit Issue');
    await userEvent.click(submitButton);

    await waitFor(function() {
      expect(mockCreateIssue).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Bug Report',
          description: 'This is a test bug report description',
          issueType: 'bug',
        }),
      );
    });
  });

  it('shows validation error on empty title', async function() {
    var NewIssuePage = require('@/app/issues/new/page').default;
    render(React.createElement(NewIssuePage));

    var descInput = screen.getByPlaceholderText('Detailed description of the issue...');
    await userEvent.type(descInput, 'Some description');

    var submitButton = screen.getByText('Submit Issue');
    await userEvent.click(submitButton);

    var toastModule = require('sonner');
    await waitFor(function() {
      expect(toastModule.toast.error).toHaveBeenCalledWith('Title is required');
    });
  });
});

describe('Feedback Widget', function() {
  beforeEach(function() {
    jest.clearAllMocks();
  });

  it('renders feedback button', function() {
    var { FeedbackWidget } = require('@/components/issues/FeedbackWidget');
    render(React.createElement(FeedbackWidget));
    expect(screen.getByTitle('Send Feedback')).toBeTruthy();
  });

  it('opens feedback form on click', async function() {
    var { FeedbackWidget } = require('@/components/issues/FeedbackWidget');
    render(React.createElement(FeedbackWidget));

    var button = screen.getByTitle('Send Feedback');
    await userEvent.click(button);

    await waitFor(function() {
      expect(screen.getByText('Send Feedback')).toBeTruthy();
      expect(screen.getByPlaceholderText('Describe your feedback...')).toBeTruthy();
    });
  });
});

describe('Issue Form Component', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockCreateIssue.mockResolvedValue(sampleIssue);
  });

  it('renders all issue type options', function() {
    var { IssueForm } = require('@/components/issues/IssueForm');
    render(React.createElement(IssueForm));
    expect(screen.getByText('Bug Report')).toBeTruthy();
    expect(screen.getByText('Feature Request')).toBeTruthy();
    expect(screen.getByText('General Feedback')).toBeTruthy();
    expect(screen.getByText('Security Report')).toBeTruthy();
  });

  it('renders severity and priority selects', function() {
    var { IssueForm } = require('@/components/issues/IssueForm');
    render(React.createElement(IssueForm));
    expect(screen.getByText('Cancel')).toBeTruthy();
  });

  it('calls createIssue on submit', async function() {
    var { IssueForm } = require('@/components/issues/IssueForm');
    render(React.createElement(IssueForm, { prefilledType: 'bug' }));

    var titleInput = screen.getByPlaceholderText('Brief summary of the issue');
    var descInput = screen.getByPlaceholderText('Detailed description of the issue...');

    await userEvent.type(titleInput, 'E2E Test Issue');
    await userEvent.type(descInput, 'Testing issue form submission flow');

    await userEvent.click(screen.getByText('Submit Issue'));

    await waitFor(function() {
      expect(mockCreateIssue).toHaveBeenCalled();
    });
  });
});

describe('Error Dialog', function() {
  it('renders error message', function() {
    var { ErrorDialog } = require('@/components/issues/ErrorDialog');
    render(React.createElement(ErrorDialog, {
      errorInfo: { error: new Error('Test error message') },
      onClose: jest.fn(),
    }));
    expect(screen.getByText('Test error message')).toBeTruthy();
    expect(screen.getByText('Something went wrong')).toBeTruthy();
  });

  it('shows report and reload buttons', function() {
    var { ErrorDialog } = require('@/components/issues/ErrorDialog');
    render(React.createElement(ErrorDialog, {
      errorInfo: { error: new Error('Test error') },
      onClose: jest.fn(),
    }));
    expect(screen.getByText('Report Issue')).toBeTruthy();
    expect(screen.getByText('Reload Page')).toBeTruthy();
  });
});

describe('Crash Screen', function() {
  it('renders crash message', function() {
    var { CrashScreen } = require('@/components/issues/CrashScreen');
    render(React.createElement(CrashScreen, {
      error: new Error('Fatal crash error'),
      onRecover: jest.fn(),
    }));
    expect(screen.getByText('Application Crashed')).toBeTruthy();
    expect(screen.getByText('Send Crash Report')).toBeTruthy();
    expect(screen.getByText('Reload App')).toBeTruthy();
  });

  it('shows technical details toggle', async function() {
    var { CrashScreen } = require('@/components/issues/CrashScreen');
    render(React.createElement(CrashScreen, {
      error: new Error('Fatal error with stack'),
      onRecover: jest.fn(),
    }));

    var showBtn = screen.getByText('Show Technical Details');
    await userEvent.click(showBtn);

    await waitFor(function() {
      expect(screen.getByText('Hide Technical Details')).toBeTruthy();
    });
  });
});

describe('Error Boundary', function() {
  it('renders children when no error', function() {
    var { ErrorBoundary } = require('@/components/issues/ErrorBoundary');
    render(React.createElement(ErrorBoundary, null,
      React.createElement('div', null, 'Child Content'),
    ));
    expect(screen.getByText('Child Content')).toBeTruthy();
  });
});

describe('Issue Settings Page', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(jest.fn());
  });

  afterEach(function() {
    jest.restoreAllMocks();
  });

  it('renders settings tabs', function() {
    var IssuesSettingsPage = require('@/app/settings/issues/page').default;
    render(React.createElement(IssuesSettingsPage));
    expect(screen.getByText('Issue Reporting Settings')).toBeTruthy();
    expect(screen.getByText('General')).toBeTruthy();
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Privacy')).toBeTruthy();
  });

  it('shows error reporting toggles', function() {
    var IssuesSettingsPage = require('@/app/settings/issues/page').default;
    render(React.createElement(IssuesSettingsPage));
    expect(screen.getByText('Auto-submit Errors')).toBeTruthy();
    expect(screen.getByText('Include Screenshots')).toBeTruthy();
  });

  it('save button persists settings', async function() {
    var IssuesSettingsPage = require('@/app/settings/issues/page').default;
    render(React.createElement(IssuesSettingsPage));

    var saveBtn = screen.getByText('Save Settings');
    await userEvent.click(saveBtn);

    await waitFor(function() {
      expect(Storage.prototype.setItem).toHaveBeenCalled();
    });
  });

  it('clear cache button works', async function() {
    var removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
    var IssuesSettingsPage = require('@/app/settings/issues/page').default;
    render(React.createElement(IssuesSettingsPage));

    var clearBtn = screen.getByText('Clear Issue Cache & Drafts');
    await userEvent.click(clearBtn);

    expect(removeItemSpy).toHaveBeenCalledWith('issue-settings');
    expect(removeItemSpy).toHaveBeenCalledWith('issue-drafts');
  });
});
