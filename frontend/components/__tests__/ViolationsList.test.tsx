// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('ViolationsList', function() {
  it('renders all 8 common violations', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { getByText } = render(<ViolationsList />);
    expect(getByText(/General Provision/i)).toBeInTheDocument();
    expect(getByText(/Violation of road regulations/i)).toBeInTheDocument();
    expect(getByText(/Driving without an active license/i)).toBeInTheDocument();
    expect(getByText(/Over-speeding/i)).toBeInTheDocument();
    expect(getByText(/Dangerous driving/i)).toBeInTheDocument();
    expect(getByText(/Drunken driving/i)).toBeInTheDocument();
    expect(getByText(/seat belt/i)).toBeInTheDocument();
    expect(getByText(/helmet/i)).toBeInTheDocument();
  });

  it('renders section numbers', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { container } = render(<ViolationsList />);
    expect(container.textContent).toMatch(/Section 185 of MV Act 1988/);
    expect(container.textContent).toMatch(/Section 194B of MV Act 1988/);
    expect(container.textContent).toMatch(/Section 177A of MV Act 1988/);
  });

  it('renders fine amounts', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { getByText } = render(<ViolationsList />);
    expect(getByText('₹5,000')).toBeInTheDocument();
    expect(getByText('₹1,000')).toBeInTheDocument();
    expect(getByText('₹10,000 (₹15000 repeat)')).toBeInTheDocument();
  });

  it('renders title', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { getByText } = render(<ViolationsList />);
    expect(getByText(/Common Violations Directory/i)).toBeInTheDocument();
  });

  it('shows MV Act source', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { getByText } = render(<ViolationsList />);
    expect(getByText(/Motor Vehicles \(Amendment\) Act 2019/i)).toBeInTheDocument();
  });

  it('renders card-glass class', async function() {
    const { ViolationsList } = await import('../ViolationsList');
    const { container } = render(<ViolationsList />);
    expect(container.firstChild).toHaveClass('card-glass');
  });
});


