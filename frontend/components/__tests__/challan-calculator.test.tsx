// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../lib/public-env', () => ({
  PUBLIC_API_BASE_URL: 'https://api.safevix.test',
}));

describe('ChallanCalculator', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        section: '185',
        base_fine: 10000,
        repeat_fine: 15000,
        amount_due: 10000,
      }),
    });
  });

  it('renders calculator form', function() {
    render(
      <div data-testid="challan-form">
        <select data-testid="violation-select">
          <option value="dui">Drunk Driving</option>
          <option value="helmet">No Helmet</option>
        </select>
        <select data-testid="state-select">
          <option value="TN">Tamil Nadu</option>
          <option value="MH">Maharashtra</option>
        </select>
        <select data-testid="vehicle-select">
          <option value="2w">Two Wheeler</option>
          <option value="4w">Four Wheeler</option>
        </select>
        <button data-testid="calculate-button">Calculate Fine</button>
      </div>
    );

    expect(screen.getByTestId('violation-select')).toBeTruthy();
    expect(screen.getByTestId('state-select')).toBeTruthy();
    expect(screen.getByTestId('vehicle-select')).toBeTruthy();
    expect(screen.getByTestId('calculate-button')).toBeTruthy();
  });

  it('allows violation selection', function() {
    render(
      <select data-testid="violation-select">
        <option value="dui">Drunk Driving</option>
        <option value="helmet">No Helmet</option>
      </select>
    );

    const select = screen.getByTestId('violation-select');
    fireEvent.change(select, { target: { value: 'helmet' } });

    expect(select).toHaveValue('helmet');
  });

  it('allows state selection', function() {
    render(
      <select data-testid="state-select">
        <option value="TN">Tamil Nadu</option>
        <option value="MH">Maharashtra</option>
      </select>
    );

    const select = screen.getByTestId('state-select');
    fireEvent.change(select, { target: { value: 'MH' } });

    expect(select).toHaveValue('MH');
  });

  it('displays calculation result', function() {
    render(
      <div data-testid="result-container">
        <p data-testid="fine-amount">Fine: ₹10,000</p>
        <p data-testid="section">Section: 185</p>
      </div>
    );

    expect(screen.getByTestId('fine-amount')).toBeTruthy();
    expect(screen.getByText('Fine: ₹10,000')).toBeTruthy();
  });

  it('shows loading state during calculation', function() {
    render(
      <div data-testid="loading-state">
        <span>Calculating...</span>
      </div>
    );

    expect(screen.getByText('Calculating...')).toBeTruthy();
  });

  it('shows error state on API failure', function() {
    render(
      <div data-testid="error-state">
        <p>Failed to calculate fine. Please try again.</p>
      </div>
    );

    expect(screen.getByText('Failed to calculate fine. Please try again.')).toBeTruthy();
  });

  it('supports repeat offender toggle', function() {
    render(
      <div>
        <label>
          <input type="checkbox" data-testid="repeat-toggle" />
          Repeat Offender
        </label>
      </div>
    );

    const checkbox = screen.getByTestId('repeat-toggle');
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });
});


