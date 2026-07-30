// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockSubmitReport = jest.fn();
const mockEnqueueRoadReport = jest.fn();
const mockTrackReportSubmitted = jest.fn();

jest.mock('../../lib/api', () => ({
  submitReport: (...args: unknown[]) => mockSubmitReport(...args),
}));

jest.mock('../../lib/offline-sos-queue', () => ({
  enqueueRoadReport: (...args: unknown[]) => mockEnqueueRoadReport(...args),
}));

jest.mock('../../lib/analytics', () => ({
  track: { reportSubmitted: mockTrackReportSubmitted },
}));

jest.mock('sonner', () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

let mockChatStore: Record<string, unknown>;

jest.mock('../../lib/store', () => {
  const mockFn: jest.Mock & { getState?: () => unknown } = jest.fn(
    (selector: unknown) => {
      if (typeof selector === 'function') return selector(mockChatStore);
      return mockChatStore;
    }
  );
  mockFn.getState = jest.fn(() => mockChatStore);
  return { useAppStore: mockFn };
});

beforeEach(function() {
  mockChatStore = { gpsLocation: null, connectivity: 'online' };
  mockSubmitReport.mockReset().mockResolvedValue({ uuid: 'test-uuid' });
  mockEnqueueRoadReport.mockReset().mockResolvedValue(undefined);
  mockTrackReportSubmitted.mockReset();
  jest.clearAllMocks();
});

function renderReportForm() {
  const ReportForm = require('../ReportForm').default;
  return render(<ReportForm />);
}

function goToStep2() {
  fireEvent.click(screen.getByRole('button', { name: /configure details/i }));
}

describe('ReportForm', function() {
  it('shows issue type selection on step 1', function() {
    renderReportForm();
    expect(screen.getByRole('button', { name: /issue type: pothole/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /issue type: accident/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /issue type: debris/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /issue type: signage/i })).toBeInTheDocument();
  });

  it('shows severity slider', function() {
    renderReportForm();
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByRole('button', { name: `Severity level ${i}` })).toBeInTheDocument();
    }
  });

  it('navigates to step 2 on configure details click', function() {
    renderReportForm();
    goToStep2();
    expect(screen.getByLabelText(/description of the road issue/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/attach evidence photo/i)).toBeInTheDocument();
  });

  it('shows submit button on step 2', function() {
    renderReportForm();
    goToStep2();
    expect(screen.getByRole('button', { name: /broadcast report/i })).toBeInTheDocument();
  });

  it('allows going back to step 1 from step 2', function() {
    renderReportForm();
    goToStep2();
    fireEvent.click(screen.getByRole('button', { name: /go back to step 1/i }));
    expect(screen.getByRole('button', { name: /issue type: pothole/i })).toBeInTheDocument();
  });

  it('shows toast error when submitting without GPS', async function() {
    renderReportForm();
    goToStep2();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });
    const { toast } = require('sonner');
    expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining('Location')
    );
    expect(mockSubmitReport).not.toHaveBeenCalled();
  });

  it('calls submitReport when GPS exists and form submitted online', async function() {
    mockChatStore = { gpsLocation: { lat: 13.08, lon: 80.27, accuracy: 10, timestamp: Date.now() }, connectivity: 'online' };
    renderReportForm();
    goToStep2();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });
    expect(mockSubmitReport).toHaveBeenCalledTimes(1);
    expect(mockSubmitReport).toHaveBeenCalledWith(
      expect.objectContaining({ lat: 13.08, lon: 80.27, issue_type: 'pothole', severity: 3 })
    );
  });

  it('calls enqueueRoadReport when offline', async function() {
    mockChatStore = { gpsLocation: { lat: 13.08, lon: 80.27, accuracy: 10, timestamp: Date.now() }, connectivity: 'offline' };
    renderReportForm();
    goToStep2();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });
    expect(mockSubmitReport).not.toHaveBeenCalled();
    expect(mockEnqueueRoadReport).toHaveBeenCalledTimes(1);
    expect(mockEnqueueRoadReport).toHaveBeenCalledWith(
      expect.objectContaining({ lat: 13.08, lon: 80.27, issue_type: 'pothole', severity: 3 })
    );
  });

  it('shows success state after submission', async function() {
    mockChatStore = { gpsLocation: { lat: 13.08, lon: 80.27, accuracy: 10, timestamp: Date.now() }, connectivity: 'online' };
    renderReportForm();
    goToStep2();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });
    expect(screen.getByRole('alert')).toHaveTextContent(/Report Uplinked/i);
  });

  it('rejects photo larger than 5MB', async function() {
    mockChatStore = { gpsLocation: { lat: 13.08, lon: 80.27, accuracy: 10, timestamp: Date.now() }, connectivity: 'online' };
    renderReportForm();
    goToStep2();

    const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
    const fileInput = screen.getByLabelText(/attach evidence photo/i);
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [largeFile] } });
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });

    const { toast } = require('sonner');
    expect(toast.error).toHaveBeenCalledWith(expect.stringMatching(/5MB|less/i));
    expect(mockSubmitReport).not.toHaveBeenCalled();
  });

  it('rejects unsupported photo type', async function() {
    mockChatStore = { gpsLocation: { lat: 13.08, lon: 80.27, accuracy: 10, timestamp: Date.now() }, connectivity: 'online' };
    renderReportForm();
    goToStep2();

    const invalidFile = new File(['x'], 'doc.pdf', { type: 'application/pdf' });
    const fileInput = screen.getByLabelText(/attach evidence photo/i);
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [invalidFile] } });
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /broadcast report/i }));
    });

    const { toast } = require('sonner');
    expect(toast.error).toHaveBeenCalledWith(expect.stringMatching(/JPEG|PNG|WebP/i));
    expect(mockSubmitReport).not.toHaveBeenCalled();
  });
});



