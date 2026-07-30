// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockOnResult = jest.fn();

jest.mock('../../lib/languages', () => ({
  getLanguageByCode: jest.fn((code: string) => {
    if (code === 'hi') return { recognitionCode: 'hi-IN' };
    return { recognitionCode: 'en-IN' };
  }),
}));

jest.mock('../../lib/client-logger', () => ({
  logClientWarning: jest.fn(),
}));

let mockRecognitionInstance: Record<string, unknown>;
let recognitionConstructor: jest.Mock;

beforeEach(function() {
  mockOnResult.mockClear();
  jest.clearAllMocks();

  mockRecognitionInstance = {
    lang: '',
    continuous: false,
    interimResults: false,
    maxAlternatives: 1,
    start: jest.fn(),
    stop: jest.fn(),
    abort: jest.fn(),
    onstart: null,
    onerror: null,
    onresult: null,
    onend: null,
  };

  recognitionConstructor = jest.fn(() => mockRecognitionInstance);
  (window as any).SpeechRecognition = recognitionConstructor;
  (window as any).webkitSpeechRecognition = undefined;
});

function renderVoiceInput(props: Record<string, unknown> = {}) {
  const { VoiceInput } = require('../VoiceInput');
  return render(<VoiceInput onResult={mockOnResult} {...props} />);
}

describe('VoiceInput', function() {
  it('renders mic button', function() {
    renderVoiceInput();
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
  });

  it('starts recording on click and shows stop button after onstart', async function() {
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    expect(mockRecognitionInstance.start).toHaveBeenCalledTimes(1);

    await act(async () => {
      (mockRecognitionInstance.onstart as () => void)();
    });

    expect(screen.getByRole('button', { name: /stop recording/i })).toBeInTheDocument();
  });

  it('shows loading state while starting recognition', function() {
    renderVoiceInput();
    const button = screen.getByRole('button', { name: /start voice input/i });
    fireEvent.click(button);
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeDisabled();
  });

  it('calls onResult when speech result arrives', async function() {
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    await act(async () => { (mockRecognitionInstance.onstart as () => void)(); });
    await act(async () => {
      (mockRecognitionInstance.onresult as (e: unknown) => void)({
        results: [[{ transcript: 'road hazard ahead' }]],
      });
    });
    expect(mockOnResult).toHaveBeenCalledWith('road hazard ahead');
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
  });

  it('sets recognition.lang based on language prop', function() {
    renderVoiceInput({ language: 'hi' });
    expect(mockRecognitionInstance.lang).toBe('hi-IN');
  });

  it('cleans up recognition on unmount', function() {
    const { unmount } = renderVoiceInput();
    unmount();
    expect(mockRecognitionInstance.abort).toHaveBeenCalledTimes(1);
  });

  it('handles recognition error gracefully', async function() {
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    await act(async () => {
      (mockRecognitionInstance.onerror as (e: unknown) => void)({ error: 'not-allowed' });
    });
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
  });

  it('stops loading when speech recognition onend fires', async function() {
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    await act(async () => { (mockRecognitionInstance.onstart as () => void)(); });
    await act(async () => { (mockRecognitionInstance.onend as () => void)(); });
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
  });

  it('stops recording when toggle clicked while recording', async function() {
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    await act(async () => { (mockRecognitionInstance.onstart as () => void)(); });
    fireEvent.click(screen.getByRole('button', { name: /stop recording/i }));
    expect(mockRecognitionInstance.stop).toHaveBeenCalledTimes(1);
  });

  it('gracefully falls back when SpeechRecognition not available', async function() {
    (window as any).SpeechRecognition = undefined;
    (window as any).webkitSpeechRecognition = undefined;
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    expect(mockOnResult).toHaveBeenCalledWith('Reporting a road hazard at my current location.');
  });

  it('handles start failure gracefully', async function() {
    mockRecognitionInstance.start = jest.fn(function() { throw new Error('start fail') });
    renderVoiceInput();
    fireEvent.click(screen.getByRole('button', { name: /start voice input/i }));
    await waitFor(function() { expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument() });
  });
});



