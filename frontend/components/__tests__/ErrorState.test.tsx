// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ErrorState } from '../ui/ErrorState';

describe('ErrorState', function() {
  it('renders error message', function() {
    render(<ErrorState message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('has role alert', function() {
    render(<ErrorState message="Error" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('renders retry button when retry provided', function() {
    const handleRetry = jest.fn();
    render(<ErrorState message="Error" retry={handleRetry} />);
    const button = screen.getByText('Try Again');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('renders custom fallback label', function() {
    render(<ErrorState message="Error" retry={() => {}} fallbackLabel="Reload" />);
    expect(screen.getByText('Reload')).toBeInTheDocument();
  });

  it('does not render retry button when retry is undefined', function() {
    render(<ErrorState message="Error" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders default AlertTriangle icon', function() {
    const { container } = render(<ErrorState message="Error" />);
    const iconContainer = container.querySelector('.flex.h-12.w-12');
    expect(iconContainer).toBeInTheDocument();
  });

  it('applies custom className', function() {
    const { container } = render(<ErrorState message="Error" className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('renders RotateCw icon inside retry button', function() {
    render(<ErrorState message="Error" retry={() => {}} />);
    const button = screen.getByText('Try Again');
    expect(button).toBeInTheDocument();
  });
});


