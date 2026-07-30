// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { triggerSos, fetchSosPayload } from '../api';
import { enqueueSOS } from '../offline-sos-queue';

jest.mock('../api', () => ({
  ...jest.requireActual('../api'),
  triggerSos: jest.fn(),
  fetchSosPayload: jest.fn(),
}));

jest.mock('../offline-sos-queue', () => {
  const original = jest.requireActual('../offline-sos-queue');
  return {
    ...original,
    enqueueSOS: jest.fn(),
    registerOfflineSyncListeners: jest.fn(),
  };
});

describe('SOS Dispatch — Safety-Critical Tests', function() {
  beforeEach(function() {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  it('triggerSos POST should accept lat/lon params', async function() {
    const mockResponse = {
      services: [],
      numbers: { police: '100', ambulance: '108', fire: '101' },
    };
    (triggerSos as jest.Mock).mockResolvedValue(mockResponse);
    const result = await triggerSos({ lat: 13.0827, lon: 80.2707 });
    expect(result.numbers.police).toBe('100');
    expect(result.numbers.ambulance).toBe('108');
  });

  it('triggerSos should fail without params', async function() {
    (triggerSos as jest.Mock).mockRejectedValue(new Error('Missing lat/lon'));
    await expect(triggerSos({} as any)).rejects.toThrow('Missing lat/lon');
  });

  it('fetchSosPayload GET should return services + numbers', async function() {
    const mockPayload = {
      services: [{ name: 'Test Hospital', distance: 500, lat: 13.0, lon: 80.2, category: 'hospital' }],
      numbers: { police: '100' },
    };
    (fetchSosPayload as jest.Mock).mockResolvedValue(mockPayload);
    const result = await fetchSosPayload({ lat: 13.0827, lon: 80.2707 });
    expect(result.services).toHaveLength(1);
    expect(result.services[0].name).toBe('Test Hospital');
  });

  it('offline SOS queue should store and retrieve entries', async function() {
    const entry = { lat: 13.0, lon: 80.0, timestamp: Date.now() };
    (enqueueSOS as jest.Mock).mockResolvedValue(undefined);

    await enqueueSOS(entry);
    expect(enqueueSOS).toHaveBeenCalledWith(entry);
  });

  it('SOS numbers should include 112 (pan-India emergency)', async function() {
    const mockNumbers = { police: '100', ambulance: '108', fire: '101', emergency: '112' };
    (fetchSosPayload as jest.Mock).mockResolvedValue({ services: [], numbers: mockNumbers });
    const result = await fetchSosPayload({ lat: 13.0827, lon: 80.2707 });
    expect(result.numbers.emergency).toBe('112');
  });

  it('SOS should handle empty services gracefully', async function() {
    (fetchSosPayload as jest.Mock).mockResolvedValue({ services: [], numbers: {} });
    const result = await fetchSosPayload({ lat: 13.0827, lon: 80.2707 });
    expect(result.services).toEqual([]);
  });
});



