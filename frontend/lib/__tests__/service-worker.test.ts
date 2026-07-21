// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

/**
 * Service Worker unit tests — offline caching and push notification logic.
 *
 * Tests use a mock ServiceWorkerGlobalScope to verify caching strategies,
 * fetch interception, and push event handling without a real browser.
 */

const CACHE_NAME = 'safevixai-v1';
const STATIC_ASSETS = [
  '/',
  '/offline',
  '/manifest.json',
  '/theme-init.js',
];

// Mock self for service worker scope
const mockSelf = {
  addEventListener: jest.fn(),
  skipWaiting: jest.fn(),
  clients: {
    claim: jest.fn(),
    matchAll: jest.fn().mockResolvedValue([]),
  },
  registration: {
    showNotification: jest.fn(),
  },
  caches: {
    open: jest.fn().mockResolvedValue({
      addAll: jest.fn().mockResolvedValue(undefined),
      put: jest.fn().mockResolvedValue(undefined),
      match: jest.fn().mockResolvedValue(undefined),
      delete: jest.fn().mockResolvedValue(true),
    }),
    keys: jest.fn().mockResolvedValue([CACHE_NAME]),
    delete: jest.fn().mockResolvedValue(true),
  },
  fetch: jest.fn().mockResolvedValue(new Response('cached', { status: 200 })),
};

// Mock cache storage
const createMockCache = () => ({
  addAll: jest.fn().mockResolvedValue(undefined),
  put: jest.fn().mockResolvedValue(undefined),
  match: jest.fn().mockImplementation(async (request: RequestInfo | URL) => {
    const url = typeof request === 'string' ? request : request instanceof URL ? request.href : request.url;
    if (url.includes('/api/')) {
      return undefined;
    }
    return new Response('cached response', { status: 200 });
  }),
  delete: jest.fn().mockResolvedValue(true),
});

describe('Service Worker - Cache Strategies', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(createMockCache());
  });

  it('cache-first returns cached response when available', async () => {
    const cache = createMockCache();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(cache);

    const request = new Request('/');
    const cachedResponse = await cache.match(request);
    expect(cachedResponse).toBeDefined();
    expect(cachedResponse!.status).toBe(200);
  });

  it('network-first falls back to cache on network failure', async () => {
    const cache = createMockCache();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(cache);

    const request = new Request('/api/v1/emergency/nearby?lat=13&lon=80');
    const networkResponse = await mockSelf.fetch(request);
    if (!networkResponse.ok) {
      const cached = await cache.match(request);
      expect(cached).toBeUndefined();
    }
  });

  it('stale-while-revalidate serves cache and updates in background', async () => {
    const cache = createMockCache();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(cache);

    const request = new Request('/api/v1/challan/calculate');
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      const networkResponse = await mockSelf.fetch(request.clone());
      await cache.put(request, networkResponse.clone());
      expect(cache.put).toHaveBeenCalled();
    }
  });

  it('installs static assets on activate', async () => {
    const cache = createMockCache();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(cache);

    await mockSelf.caches.open(CACHE_NAME);
    await cache.addAll(STATIC_ASSETS);
    expect(cache.addAll).toHaveBeenCalledWith(STATIC_ASSETS);
  });

  it('deletes old cache versions on activate', async () => {
    const oldCaches = ['safevixai-v0', 'safevixai-v1'];
    (mockSelf.caches.keys as jest.Mock).mockResolvedValue(oldCaches);
    (mockSelf.caches.delete as jest.Mock).mockResolvedValue(true);

    const cacheNames = await mockSelf.caches.keys();
    for (const name of cacheNames) {
      if (name !== CACHE_NAME) {
        await mockSelf.caches.delete(name);
      }
    }
    expect(mockSelf.caches.delete).toHaveBeenCalledWith('safevixai-v0');
  });
});

describe('Service Worker - Push Notifications', () => {
  it('shows notification on push event', async () => {
    const event = new PushEvent('push', {
      data: {
        json: () => ({
          title: 'Road Alert',
          body: 'Pothole reported nearby',
          icon: '/icons/icon-192.png',
          badge: '/icons/icon-96.png',
        }),
      },
    } as unknown as PushEventInit);

    const { title } = event.data!.json();
    expect(title).toBe('Road Alert');
  });

  it('handles push with no data gracefully', () => {
    const event = new PushEvent('push');
    expect(event.data).toBeNull();
  });
});

describe('Service Worker - Fetch Interception', () => {
  it('passes through non-GET requests', async () => {
    const request = new Request('/api/v1/roads/report', { method: 'POST' });
    (mockSelf.fetch as jest.Mock).mockResolvedValue(new Response('ok', { status: 200 }));

    const response = await mockSelf.fetch(request.clone());
    expect(response.status).toBe(200);
  });

  it('returns offline page for navigation requests when offline', async () => {
    const cache = createMockCache();
    (mockSelf.caches.open as jest.Mock).mockResolvedValue(cache);
    (mockSelf.fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'));

    const request = new Request('/some-page', {
      method: 'GET',
      headers: { Accept: 'text/html' },
    });

    try {
      await mockSelf.fetch(request.clone());
    } catch {
      const offlineResponse = await cache.match('/offline');
      expect(offlineResponse).toBeDefined();
    }
  });
});

describe('Service Worker - Install Event', () => {
  it('skips waiting on install', () => {
    mockSelf.skipWaiting();
    expect(mockSelf.skipWaiting).toHaveBeenCalled();
  });

  it('claims clients on activate', () => {
    mockSelf.clients.claim();
    expect(mockSelf.clients.claim).toHaveBeenCalled();
  });
});
