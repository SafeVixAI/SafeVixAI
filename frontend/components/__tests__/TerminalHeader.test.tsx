// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('@/hooks/useSplitTextEntry', () => ({
  useSplitTextEntry: () => ({ current: null }),
}));

import { TerminalHeader } from '../ui/TerminalHeader';

describe('TerminalHeader', function() {
  it('renders title', function() {
    render(<TerminalHeader title="SafeVix" />);
    expect(screen.getByText('SafeVix')).toBeInTheDocument();
  });

  it('renders subtitle when provided', function() {
    render(<TerminalHeader title="SafeVix" subtitle="Road Safety System" />);
    expect(screen.getByText('Road Safety System')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', function() {
    render(<TerminalHeader title="SafeVix" />);
    expect(screen.queryByText('Road Safety System')).not.toBeInTheDocument();
  });

  it('shows Sentinel Active status by default', function() {
    render(<TerminalHeader title="SafeVix" />);
    expect(screen.getByText('Sentinel Active')).toBeInTheDocument();
  });

  it('shows Emergency Active when status is emergency', function() {
    render(<TerminalHeader title="SafeVix" status="emergency" />);
    expect(screen.getByText('Emergency Active')).toBeInTheDocument();
  });

  it('shows Offline status label', function() {
    render(<TerminalHeader title="SafeVix" status="offline" />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('renders rightElement when provided', function() {
    render(<TerminalHeader title="SafeVix" rightElement={<span data-testid="right-el" />} />);
    expect(screen.getByTestId('right-el')).toBeInTheDocument();
  });

  it('has sv-terminal-header class', function() {
    const { container } = render(<TerminalHeader title="SafeVix" />);
    expect(container.firstChild).toHaveClass('sv-terminal-header');
  });

  it('shows terminal-styled branding', function() {
    render(<TerminalHeader title="SafeVix" />);
    const h1 = screen.getByText('SafeVix');
    expect(h1).toHaveClass('sv-terminal-overline');
  });
});



