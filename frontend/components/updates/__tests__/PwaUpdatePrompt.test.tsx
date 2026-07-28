// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PwaUpdatePrompt from '@/components/updates/PwaUpdatePrompt';

var mockApplyUpdate = jest.fn();
var mockDismissUpdate = jest.fn();

jest.mock('@/hooks/useServiceWorkerUpdate', function () {
  return {
    useServiceWorkerUpdate: jest.fn(),
  };
});

var mockUseServiceWorkerUpdate = jest.fn();

beforeEach(function () {
  jest.clearAllMocks();
  jest.isolateModules(function () {
    var mod = require('@/hooks/useServiceWorkerUpdate');
    mockUseServiceWorkerUpdate = mod.useServiceWorkerUpdate;
  });
});

describe('PwaUpdatePrompt', function () {
  it('renders when update is available', function () {
    mockUseServiceWorkerUpdate.mockReturnValue({
      updateAvailable: true,
      applyUpdate: mockApplyUpdate,
      dismissUpdate: mockDismissUpdate,
      waitingSw: {} as ServiceWorker,
    });
    render(React.createElement(PwaUpdatePrompt));
    expect(screen.getByText(/New version available/)).toBeInTheDocument();
  });

  it('does not render when no update available', function () {
    mockUseServiceWorkerUpdate.mockReturnValue({
      updateAvailable: false,
      applyUpdate: mockApplyUpdate,
      dismissUpdate: mockDismissUpdate,
      waitingSw: null,
    });
    var { container } = render(React.createElement(PwaUpdatePrompt));
    expect(container.innerHTML).toBe('');
  });

  it('calls applyUpdate on Update button click', function () {
    mockUseServiceWorkerUpdate.mockReturnValue({
      updateAvailable: true,
      applyUpdate: mockApplyUpdate,
      dismissUpdate: mockDismissUpdate,
      waitingSw: {} as ServiceWorker,
    });
    render(React.createElement(PwaUpdatePrompt));
    fireEvent.click(screen.getByText('Update'));
    expect(mockApplyUpdate).toHaveBeenCalled();
  });

  it('calls dismissUpdate on Dismiss button click', function () {
    mockUseServiceWorkerUpdate.mockReturnValue({
      updateAvailable: true,
      applyUpdate: mockApplyUpdate,
      dismissUpdate: mockDismissUpdate,
      waitingSw: {} as ServiceWorker,
    });
    render(React.createElement(PwaUpdatePrompt));
    fireEvent.click(screen.getByLabelText('Dismiss'));
    expect(mockDismissUpdate).toHaveBeenCalled();
  });

  it('has accessible aria attributes', function () {
    mockUseServiceWorkerUpdate.mockReturnValue({
      updateAvailable: true,
      applyUpdate: mockApplyUpdate,
      dismissUpdate: mockDismissUpdate,
      waitingSw: {} as ServiceWorker,
    });
    render(React.createElement(PwaUpdatePrompt));
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
