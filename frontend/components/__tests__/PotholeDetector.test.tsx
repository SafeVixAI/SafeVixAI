// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../lib/client-logger', () => ({
  logClientError: jest.fn(),
}));

jest.mock('sonner', () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

// Mock useRef so the component gets a valid video element for camera setup
var mockVideoElement = document.createElement('video');
jest.mock('react', () => {
  const actual = jest.requireActual('react');
  return {
    ...actual,
    useRef: jest.fn(() => ({ current: mockVideoElement })),
  };
});

var mockTrack = { stop: jest.fn() };
var mockStream = { getTracks: () => [mockTrack] };
var getUserMediaMock: jest.Mock;

beforeEach(function() {
  jest.clearAllMocks();
  mockTrack.stop.mockReset();

  getUserMediaMock = jest.fn().mockResolvedValue(mockStream);
  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia: getUserMediaMock },
    configurable: true,
    writable: true,
  });
});

function renderPotholeDetector() {
  var PotholeDetector = require('../PotholeDetector').default;
  return render(<PotholeDetector />);
}

describe('PotholeDetector', function() {
  it('starts camera on mount', function() {
    renderPotholeDetector();
    expect(getUserMediaMock).toHaveBeenCalledWith(
      expect.objectContaining({ video: { facingMode: 'environment' } })
    );
  });

  it('hasCamera state becomes true after camera starts', async function() {
    renderPotholeDetector();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /initiate ai scan/i })).toBeEnabled();
    });
  });

  it('scanning toggle changes button text immediately', async function() {
    renderPotholeDetector();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /initiate ai scan/i })).toBeEnabled();
    });
    fireEvent.click(screen.getByRole('button', { name: /initiate ai scan/i }));
    expect(screen.getByRole('button', { name: /processing sensor grid/i })).toBeDisabled();
  });

  it('shows camera-unavailable state when getUserMedia rejects', async function() {
    getUserMediaMock.mockRejectedValue(new Error('Permission denied'));
    renderPotholeDetector();
    await act(async () => {});
    expect(screen.getByText(/active sensor required/i)).toBeInTheDocument();
  });

  it('stops camera tracks on unmount', async function() {
    var { unmount } = renderPotholeDetector();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /initiate ai scan/i })).toBeEnabled();
    });
    unmount();
    expect(mockTrack.stop).toHaveBeenCalledTimes(1);
  });

  it('scan shows processing state and completes with error fallback', async function() {
    jest.useFakeTimers()
    // Mock getContext to return null, triggering error path
    var origCreateElement = document.createElement.bind(document)
    var createElementSpy = jest.fn(function(tag: string) {
      var el = origCreateElement(tag)
      if (tag === 'canvas') {
        jest.spyOn(el, 'getContext').mockReturnValue(null)
      }
      return el
    })
    document.createElement = createElementSpy

    renderPotholeDetector()
    await waitFor(function () {
      expect(screen.getByRole('button', { name: /initiate ai scan/i })).toBeEnabled()
    })

    fireEvent.click(screen.getByRole('button', { name: /initiate ai scan/i }))
    expect(screen.getByText(/processing sensor grid/i)).toBeDisabled()

    act(function () { jest.advanceTimersByTime(2000) })

    // Error fallback sets detected=true
    expect(screen.getByText(/ph-crater detected/i)).toBeInTheDocument()

    document.createElement = origCreateElement
    jest.useRealTimers()
  })

  it('scan completes with no anomaly when no edge pixels', async function() {
    jest.useFakeTimers()
    var origCreateElement = document.createElement.bind(document)
    var createElementSpy = jest.fn(function(tag: string) {
      var el = origCreateElement(tag)
      if (tag === 'canvas') {
        var mockCtx = {
          drawImage: jest.fn(),
          getImageData: jest.fn(function() {
            return { data: new Uint8ClampedArray(160 * 120 * 4), width: 160, height: 120 }
          }),
        }
        jest.spyOn(el, 'getContext').mockReturnValue(mockCtx as any)
        Object.defineProperty(el, 'width', { value: 160, writable: true })
        Object.defineProperty(el, 'height', { value: 120, writable: true })
      }
      return el
    })
    document.createElement = createElementSpy

    renderPotholeDetector()
    await waitFor(function () {
      expect(screen.getByRole('button', { name: /initiate ai scan/i })).toBeEnabled()
    })

    fireEvent.click(screen.getByRole('button', { name: /initiate ai scan/i }))

    act(function () { jest.advanceTimersByTime(2000) })

    var toast = require('sonner').toast
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('No high-contrast')
    )

    document.createElement = origCreateElement
    jest.useRealTimers()
  })
});



