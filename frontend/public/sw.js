// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// SafeVixAI Service Worker - offline cache plus queued SOS/report replay.

const CACHE_NAME = 'safevixai-v3';
const CRITICAL_API_CACHE = 'safevixai-critical-api-v1';
const OFFLINE_DATA_REFRESH_INTERVAL = 24 * 60 * 60 * 1000; // once per day
const TILE_LRU_DB = 'safevixai-tile-lru-v1';
const TILE_LRU_STORE = 'tileAccess';
// 1x1 transparent PNG tile placeholder used when map tile fetch fails offline.
const TRANSPARENT_TILE_PLACEHOLDER_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQABNjN9GQAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAA0lEQVQI12P4z8BQDwAEgAF/QualzQAAAABJRU5ErkJggg==';

function openTileLruDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(TILE_LRU_DB, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(TILE_LRU_STORE)) {
        db.createObjectStore(TILE_LRU_STORE, { keyPath: 'url' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function tileLruError(error, fallbackMessage) {
  if (error instanceof Error) return error;
  return new Error(fallbackMessage);
}

function logTileLruWarning(message, error) {
  console.warn(message, error instanceof Error ? error.message : error);
}

async function touchTileAccess(url) {
  const db = await openTileLruDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TILE_LRU_STORE, 'readwrite');
    tx.objectStore(TILE_LRU_STORE).put({ url, lastAccess: Date.now() });
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tileLruError(tx.error, `Tile LRU access write failed for ${url}`));
    };
  });
}

async function getAllTileAccessEntries() {
  const db = await openTileLruDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TILE_LRU_STORE, 'readonly');
    const req = tx.objectStore(TILE_LRU_STORE).getAll();
    req.onsuccess = () => {
      db.close();
      resolve(req.result || []);
    };
    req.onerror = () => {
      db.close();
      reject(tileLruError(req.error, 'Tile LRU access read failed'));
    };
  });
}

async function removeTileAccess(url) {
  const db = await openTileLruDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(TILE_LRU_STORE, 'readwrite');
    tx.objectStore(TILE_LRU_STORE).delete(url);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tileLruError(tx.error, `Tile LRU access delete failed for ${url}`));
    };
  });
}

async function evictLeastRecentlyUsedTiles(cache, maxEntries) {
  const entries = await getAllTileAccessEntries();
  if (entries.length <= maxEntries) return;

  entries.sort((a, b) => a.lastAccess - b.lastAccess);
  const excess = entries.length - maxEntries;
  const toDelete = entries.slice(0, excess);

  await Promise.all(
    toDelete.map(async ({ url }) => {
      await cache.delete(url);
      await removeTileAccess(url);
    })
  );
}

const OFFLINE_DATA_URLS = [
  '/offline-data/first-aid.json',
  '/offline-data/india-emergency.geojson',
  '/offline-data/india-emergency.geojson.gz',
  '/offline-data/violations.csv',
  '/offline-data/state_overrides.csv',
  '/offline-data/accidents_summary.json',
  '/offline-data/blackspot_seed.csv',
  '/offline-data/nh_blackspots.csv',
  '/offline-data/chennai.json',
  '/offline-data/municipalities_bundle.json',
  '/offline-data/civic_features_summary.json',
];

const DUCKDB_WASM = [
  '/duckdb/duckdb-mvp.wasm',
  '/duckdb/duckdb-eh.wasm',
  '/duckdb/duckdb-browser-mvp.worker.js',
  '/duckdb/duckdb-browser-eh.worker.js',
  '/duckdb/duckdb-browser-coi.worker.js',
  '/duckdb/duckdb-browser-coi.pthread.worker.js',
];

const PWA_ASSETS = [
  '/icons/icon-72x72.png',
  '/icons/icon-96x96.png',
  '/icons/icon-128x128.png',
  '/icons/icon-144x144.png',
  '/icons/icon-152x152.png',
  '/icons/icon-192x192.png',
  '/icons/icon-384x384.png',
  '/icons/icon-512x512.png',
  '/theme-init.js',
  '/manifest.json',
];

