// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

var mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
}));

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => <a href={href} {...props}>{children}</a>;
});

jest.mock('@/lib/haptics', () => ({
  haptics: { heavy: jest.fn(), light: jest.fn(), medium: jest.fn(), sos: jest.fn(), warning: jest.fn() },
}));

import { GlobalSOS } from '../GlobalSOS';

describe('GlobalSOS', function() {
  beforeEach(function() {
    mockUsePathname.mockReset();
  });

  it('renders null on hidden route /sos', function() {
    mockUsePathname.mockReturnValue('/sos');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on root / route', function() {
    mockUsePathname.mockReturnValue('/');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /emergency route', function() {
    mockUsePathname.mockReturnValue('/emergency');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /first-aid route', function() {
    mockUsePathname.mockReturnValue('/first-aid');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /report route', function() {
    mockUsePathname.mockReturnValue('/report');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /challan route', function() {
    mockUsePathname.mockReturnValue('/challan');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /profile route', function() {
    mockUsePathname.mockReturnValue('/profile');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null on /settings route', function() {
    mockUsePathname.mockReturnValue('/settings');
    var { container } = render(<GlobalSOS />);
    expect(container.firstChild).toBeNull();
  });

  it('renders SOS buttons on non-hidden route /assistant', function() {
    mockUsePathname.mockReturnValue('/assistant');
    render(<GlobalSOS />);
    var buttons = screen.getAllByLabelText('Emergency SOS');
    expect(buttons.length).toBe(2);
  });

  it('has aria-label "Emergency SOS" on buttons', function() {
    mockUsePathname.mockReturnValue('/assistant');
    render(<GlobalSOS />);
    var buttons = screen.getAllByLabelText('Emergency SOS');
    expect(buttons.length).toBe(2);
    buttons.forEach(btn => {
      expect(btn).toHaveAttribute('aria-label', 'Emergency SOS');
    });
  });

  it('links point to /sos', function() {
    mockUsePathname.mockReturnValue('/assistant');
    render(<GlobalSOS />);
    var links = screen.getAllByRole('link');
    links.forEach(link => {
      expect(link).toHaveAttribute('href', '/sos');
    });
  });

  it('renders mobile variant with lg:hidden class', function() {
    mockUsePathname.mockReturnValue('/assistant');
    var { container } = render(<GlobalSOS />);
    var divs = container.querySelectorAll('div.fixed');
    expect(divs.length).toBe(2);
    expect(divs[0]).toHaveClass('lg:hidden');
  });

  it('renders desktop variant with hidden lg:block classes', function() {
    mockUsePathname.mockReturnValue('/assistant');
    var { container } = render(<GlobalSOS />);
    var divs = container.querySelectorAll('div.fixed');
    expect(divs.length).toBe(2);
    expect(divs[1]).toHaveClass('hidden');
    expect(divs[1]).toHaveClass('lg:block');
  });

  it('calls haptics.heavy when SOS link is clicked', function() {
    mockUsePathname.mockReturnValue('/assistant');
    var hapticsMod = require('@/lib/haptics');
    render(<GlobalSOS />);
    var links = screen.getAllByRole('link');
    fireEvent.click(links[0]);
    expect(hapticsMod.haptics.heavy).toHaveBeenCalled();
  });
});



