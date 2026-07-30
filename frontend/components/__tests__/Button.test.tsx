// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('@base-ui/react/button', () => ({
  Button: ({ children, className, ...props }: any) =>
    React.createElement('button', { className, ...props }, children),
}));

import { Button } from '../ui/button';

describe('Button', function() {
  it('renders children', function() {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('renders all variant props without error', function() {
    const variants = ['default', 'brand', 'emergency', 'terminal', 'safeGhost', 'outline', 'secondary', 'ghost', 'destructive', 'link'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Button variant={variant}>{variant}</Button>);
      expect(screen.getByText(variant)).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all size props without error', function() {
    const sizes = ['default', 'xs', 'sm', 'lg', 'icon', 'icon-xs', 'icon-sm', 'icon-lg'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Button size={size}>{size}</Button>);
      expect(screen.getByText(size)).toBeInTheDocument();
      unmount();
    }
  });

  it('applies className prop', function() {
    render(<Button className="my-custom-class">Styled</Button>);
    expect(screen.getByText('Styled').className).toContain('my-custom-class');
  });

  it('renders disabled state with disabled attribute', function() {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText('Disabled')).toBeDisabled();
  });

  it('has data-slot="button"', function() {
    render(<Button>Test</Button>);
    expect(screen.getByText('Test')).toHaveAttribute('data-slot', 'button');
  });

  it('forwards additional props', function() {
    render(<Button data-testid="my-btn">Test</Button>);
    expect(screen.getByTestId('my-btn')).toBeInTheDocument();
  });

  it('applies default variant classes', function() {
    render(<Button>Default</Button>);
    const btn = screen.getByText('Default');
    expect(btn.className).toContain('inline-flex');
    expect(btn.className).toContain('rounded-lg');
    expect(btn.className).toContain('font-medium');
  });
});



