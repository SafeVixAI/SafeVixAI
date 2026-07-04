// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';
import { render, screen } from '@testing-library/react';

jest.mock('../hooks/useLandingGSAP', function() {
  return { useScrollReveal: jest.fn().mockReturnValue({ current: null }) };
});

describe('CTASection', function() {
  it('renders heading and subtitle', function() {
    var CTASection = require('../components/CTASection').default;
    render(React.createElement(CTASection));
    expect(screen.getByText('Ready to Transform Road Safety?')).toBeTruthy();
    expect(screen.getByText(/protecting India's roads/)).toBeTruthy();
  });

  it('renders launch and explore links', function() {
    var CTASection = require('../components/CTASection').default;
    render(React.createElement(CTASection));
    expect(screen.getByText('Launch Platform').closest('a')).toHaveAttribute('href', '/login');
    expect(screen.getByText('Explore Intelligence').closest('a')).toHaveAttribute('href', '/');
  });

  it('renders GitHub link', function() {
    var CTASection = require('../components/CTASection').default;
    render(React.createElement(CTASection));
    var ghLink = screen.getByText('View GitHub');
    expect(ghLink.closest('a')).toHaveAttribute('href', 'https://github.com/SafeVixAI/SafeVixAI');
    expect(ghLink.closest('a')).toHaveAttribute('target', '_blank');
  });
});
