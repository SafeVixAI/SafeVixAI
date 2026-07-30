// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Select } from '../ui/Select';

describe('Select', function() {
  const options = [
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' },
  ];

  it('renders options', function() {
    render(<Select options={options} value="" onChange={() => {}} />);
    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
  });

  it('renders placeholder by default', function() {
    render(<Select options={options} value="" onChange={() => {}} />);
    expect(screen.getByText('Select...')).toBeInTheDocument();
  });

  it('renders custom placeholder', function() {
    render(<Select options={options} value="" onChange={() => {}} placeholder="Pick one" />);
    expect(screen.getByText('Pick one')).toBeInTheDocument();
  });

  it('renders label when provided', function() {
    render(<Select options={options} value="" onChange={() => {}} label="Category" />);
    expect(screen.getByText('Category')).toBeInTheDocument();
  });

  it('links label to select via htmlFor', function() {
    render(<Select options={options} value="" onChange={() => {}} label="My Label" />);
    const label = screen.getByText('My Label');
    expect(label).toHaveAttribute('for', 'my-label');
  });

  it('renders error message when error provided', function() {
    render(<Select options={options} value="" onChange={() => {}} error="Required" />);
    expect(screen.getByText('Required')).toBeInTheDocument();
  });

  it('error message has role alert', function() {
    render(<Select options={options} value="" onChange={() => {}} error="Error" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('does not render error when not provided', function() {
    const { container } = render(<Select options={options} value="" onChange={() => {}} />);
    const alerts = container.querySelectorAll('[role="alert"]');
    expect(alerts.length).toBe(0);
  });

  it('calls onChange when selection changes', function() {
    const handleChange = jest.fn();
    render(<Select options={options} value="" onChange={handleChange} />);
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'opt1' } });
    expect(handleChange).toHaveBeenCalledWith('opt1');
  });

  it('has aria-label when ariaLabel provided', function() {
    render(<Select options={options} value="" onChange={() => {}} ariaLabel="Custom Aria" />);
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-label', 'Custom Aria');
  });

  it('uses label as fallback for aria-label', function() {
    render(<Select options={options} value="" onChange={() => {}} label="Category" />);
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-label', 'Category');
  });

  it('handles empty options array', function() {
    render(<Select options={[]} value="" onChange={() => {}} />);
    const select = screen.getByRole('combobox');
    expect(select.children.length).toBe(1);
    expect(select.children[0]).toHaveValue('');
  });

  it('selects the current value', function() {
    render(<Select options={options} value="opt2" onChange={() => {}} />);
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('opt2');
  });

  it('applies error border class when error present', function() {
    const { container } = render(<Select options={options} value="" onChange={() => {}} error="Error" />);
    const select = container.querySelector('select');
    expect(select).toHaveClass('border-emergency');
  });

  it('applies custom className', function() {
    const { container } = render(<Select options={options} value="" onChange={() => {}} className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });
});


