// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

const mockRecords: Array<Record<string, unknown>> = [];

const mockStore = {
  getAllKeys: jest.fn(async () => mockRecords.map((record) => record.id as number)),
  getAll: jest.fn(async () => [...mockRecords]),
  delete: jest.fn(async (key: number) => {
    const index = mockRecords.findIndex((record) => record.id === key);
    if (index >= 0) {
      mockRecords.splice(index, 1);
    }
  }),
};

const mockDb = {
  add: jest.fn(async (_storeName: string, value: Record<string, unknown>) => {
    mockRecords.push({ ...value, id: mockRecords.length + 1 });
  }),
  transaction: jest.fn(() => ({
    objectStore: () => mockStore,
    store: mockStore,
    done: Promise.resolve(),
  })),
};

const mockOpenDB = jest.fn(async () => mockDb);

jest.mock('idb', () => ({
  openDB: () => mockOpenDB(),
}));

jest.mock('../public-env', () => ({
  PUBLIC_API_BASE_URL: 'https://api.safevix.test',
}));

jest.mock('../safety-constants', () => ({
  OFFLINE_SOS_SYNC_TIMEOUT_MS: 5000,
}));

import { enqueueSOS, syncOfflineSOSQueue } from '../offline-sos-queue';

describe('offline SOS queue', function() {
  beforeEach(function() {
    mockRecords.length = 0;
    jest.clearAllMocks();
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    global.fetch = jest.fn(async () => ({ ok: true })) as jest.Mock;
  });

  it('stores SOS records with the configured public API URL', async function() {
    await enqueueSOS({ lat: 13.0827, lon: 80.2707 });

    expect(mockDb.add).toHaveBeenCalledWith(
      'sos-queue',
      expect.objectContaining({
        apiUrl: 'https://api.safevix.test',
        lat: 13.0827,
        lon: 80.2707,
        timestamp: expect.any(String),
      })
    );
  });

  it('replays queued SOS records with POST and removes successful records', async function() {
    await enqueueSOS({ lat: 13.0827, lon: 80.2707 });

    await syncOfflineSOSQueue();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.safevix.test/api/v1/emergency/sos?lat=13.0827&lon=80.2707',
      expect.objectContaining({ method: 'POST' })
    );
    expect(mockRecords).toHaveLength(0);
  });

  it('queues SOS when offline and flushes when online', async function() {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });

    await enqueueSOS({ lat: 13.0827, lon: 80.2707 });

    expect(mockRecords).toHaveLength(1);

    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    await syncOfflineSOSQueue();

    expect(mockRecords).toHaveLength(0);
  });

  it('retries failed flush on next online event', async function() {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });

    await enqueueSOS({ lat: 13.0827, lon: 80.2707 });
    await syncOfflineSOSQueue();

    expect(mockRecords).toHaveLength(1);

    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });
    await syncOfflineSOSQueue();

    expect(mockRecords).toHaveLength(0);
  });

});


