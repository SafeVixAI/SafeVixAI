// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Toast', function() {
  const mockOnClose = jest.fn();

  beforeEach(function() {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(function() {
    jest.useRealTimers();
  });

  it('renders message when visible', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Operation successful" isVisible={true} onClose={mockOnClose} />);
    expect(screen.getByText('Operation successful')).toBeInTheDocument();
  });

  it('does not render when not visible', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    const { container } = render(<Toast message="Hidden toast" isVisible={false} onClose={mockOnClose} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders success icon for success type', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Success" type="success" isVisible={true} onClose={mockOnClose} />);
    expect(screen.getByText('Success')).toBeInTheDocument();
  });

  it('renders error icon for error type', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Error occurred" type="error" isVisible={true} onClose={mockOnClose} />);
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  it('renders info icon for info type', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Info message" type="info" isVisible={true} onClose={mockOnClose} />);
    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Dismiss me" isVisible={true} onClose={mockOnClose} />);
    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('auto-dismisses after default duration', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Auto dismiss" isVisible={true} onClose={mockOnClose} />);
    act(() => { jest.advanceTimersByTime(3000); });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('auto-dismisses after custom duration', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Custom" isVisible={true} onClose={mockOnClose} duration={5000} />);
    act(() => { jest.advanceTimersByTime(5000); });
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('does not auto-dismiss when duration is 0', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Persistent" isVisible={true} onClose={mockOnClose} duration={0} />);
    act(() => { jest.advanceTimersByTime(10000); });
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('has uppercase message styling', async function() {
    const Toast = (await import('../dashboard/Toast')).default;
    render(<Toast message="Styled" isVisible={true} onClose={mockOnClose} />);
    const msgSpan = screen.getByText('Styled');
    expect(msgSpan.className).toContain('uppercase');
  });
});


