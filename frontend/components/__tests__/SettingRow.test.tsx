// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SettingRow } from '../ui/SettingRow';

describe('SettingRow', function() {
  it('renders label', function() {
    render(<SettingRow title="Speed Alert" />);
    expect(screen.getByText('Speed Alert')).toBeInTheDocument();
  });

  it('renders description below label', function() {
    render(<SettingRow title="Speed Alert" description="Alert when exceeding speed limit" />);
    expect(screen.getByText('Speed Alert')).toBeInTheDocument();
    expect(screen.getByText('Alert when exceeding speed limit')).toBeInTheDocument();
  });

  it('does not render description when not provided', function() {
    render(<SettingRow title="Speed Alert" />);
    expect(screen.queryByText('Alert when exceeding speed limit')).not.toBeInTheDocument();
  });

  it('renders rightElement controls', function() {
    render(<SettingRow title="Notifications" rightElement={<span data-testid="control">toggle</span>} />);
    expect(screen.getByTestId('control')).toBeInTheDocument();
  });

  it('renders icon when provided', function() {
    render(<SettingRow title="Speed Alert" icon={<span data-testid="icon">*</span>} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('renders rightElement when provided', function() {
    render(<SettingRow title="Speed Alert" rightElement={<span data-testid="right">arr</span>} />);
    expect(screen.getByTestId('right')).toBeInTheDocument();
  });

  it('renders as div when no onClick provided', function() {
    const { container } = render(<SettingRow title="Speed Alert" />);
    expect(container.firstChild?.nodeName).toBe('DIV');
  });

  it('renders as button when onClick provided', function() {
    const handleClick = jest.fn();
    const { container } = render(<SettingRow title="Speed Alert" onClick={handleClick} />);
    expect(container.firstChild?.nodeName).toBe('BUTTON');
  });

  it('calls onClick when clicked and onClick provided', function() {
    const handleClick = jest.fn();
    render(<SettingRow title="Speed Alert" onClick={handleClick} />);
    fireEvent.click(screen.getByText('Speed Alert'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies border-b class for separation', function() {
    const { container } = render(<SettingRow title="Speed Alert" />);
    expect(container.firstChild).toHaveClass('border-b');
  });
});


