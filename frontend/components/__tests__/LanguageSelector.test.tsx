// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockPush = jest.fn();
const mockSetUserProfile = jest.fn();
const mockStore = {
  userProfile: { preferredLanguage: 'en' },
  setUserProfile: mockSetUserProfile,
};

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('lucide-react', () => ({
  Globe: () => <span data-testid="globe-icon" />,
}));

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => selector(mockStore),
}));

import { LanguageSelector } from '../ui/LanguageSelector';

describe('LanguageSelector', function() {
  beforeEach(function() {
    mockPush.mockClear();
    mockSetUserProfile.mockClear();
  });

  it('renders language options', function() {
    render(<LanguageSelector />);
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('हिन्दी (Hindi)')).toBeInTheDocument();
    expect(screen.getByText('தமிழ் (Tamil)')).toBeInTheDocument();
  });

  it('has select with aria-label', function() {
    render(<LanguageSelector />);
    expect(screen.getByLabelText('Select preferred language')).toBeInTheDocument();
  });

  it('highlights current language', function() {
    render(<LanguageSelector />);
    const select = screen.getByLabelText('Select preferred language') as HTMLSelectElement;
    expect(select.value).toBe('en');
  });

  it('calls onChangeLanguage when selecting a language', function() {
    const handleChange = jest.fn();
    render(<LanguageSelector onChangeLanguage={handleChange} />);
    const select = screen.getByLabelText('Select preferred language');
    fireEvent.change(select, { target: { value: 'hi' } });
    expect(handleChange).toHaveBeenCalledWith('hi');
  });

  it('updates store when language changes', function() {
    render(<LanguageSelector />);
    const select = screen.getByLabelText('Select preferred language');
    fireEvent.change(select, { target: { value: 'ta' } });
    expect(mockSetUserProfile).toHaveBeenCalledWith({ preferredLanguage: 'ta' });
  });

  it('renders globe icon', function() {
    render(<LanguageSelector />);
    expect(screen.getByTestId('globe-icon')).toBeInTheDocument();
  });

  it('applies custom className', function() {
    const { container } = render(<LanguageSelector className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('navigates with locale prefix replacement when path has one', function() {
    window.history.pushState({}, '', '/hi/challan')
    render(<LanguageSelector />);
    fireEvent.change(screen.getByLabelText('Select preferred language'), { target: { value: 'ta' } });
    expect(mockPush).toHaveBeenCalledWith('/ta/challan');
  });

  it('inserts locale prefix when path has no locale', function() {
    window.history.pushState({}, '', '/challan')
    render(<LanguageSelector />);
    fireEvent.change(screen.getByLabelText('Select preferred language'), { target: { value: 'ta' } });
    expect(mockPush).toHaveBeenCalledWith('/ta/challan');
  });

  it('works without onChangeLanguage callback', function() {
    window.history.pushState({}, '', '/')
    render(<LanguageSelector />);
    fireEvent.change(screen.getByLabelText('Select preferred language'), { target: { value: 'hi' } });
    expect(mockSetUserProfile).toHaveBeenCalledWith({ preferredLanguage: 'hi' });
  });

  it('falls back to en when preferredLanguage is empty', function() {
    mockStore.userProfile.preferredLanguage = '';
    render(<LanguageSelector />);
    const select = screen.getByLabelText('Select preferred language') as HTMLSelectElement;
    expect(select.value).toBe('en');
    mockStore.userProfile.preferredLanguage = 'en';
  });
});



