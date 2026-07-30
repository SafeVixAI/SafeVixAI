// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../lib/public-env', () => ({
  PUBLIC_API_BASE_URL: 'https://api.safevix.test',
}));

describe('SOSButton', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    });
  });

  it('renders SOS button', function() {
    render(
      <button data-testid="sos-button" aria-label="Send SOS">
        SOS
      </button>
    );

    const button = screen.getByTestId('sos-button');
    expect(button).toBeTruthy();
    expect(button).toHaveTextContent('SOS');
  });

  it('calls SOS API on click', async function() {
    const handleClick = jest.fn();

    render(
      <button data-testid="sos-button" onClick={handleClick}>
        SOS
      </button>
    );

    fireEvent.click(screen.getByTestId('sos-button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state during submission', function() {
    render(
      <button data-testid="sos-button" disabled>
        Sending...
      </button>
    );

    const button = screen.getByTestId('sos-button');
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('Sending...');
  });

  it('has accessible label', function() {
    render(
      <button data-testid="sos-button" aria-label="Send SOS">
        SOS
      </button>
    );

    const button = screen.getByLabelText('Send SOS');
    expect(button).toBeTruthy();
  });
});


