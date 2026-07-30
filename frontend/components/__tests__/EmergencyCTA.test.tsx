// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EmergencyCTA } from '../ui/EmergencyCTA';

describe('EmergencyCTA', function() {
  it('renders title', function() {
    render(<EmergencyCTA title="Call 112" />);
    expect(screen.getByText('Call 112')).toBeInTheDocument();
  });

  it('renders subtitle when provided', function() {
    render(<EmergencyCTA title="SOS" subtitle="Emergency services" />);
    expect(screen.getByText('Emergency services')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', function() {
    render(<EmergencyCTA title="SOS" />);
    expect(screen.getByText('SOS')).toBeInTheDocument();
  });

  it('renders icon when provided', function() {
    render(<EmergencyCTA title="Help" icon={<span data-testid="cta-icon">!</span>} />);
    expect(screen.getByTestId('cta-icon')).toBeInTheDocument();
  });

  it('calls onClick when clicked', function() {
    const handleClick = jest.fn();
    render(<EmergencyCTA title="Call Now" onClick={handleClick} />);
    fireEvent.click(screen.getByText('Call Now'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders as a button element', function() {
    render(<EmergencyCTA title="SOS" />);
    const btn = screen.getByRole('button', { name: /SOS/ });
    expect(btn).toBeInTheDocument();
    expect(btn.tagName).toBe('BUTTON');
  });

  it('has emergency background', function() {
    const { container } = render(<EmergencyCTA title="SOS" />);
    expect(container.firstChild).toHaveClass('bg-emergency');
  });

  it('applies custom className', function() {
    const { container } = render(<EmergencyCTA title="SOS" className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('can be disabled', function() {
    render(<EmergencyCTA title="SOS" disabled />);
    expect(screen.getByRole('button', { name: /SOS/ })).toBeDisabled();
  });

  it('forwards additional button props', function() {
    render(<EmergencyCTA title="SOS" data-testid="emergency-btn" />);
    expect(screen.getByTestId('emergency-btn')).toBeInTheDocument();
  });
});


