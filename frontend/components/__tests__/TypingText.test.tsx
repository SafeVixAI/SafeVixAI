// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('TypingText', function() {
  beforeEach(function() {
    jest.useFakeTimers();
  });

  afterEach(function() {
    jest.useRealTimers();
  });

  it('renders empty initially', async function() {
    const TypingText = (await import('../dashboard/TypingText')).default;
    const { container } = render(<TypingText text="Hello World" />);
    const span = container.querySelector('span');
    expect(span).toBeInTheDocument();
    expect(span?.textContent).toBe('');
  });

  it('types text step by step', async function() {
    const TypingText = (await import('../dashboard/TypingText')).default;
    render(<TypingText text="Hi" />);
    act(() => { jest.advanceTimersByTime(10); });
    act(() => { jest.advanceTimersByTime(10); });
    expect(screen.getByText('Hi')).toBeInTheDocument();
  });

  it('displays full text after advancing enough', async function() {
    const TypingText = (await import('../dashboard/TypingText')).default;
    render(<TypingText text="AB" />);
    for (let i = 0; i < 5; i++) {
      act(() => { jest.advanceTimersByTime(10); });
    }
    expect(screen.getByText('AB')).toBeInTheDocument();
  });

  it('calls onComplete when typing finishes', async function() {
    const onComplete = jest.fn();
    const TypingText = (await import('../dashboard/TypingText')).default;
    render(<TypingText text="A" onComplete={onComplete} />);
    for (let i = 0; i < 5; i++) {
      act(() => { jest.advanceTimersByTime(10); });
    }
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it('resets when text changes', async function() {
    const TypingText = (await import('../dashboard/TypingText')).default;
    const { rerender } = render(<TypingText text="Hello" />);
    for (let i = 0; i < 10; i++) {
      act(() => { jest.advanceTimersByTime(10); });
    }
    expect(screen.getByText('Hello')).toBeInTheDocument();
    rerender(<TypingText text="Bye" />);
    for (let i = 0; i < 10; i++) {
      act(() => { jest.advanceTimersByTime(10); });
    }
    expect(screen.getByText('Bye')).toBeInTheDocument();
  });
});


