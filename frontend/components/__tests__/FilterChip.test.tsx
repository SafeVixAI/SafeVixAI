// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FilterChip } from '../ui/FilterChip';

describe('FilterChip', function() {
  it('renders label', function() {
    render(<FilterChip label="Hospital" />);
    expect(screen.getByText('Hospital')).toBeInTheDocument();
  });

  it('has role radio', function() {
    render(<FilterChip label="All" />);
    expect(screen.getByRole('radio')).toBeInTheDocument();
  });

  it('sets aria-checked to false by default', function() {
    render(<FilterChip label="All" />);
    expect(screen.getByRole('radio')).toHaveAttribute('aria-checked', 'false');
  });

  it('sets aria-checked to true when active', function() {
    render(<FilterChip label="All" active={true} />);
    expect(screen.getByRole('radio')).toHaveAttribute('aria-checked', 'true');
  });

  it('applies active class when active', function() {
    const { container } = render(<FilterChip label="All" active={true} />);
    expect(container.firstChild).toHaveClass('sv-chip-active');
  });

  it('does not apply active class by default', function() {
    const { container } = render(<FilterChip label="All" />);
    expect(container.firstChild).not.toHaveClass('sv-chip-active');
  });

  it('renders icon when provided', function() {
    render(<FilterChip label="All" icon={<span data-testid="chip-icon">+</span>} />);
    expect(screen.getByTestId('chip-icon')).toBeInTheDocument();
  });

  it('does not render icon wrapper when icon not provided', function() {
    const { container } = render(<FilterChip label="All" />);
    const spans = container.querySelectorAll('span');
    expect(spans.length).toBe(0);
  });

  it('calls onClick when clicked', function() {
    const handleClick = jest.fn();
    render(<FilterChip label="All" onClick={handleClick} />);
    fireEvent.click(screen.getByRole('radio'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', function() {
    const { container } = render(<FilterChip label="All" className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('is type button', function() {
    render(<FilterChip label="All" />);
    expect(screen.getByRole('radio')).toHaveAttribute('type', 'button');
  });

  it('forwards additional button props', function() {
    render(<FilterChip label="All" data-testid="filter-chip" disabled />);
    const chip = screen.getByTestId('filter-chip');
    expect(chip).toBeDisabled();
  });
});


