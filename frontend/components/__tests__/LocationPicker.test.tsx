// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const onLocationChange = jest.fn();

jest.mock('next/dynamic', () => {
  const MockLocationPicker = (props: Record<string, unknown>) => (
    <div data-testid="location-picker-inner" data-lat={props.lat} data-lon={props.lon}>Map Placeholder</div>
  );
  return () => MockLocationPicker;
});

describe('LocationPicker', function() {
  it('renders dynamically loaded map component', async function() {
    const LocationPicker = (await import('../report/LocationPicker')).default;
    const { container } = render(<LocationPicker lat={13.0827} lon={80.2707} onLocationChange={onLocationChange} />);
    expect(container.querySelector('[data-testid="location-picker-inner"]')).toBeInTheDocument();
  });

  it('renders without crashing', async function() {
    const LocationPicker = (await import('../report/LocationPicker')).default;
    render(<LocationPicker lat={13.0827} lon={80.2707} onLocationChange={onLocationChange} />);
    expect(screen.getByTestId('location-picker-inner')).toBeInTheDocument();
  });
});


