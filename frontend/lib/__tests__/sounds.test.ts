// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useAppStore } from '../store';
import { sounds } from '../sounds';

let mockOscillator: ReturnType<typeof createOscillatorObj>;
let mockGainNode: ReturnType<typeof createGainObj>;
let mockCreateOscillator: jest.Mock;
let mockCreateGain: jest.Mock;
let mockResume: jest.Mock;
let mockAudioContextCtor: jest.Mock;
let audioContextInstance: Record<string, any>;
let mocksCreated = false;

function createOscillatorObj() {
  return {
    connect: jest.fn(),
    frequency: { value: 0 },
    start: jest.fn(),
    stop: jest.fn(),
  };
}

function createGainObj() {
  return {
    connect: jest.fn(),
    gain: {
      setValueAtTime: jest.fn(),
      exponentialRampToValueAtTime: jest.fn(),
    },
  };
}

function initMocks(): void {
  if (mocksCreated) return;
  mockOscillator = createOscillatorObj();
  mockGainNode = createGainObj();
  mockResume = jest.fn();
  mockCreateOscillator = jest.fn(function () { return mockOscillator; });
  mockCreateGain = jest.fn(function () { return mockGainNode; });
  audioContextInstance = {
    createOscillator: mockCreateOscillator,
    createGain: mockCreateGain,
    destination: {},
    state: 'running',
    resume: mockResume,
    currentTime: 100,
  };
  mockAudioContextCtor = jest.fn(function () { return audioContextInstance; });
  mocksCreated = true;
}

function installWorkingAudioContext(): void {
  initMocks();
  (globalThis as any).AudioContext = mockAudioContextCtor;
}

function resetMockCalls(): void {
  if (!mocksCreated) return;
  mockOscillator.start.mockClear();
  mockOscillator.stop.mockClear();
  mockOscillator.connect.mockClear();
  mockOscillator.frequency.value = 0;
  mockGainNode.connect.mockClear();
  mockGainNode.gain.setValueAtTime.mockClear();
  mockGainNode.gain.exponentialRampToValueAtTime.mockClear();
  mockCreateOscillator.mockClear();
  mockCreateGain.mockClear();
  mockResume.mockClear();
  mockAudioContextCtor.mockClear();
  audioContextInstance.state = 'running';
}

beforeEach(function () {
  jest.useFakeTimers();
  useAppStore.setState({ soundsEnabled: true });
  resetMockCalls();
});

afterEach(function () {
  jest.useRealTimers();
  jest.restoreAllMocks();
});

describe('error handling', function () {
  // These tests run BEFORE any test creates the AudioContext (ctx stays null)

  it('does nothing when soundsEnabled is false', function () {
    useAppStore.setState({ soundsEnabled: false });
    expect(function () { sounds.sosSent(); }).not.toThrow();
    expect(function () { sounds.reportSent(); }).not.toThrow();
    expect(function () { sounds.error(); }).not.toThrow();
    expect(function () { sounds.countdown(10); }).not.toThrow();
    expect(function () { sounds.sev5Alert(); }).not.toThrow();
  });

  it('handles AudioContext being undefined on window', function () {
    (globalThis as any).AudioContext = undefined;
    expect(function () { sounds.sosSent(); }).not.toThrow();
    expect(function () { sounds.reportSent(); }).not.toThrow();
    expect(function () { sounds.error(); }).not.toThrow();
    expect(function () { sounds.countdown(10); }).not.toThrow();
    expect(function () { sounds.sev5Alert(); }).not.toThrow();
  });

  it('handles AudioContext constructor throwing', function () {
    (globalThis as any).AudioContext = jest.fn(function () {
      throw new Error('AudioContext unavailable');
    });
    expect(function () { sounds.sosSent(); }).not.toThrow();
    expect(function () { sounds.reportSent(); }).not.toThrow();
    expect(function () { sounds.error(); }).not.toThrow();
    expect(function () { sounds.countdown(10); }).not.toThrow();
    expect(function () { sounds.sev5Alert(); }).not.toThrow();
  });
});

describe('sound functions', function () {
  beforeEach(function () {
    installWorkingAudioContext();
  });

  it('sosSent plays 880Hz tone with 0.3s duration and 0.15 gain', function () {
    sounds.sosSent();
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(880);
    expect(mockOscillator.start).toHaveBeenCalledWith(100);
    expect(mockOscillator.stop).toHaveBeenCalledWith(100.3);
    expect(mockGainNode.gain.setValueAtTime).toHaveBeenCalledWith(0.15, 100);
    expect(mockGainNode.gain.exponentialRampToValueAtTime).toHaveBeenCalledWith(0.001, 100.3);
  });

  it('reportSent plays 440Hz tone with 0.2s duration and 0.08 gain', function () {
    sounds.reportSent();
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(440);
    expect(mockOscillator.start).toHaveBeenCalledWith(100);
    expect(mockOscillator.stop).toHaveBeenCalledWith(100.2);
    expect(mockGainNode.gain.setValueAtTime).toHaveBeenCalledWith(0.08, 100);
  });

  it('error plays 220Hz tone with 0.4s duration and 0.12 gain', function () {
    sounds.error();
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(220);
    expect(mockOscillator.start).toHaveBeenCalledWith(100);
    expect(mockOscillator.stop).toHaveBeenCalledWith(100.4);
  });

  it('countdown with seconds > 5 plays 440Hz tone', function () {
    sounds.countdown(10);
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(440);
  });

  it('countdown with seconds <= 5 plays 660Hz tone', function () {
    sounds.countdown(3);
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(660);
  });

  it('countdown with exactly 5 seconds plays 660Hz tone', function () {
    sounds.countdown(5);
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(660);
  });

  it('sev5Alert plays two tones with 120ms delay between them', function () {
    sounds.sev5Alert();
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
    expect(mockOscillator.frequency.value).toBe(987.77);
    expect(mockGainNode.gain.setValueAtTime).toHaveBeenCalledWith(0.15, 100);

    jest.advanceTimersByTime(120);

    expect(mockCreateOscillator).toHaveBeenCalledTimes(2);
    expect(mockOscillator.frequency.value).toBe(1318.51);
    expect(mockOscillator.start).toHaveBeenNthCalledWith(2, 100);
    expect(mockOscillator.stop).toHaveBeenNthCalledWith(2, 100.3);
  });
});

describe('AudioContext lifecycle', function () {
  beforeEach(function () {
    installWorkingAudioContext();
  });

  it('resumes AudioContext when it is suspended', function () {
    audioContextInstance.state = 'suspended';
    sounds.sosSent();
    expect(mockResume).toHaveBeenCalledTimes(1);
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
  });

  it('does not resume when AudioContext is already running', function () {
    sounds.sosSent();
    expect(mockResume).not.toHaveBeenCalled();
    expect(mockCreateOscillator).toHaveBeenCalledTimes(1);
  });

  it('reuses cached AudioContext on subsequent calls', function () {
    sounds.sosSent();
    const callsAfterFirst = mockAudioContextCtor.mock.calls.length;
    sounds.error();
    expect(mockAudioContextCtor.mock.calls.length).toBe(callsAfterFirst);
  });
});
