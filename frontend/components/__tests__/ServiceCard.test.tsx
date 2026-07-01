// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/navigation-launch', function() {
  return {
    openBestNavApp: jest.fn(),
    openNavApp: jest.fn(),
    setPreferredNavApp: jest.fn(),
    getPreferredNavApp: jest.fn().mockReturnValue('google-maps'),
    NAV_APPS: [
      { key: 'google-maps', label: 'Google Maps', emoji: '📍' },
      { key: 'waze', label: 'Waze', emoji: '🗺️' },
      { key: 'apple-maps', label: 'Apple Maps', emoji: '🗺️' },
    ],
  }
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ServiceCard } from '../ServiceCard';

var mockService = {
  id: '1',
  name: 'Apollo Hospital',
  category: 'hospital' as const,
  lat: 13.0827,
  lon: 80.2707,
  distance: 1500,
  phone: '+911234567890',
  source: 'api' as const,
};

describe('ServiceCard', function() {
  beforeEach(function() {
    localStorage.clear();
  });

  it('renders service name', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.getByText('Apollo Hospital')).toBeInTheDocument();
  });

  it('renders category label', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.getByText('Hospital')).toBeInTheDocument();
  });

  it('renders formatted distance in km', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.getByText('1.5 km')).toBeInTheDocument();
  });

  it('renders distance in metres when < 1km', function() {
    var nearbyService = { ...mockService, distance: 500 };
    render(<ServiceCard service={nearbyService} />);
    expect(screen.getByText('500 m')).toBeInTheDocument();
  });

  it('renders distance 0m', function() {
    var nearbyService = { ...mockService, distance: 0 };
    render(<ServiceCard service={nearbyService} />);
    expect(screen.getByText('0 m')).toBeInTheDocument();
  });

  it('renders phone call link when phone is provided', function() {
    render(<ServiceCard service={mockService} />);
    var callLink = screen.getByLabelText('Call Apollo Hospital: +911234567890');
    expect(callLink).toBeInTheDocument();
    expect(callLink).toHaveAttribute('href', 'tel:+911234567890');
  });

  it('does not render call link when phone is missing', function() {
    var noPhoneService = { ...mockService, phone: undefined };
    render(<ServiceCard service={noPhoneService} />);
    expect(screen.queryByText('Call')).not.toBeInTheDocument();
  });

  it('renders directions button', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.getByLabelText('Get directions to Apollo Hospital')).toBeInTheDocument();
  });

  it('renders offline source indicator', function() {
    var offlineService = { ...mockService, source: 'offline' as const };
    var { container } = render(<ServiceCard service={offlineService} />);
    expect(container.textContent).toContain('offline cache');
  });

  it('does not show offline indicator for api source', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.queryByText('offline cache')).not.toBeInTheDocument();
  });

  it('has role article with aria-label', function() {
    render(<ServiceCard service={mockService} />);
    var article = screen.getByRole('article');
    expect(article).toHaveAttribute('aria-label', 'Apollo Hospital');
  });

  it('renders nav app chooser button', function() {
    render(<ServiceCard service={mockService} />);
    expect(screen.getByLabelText('Choose navigation app')).toBeInTheDocument();
  });

  it('shows nav app dropdown on chooser click', function() {
    render(<ServiceCard service={mockService} />);
    fireEvent.click(screen.getByLabelText('Choose navigation app'));
    expect(screen.getByText('Google Maps')).toBeInTheDocument();
    expect(screen.getByText('Waze')).toBeInTheDocument();
    expect(screen.getByText('Apple Maps')).toBeInTheDocument();
  });

  it('hides dropdown on second chooser click', function() {
    render(<ServiceCard service={mockService} />);
    var chooser = screen.getByLabelText('Choose navigation app');
    fireEvent.click(chooser);
    expect(screen.getByText('Google Maps')).toBeInTheDocument();
    fireEvent.click(chooser);
    expect(screen.queryByText('Google Maps')).not.toBeInTheDocument();
  });

  it('renders all category labels', function() {
    var categories = [
      { category: 'ambulance' as const, label: 'Ambulance' },
      { category: 'police' as const, label: 'Police Station' },
      { category: 'fire' as const, label: 'Fire Station' },
      { category: 'towing' as const, label: 'Towing Service' },
      { category: 'pharmacy' as const, label: 'Pharmacy' },
      { category: 'puncture' as const, label: 'Puncture Shop' },
      { category: 'showroom' as const, label: 'Showroom' },
    ];
    for (const { category, label } of categories) {
      var { unmount } = render(<ServiceCard service={{ ...mockService, category }} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    }
  });

  it('applies custom className', function() {
    var { container } = render(<ServiceCard service={mockService} className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('calls openBestNavApp on Map Directions click', function() {
    var nav = require('@/lib/navigation-launch');
    render(<ServiceCard service={mockService} />);
    fireEvent.click(screen.getByLabelText('Get directions to Apollo Hospital'));
    expect(nav.openBestNavApp).toHaveBeenCalled();
  });

  it('selects nav app from dropdown', function() {
    var nav = require('@/lib/navigation-launch');
    render(<ServiceCard service={mockService} />);
    fireEvent.click(screen.getByLabelText('Choose navigation app'));
    var wazeBtn = screen.getByText('Waze');
    fireEvent.click(wazeBtn);
    expect(nav.setPreferredNavApp).toHaveBeenCalledWith('waze');
    expect(nav.openNavApp).toHaveBeenCalled();
  });

  it('shows preferred nav as active in dropdown', function() {
    var nav = require('@/lib/navigation-launch');
    nav.getPreferredNavApp.mockReturnValue('waze');
    render(<ServiceCard service={mockService} />);
    fireEvent.click(screen.getByLabelText('Choose navigation app'));
    var wazeBtn = screen.getByText('Waze');
    expect(wazeBtn).toBeInTheDocument();
    nav.getPreferredNavApp.mockReturnValue('google-maps');
  });
});