const STATIC_ASSETS = [
  '/',
  '/offline',
  '/sos',
  '/first-aid',
  '/emergency',
  '/offline-data/first-aid.json',
  '/offline-data/india-emergency.geojson',
  ...DUCKDB_WASM,
  ...PWA_ASSETS,
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([...OFFLINE_DATA_URLS, ...STATIC_ASSETS].filter(
        (url, i, arr) => arr.indexOf(url) === i
      )).catch(() => undefined);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  const KEEP_CACHES = [CACHE_NAME, CRITICAL_API_CACHE, 'safevixai-map-tiles-v1'];
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(
      names.filter((name) => !KEEP_CACHES.includes(name)).map((name) => caches.delete(name))
    );

    if ('periodicSync' in self.registration) {
      try {
        await self.registration.periodicSync.register('offline-data-refresh', {
          minInterval: OFFLINE_DATA_REFRESH_INTERVAL,
        });
      } catch { /* periodic sync not supported */ }
    }
  })());
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith('/api/')) {
    // Critical API endpoints that should work offline
    const criticalApis = ['/api/v1/emergency/numbers'];
    if (criticalApis.some((path) => url.pathname === path)) {
      event.respondWith(
        fetch(event.request)
          .then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches.open(CRITICAL_API_CACHE).then((cache) => cache.put(event.request, clone));
            }
            return response;
          })
          .catch(async () => {
            const cached = await caches.match(event.request);
            if (cached) return cached;
            return new Response(JSON.stringify({ error: 'offline' }), { status: 503, headers: { 'Content-Type': 'application/json' } });
          })
      );
      return;
    }
    return;
  }

  if (url.pathname.startsWith('/offline-data/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }

  // ── Map Tile Runtime Caching ──
  // Cache tiles from MapLibre, OpenStreetMap, OpenFreeMap, MapTiler, and Google Maps
  // to enable offline base map rendering. Uses a dedicated cache with LRU eviction.
  const MAP_TILE_CACHE = 'safevixai-map-tiles-v1';
  const MAX_TILE_ENTRIES = 500;
  const TILE_DOMAINS = [
    'tile.openstreetmap.org',
    'tiles.openfreemap.org',
    'demotiles.maplibre.org',
    'tiles.stadiamaps.com',
    'api.maptiler.com',
    'mt1.google.com',
  ];

  if (TILE_DOMAINS.some((domain) => url.hostname.endsWith(domain))) {
    event.respondWith(
      caches.open(MAP_TILE_CACHE).then(async (cache) => {
        const cached = await cache.match(event.request);
        if (cached) {
          event.waitUntil(
            touchTileAccess(event.request.url).catch((error) =>
              logTileLruWarning('Tile LRU touch failed for cached tile', error)
            )
          );
          return cached;
        }

        try {
          const response = await fetch(event.request);
          if (response.ok) {
            const clone = response.clone();
            await cache.put(event.request, clone);
            event.waitUntil((async () => {
              await touchTileAccess(event.request.url).catch((error) =>
                logTileLruWarning('Tile LRU touch failed for fetched tile', error)
              );

              // LRU eviction: keep the cache under MAX_TILE_ENTRIES using tracked access timestamps
              await evictLeastRecentlyUsedTiles(cache, MAX_TILE_ENTRIES).catch((error) =>
                logTileLruWarning('Tile LRU eviction failed', error)
              );
            })());
          }
          return response;
        } catch {
          // Offline: return a transparent 1x1 PNG tile placeholder
          return new Response(
            Uint8Array.from(atob(TRANSPARENT_TILE_PLACEHOLDER_BASE64), (c) => c.charCodeAt(0)),
            {
              status: 200,
              headers: { 'Content-Type': 'image/png', 'Cache-Control': 'no-store' },
            }
          );
        }
      })
    );
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(async () => {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        if (event.request.mode === 'navigate') {
          return caches.match('/offline');
        }
        return cached;
      })
  );
});

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Track successful PWA installation for analytics
self.addEventListener('appinstalled', () => {
  self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
    clients.forEach((client) => {
      client.postMessage({ type: 'APP_INSTALLED' });
    });
  });
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'sos-queue-flush') {
    event.waitUntil(flushSafeVixSosQueue());
  }
  if (event.tag === 'road-report-queue-flush') {
    event.waitUntil(flushSafeVixRoadReportQueue());
  }
});

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'offline-data-refresh') {
    event.waitUntil((async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        await Promise.all(
          OFFLINE_DATA_URLS.map(async (url) => {
            try {
              const res = await fetch(url, { cache: 'no-cache' });
              if (res.ok) await cache.put(url, res);
            } catch { /* skip failed individual fetches */ }
          })
        );
        const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
        clients.forEach((client) => client.postMessage({ type: 'OFFLINE_DATA_REFRESHED' }));
      } catch { /* periodic sync refresh failed */ }
    })());
  }
});

