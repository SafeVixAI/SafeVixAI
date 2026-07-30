// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
const React = require('react');
const rtl = require('@testing-library/react');

describe('useBackendPrewarm', function() {
  let mockFetch: jest.Mock;
  let originalApiUrl: string | undefined;
  let originalChatbotUrl: string | undefined;

  beforeEach(function() {
    jest.useFakeTimers();
    jest.spyOn(global, 'setTimeout');
    mockFetch = jest.fn().mockResolvedValue({ ok: true });
    global.fetch = mockFetch;
    originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
    originalChatbotUrl = process.env.NEXT_PUBLIC_CHATBOT_URL;
  });

  afterEach(function() {
    jest.useRealTimers();
    process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
    process.env.NEXT_PUBLIC_CHATBOT_URL = originalChatbotUrl;
    rtl.act(function() {});
  });

  function renderHook() {
    const result: { current: unknown } = { current: null };
    function TestComponent() {
      const mod = require('../hooks/useBackendPrewarm');
      mod.useBackendPrewarm();
      React.useEffect(function() { result.current = 'mounted'; }, []);
      return null;
    }
    rtl.render(React.createElement(TestComponent));
    return result;
  }

  it('fires health check to backend after delay', function() {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    renderHook();
    expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 2000);
    jest.advanceTimersByTime(2000);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/health',
      expect.objectContaining({ method: 'GET', keepalive: true })
    );
  });

  it('fires health check to both urls when different', function() {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    process.env.NEXT_PUBLIC_CHATBOT_URL = 'http://localhost:8010';
    renderHook();
    jest.advanceTimersByTime(2000);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/health', expect.any(Object));
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8010/api/v1/health', expect.any(Object));
  });

  it('does not fire when API_URL is not set', function() {
    delete process.env.NEXT_PUBLIC_API_URL;
    renderHook();
    jest.advanceTimersByTime(2000);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('cleans up timer on unmount', function() {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const clearSpy = jest.spyOn(global, 'clearTimeout');
    const comp = rtl.render(React.createElement(function() {
      const mod = require('../hooks/useBackendPrewarm');
      mod.useBackendPrewarm();
      return null;
    }));
    comp.unmount();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });
});
