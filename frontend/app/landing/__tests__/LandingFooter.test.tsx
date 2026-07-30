// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';
import { render, screen } from '@testing-library/react';

describe('LandingFooter', function() {
  it('renders brand name and tagline', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText('SafeVixAI')).toBeTruthy();
    expect(screen.getByText('AI-Powered Road Safety Intelligence')).toBeTruthy();
  });

  it('renders platform links', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText('Dashboard').closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByText('Emergency SOS').closest('a')).toHaveAttribute('href', '/sos');
    expect(screen.getByText('Challan Calculator').closest('a')).toHaveAttribute('href', '/challan');
  });

  it('renders resource links with external targets', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText('GitHub').closest('a')).toHaveAttribute('target', '_blank');
    expect(screen.getByText('Dataset Hub').closest('a')).toHaveAttribute('target', '_blank');
  });

  it('renders legal links', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText('Privacy Policy').closest('a')).toHaveAttribute('href', '/privacy');
    expect(screen.getByText('Terms of Service').closest('a')).toHaveAttribute('href', '/terms');
  });

  it('renders copyright and version', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText(/2026 SafeVixAI/)).toBeTruthy();
    expect(screen.getByText(/v2.4.0-SVA/)).toBeTruthy();
  });

  it('renders IIT Madras badge', function() {
    const LandingFooter = require('../components/LandingFooter').default;
    render(React.createElement(LandingFooter));
    expect(screen.getByText('IIT Madras Hackathon 2026')).toBeTruthy();
  });
});
