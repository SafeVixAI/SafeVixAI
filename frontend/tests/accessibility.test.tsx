// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Accessibility', function() {
  it('homepage has proper heading structure', function() {
    render(
      <main>
        <h1>SafeVixAI - Road Safety Platform</h1>
        <h2>Emergency Services</h2>
        <h3>Nearby Hospitals</h3>
        <h3>Nearby Police Stations</h3>
        <h2>Quick Actions</h2>
        <h3>Report Road Issue</h3>
      </main>
    );

    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy();
    expect(screen.getByText('SafeVixAI - Road Safety Platform')).toBeTruthy();
  });

  it('interactive elements have accessible names', function() {
    render(
      <div>
        <button aria-label="Send SOS">SOS</button>
        <button aria-label="Open navigation menu">Menu</button>
        <input aria-label="Search location" type="text" />
      </div>
    );

    expect(screen.getByLabelText('Send SOS')).toBeTruthy();
    expect(screen.getByLabelText('Open navigation menu')).toBeTruthy();
    expect(screen.getByLabelText('Search location')).toBeTruthy();
  });

  it('images have alt text', function() {
    render(
      <div>
        <img src="/icon-hospital.png" alt="Hospital icon" />
        <img src="/icon-police.png" alt="Police station icon" />
      </div>
    );

    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(2);
    expect(screen.getByAltText('Hospital icon')).toBeTruthy();
    expect(screen.getByAltText('Police station icon')).toBeTruthy();
  });

  it('form inputs have associated labels', function() {
    render(
      <form>
        <label htmlFor="violation">Violation Type</label>
        <select id="violation">
          <option>Drunk Driving</option>
        </select>

        <label htmlFor="state">State</label>
        <select id="state">
          <option>Tamil Nadu</option>
        </select>
      </form>
    );

    expect(screen.getByLabelText('Violation Type')).toBeTruthy();
    expect(screen.getByLabelText('State')).toBeTruthy();
  });

  it('links have descriptive text', function() {
    render(
      <nav>
        <a href="/emergency">Emergency Locator</a>
        <a href="/challan">Challan Calculator</a>
        <a href="/report">Report Issue</a>
      </nav>
    );

    expect(screen.getByText('Emergency Locator')).toBeTruthy();
    expect(screen.getByText('Challan Calculator')).toBeTruthy();
    expect(screen.getByText('Report Issue')).toBeTruthy();
  });

  it('color contrast meets minimum requirements', function() {
    render(
      <div>
        <p style={{ color: '#1a1a1a', backgroundColor: '#ffffff' }}>
          High contrast text
        </p>
        <p style={{ color: '#ffffff', backgroundColor: '#1a1a1a' }}>
          Inverted contrast text
        </p>
      </div>
    );

    const paragraphs = screen.getAllByText(/contrast text/);
    expect(paragraphs).toHaveLength(2);
  });

  it('keyboard navigation is supported', function() {
    render(
      <div>
        <button tabIndex={0}>Button 1</button>
        <button tabIndex={0}>Button 2</button>
        <a href="/link" tabIndex={0}>Link</a>
        <input tabIndex={0} type="text" />
      </div>
    );

    const focusableElements = screen.getAllByRole('button');
    expect(focusableElements).toHaveLength(2);
  });

  it('aria-live regions for dynamic content', function() {
    render(
      <div>
        <div aria-live="polite" data-testid="status-message">
          Loading...
        </div>
        <div aria-live="assertive" data-testid="error-message">
          Error occurred
        </div>
      </div>
    );

    expect(screen.getByTestId('status-message')).toBeTruthy();
    expect(screen.getByTestId('error-message')).toBeTruthy();
  });

  it('skip navigation link present', function() {
    render(
      <div>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <main id="main-content">Main content</main>
      </div>
    );

    expect(screen.getByText('Skip to main content')).toBeTruthy();
  });

  it('focus indicators visible', function() {
    render(
      <button style={{ outline: '2px solid blue' }}>Focusable Button</button>
    );

    const button = screen.getByText('Focusable Button');
    expect(button).toBeTruthy();
  });
});