// P1-12: Each item is flushed in its own isolated transaction.
// If the network fails mid-loop, only successfully-sent items are deleted.
// The remaining items stay in the queue and are retried on the next sync event.
async function flushSafeVixSosQueue() {
  let db;
  try {
    db = await openSafeVixDb();

    // Read all pending items in a read-only transaction first
    const readTx = db.transaction('sos-queue', 'readonly');
    const readStore = readTx.objectStore('sos-queue');
    const [items, keys] = await Promise.all([
      idbRequest(readStore.getAll()),
      idbRequest(readStore.getAllKeys()),
    ]);

    for (let i = 0; i < items.length; i += 1) {
      const pendingSOS = items.at(i);
      const key = keys.at(i);
      const apiBase = pendingSOS.apiUrl;
      if (!apiBase) continue;

      // S19: Include Authorization header when available.
      // The authToken is stored in the IDB item at queue time (see offline-sos-queue.ts).
      const headers = { 'Content-Type': 'application/json' };
      if (pendingSOS.authToken) {
        headers['Authorization'] = `Bearer ${pendingSOS.authToken}`;
      }

      const resp = await fetch(
        `${apiBase.replace(/\/+$/, '')}/api/v1/emergency/sos?lat=${pendingSOS.lat}&lon=${pendingSOS.lon}`,
        { method: 'POST', headers }
      );

      if (!resp.ok) {
        console.error('SOS queue replay failed for item', {
          key,
          status: resp.status,
          statusText: resp.statusText,
        });
        await notifyClients({
          type: 'SOS_QUEUE_FLUSHED',
          success: false,
          error: `SOS replay failed (${resp.status} ${resp.statusText})`,
        });
        break; // Stop on first failure; remaining items stay in queue
      }

      // Delete only this successfully-sent item in its own atomic transaction
      const delTx = db.transaction('sos-queue', 'readwrite');
      await idbRequest(delTx.objectStore('sos-queue').delete(key));

      await notifyClients({ type: 'SOS_QUEUE_FLUSHED', success: true });
    }
  } catch (error) {
    await notifyClients({
      type: 'SOS_QUEUE_FLUSHED',
      success: false,
      error: error instanceof Error ? error.message : 'SOS queue replay failed',
    });
  } finally {
    db?.close?.();
  }
}

async function flushSafeVixRoadReportQueue() {
  let db;
  try {
    db = await openSafeVixDb();

    const readTx = db.transaction('road-report-queue', 'readonly');
    const readStore = readTx.objectStore('road-report-queue');
    const [items, keys] = await Promise.all([
      idbRequest(readStore.getAll()),
      idbRequest(readStore.getAllKeys()),
    ]);

    for (let i = 0; i < items.length; i += 1) {
      const pendingReport = items.at(i);
      const key = keys.at(i);
      const apiBase = pendingReport.apiUrl;
      if (!apiBase) continue;

      const formData = new FormData();
      formData.append('lat', String(pendingReport.lat));
      formData.append('lon', String(pendingReport.lon));
      formData.append('issue_type', pendingReport.issue_type);
      formData.append('severity', String(pendingReport.severity));
      if (pendingReport.description) {
        formData.append('description', pendingReport.description);
      }
      if (pendingReport.photo) {
        formData.append('photo', pendingReport.photo, pendingReport.photoName || 'road-report.webp');
      }

      const resp = await fetch(`${apiBase.replace(/\/+$/, '')}/api/v1/roads/report`, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) break;

      // Delete only this successfully-sent item atomically
      const delTx = db.transaction('road-report-queue', 'readwrite');
      await idbRequest(delTx.objectStore('road-report-queue').delete(key));

      await notifyClients({ type: 'ROAD_REPORT_QUEUE_FLUSHED', success: true });
    }
  } catch (error) {
    await notifyClients({
      type: 'ROAD_REPORT_QUEUE_FLUSHED',
      success: false,
      error: error instanceof Error ? error.message : 'Road report queue replay failed',
    });
  } finally {
    db?.close?.();
  }
}

// P1-15: Push Notification handler stub (audit H13)
// Displays a native OS notification and routes clicks to the correct page.
self.addEventListener('push', (event) => {
  let data = { title: 'SafeVixAI', body: 'You have a new safety alert.', url: '/sos' };
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72x72.png',
    tag: data.tag || 'safevixai-alert',
    renotify: true,
    data: { url: data.url || '/' },
    actions: [
      { action: 'open', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const targetUrl = event.notification.data?.url || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return self.clients.openWindow(targetUrl);
    })
  );
});

function openSafeVixDb() {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in self)) {
      reject(new Error('IndexedDB is unavailable in this browser context'));
      return;
    }
    const request = indexedDB.open('safevix-offline-db', 2);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('sos-queue')) {
        const store = db.createObjectStore('sos-queue', { keyPath: 'id', autoIncrement: true });
        store.createIndex('by-timestamp', 'timestamp');
      }
      if (!db.objectStoreNames.contains('road-report-queue')) {
        const store = db.createObjectStore('road-report-queue', { keyPath: 'id', autoIncrement: true });
        store.createIndex('by-timestamp', 'timestamp');
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function notifyClients(message) {
  const clients = await self.clients.matchAll();
  clients.forEach((client) => client.postMessage(message));
}

function idbRequest(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
