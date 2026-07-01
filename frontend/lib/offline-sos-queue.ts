// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { PUBLIC_API_BASE_URL } from './public-env';
import { OFFLINE_SOS_SYNC_TIMEOUT_MS } from './safety-constants';

interface SOSData {
  id?: number;
  apiUrl?: string;
  lat: number;
  lon: number;
  userId?: string;
  timestamp: string;
}

interface RoadReportQueueData {
  id?: number;
  apiUrl?: string;
  lat: number;
  lon: number;
  issue_type: string;
  severity: number;
  description?: string;
  photo?: Blob;
  photoName?: string;
  timestamp: string;
}

interface SafeVixDB extends DBSchema {
  'sos-queue': {
    key: number;
    value: SOSData;
    indexes: { 'by-timestamp': string };
  };
  'road-report-queue': {
    key: number;
    value: RoadReportQueueData;
    indexes: { 'by-timestamp': string };
  };
}

interface SyncManagerRegistration extends ServiceWorkerRegistration {
  sync?: {
    register(tag: string): Promise<void>;
  };
}

let dbPromise: Promise<IDBPDatabase<SafeVixDB> | null> | null = null;
let indexedDbUnavailable = false;
let offlineSyncListenersRegistered = false;
const SOS_FALLBACK_KEY = 'safevix:sos-queue:fallback';
const ROAD_REPORT_FALLBACK_KEY = 'safevix:road-report-queue:fallback';

function readFallbackQueue<T>(key: string): T[] {
  /* istanbul ignore next */
if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(window.sessionStorage.getItem(key) || '[]') as T[];
  } catch {
    window.sessionStorage.removeItem(key);
    return [];
  }
}

function writeFallbackQueue<T>(key: string, items: T[]): void {
  /* istanbul ignore next */
if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(key, JSON.stringify(items));
  } catch {
    // Private mode can block all storage. Keep the app alive and let callers show UX.
  }
}

async function ensureServiceWorkerRegistration(): Promise<void> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;
  try {
    await navigator.serviceWorker.register('/sw.js');
  } catch {
    return;
  }
}

/**
 * Initializes the IndexedDB for storing offline SOS requests.
 */
export function initDB() {
  /* istanbul ignore next */
if (typeof window === 'undefined') return null;
  if (indexedDbUnavailable) return null;
  
  if (!dbPromise) {
    dbPromise = openDB<SafeVixDB>('safevix-offline-db', 2, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('sos-queue')) {
          const store = db.createObjectStore('sos-queue', {
            keyPath: 'id',
            autoIncrement: true,
          });
          store.createIndex('by-timestamp', 'timestamp');
        }
        if (!db.objectStoreNames.contains('road-report-queue')) {
          const store = db.createObjectStore('road-report-queue', {
            keyPath: 'id',
            autoIncrement: true,
          });
          store.createIndex('by-timestamp', 'timestamp');
        }
      },
    }).catch(() => {
      indexedDbUnavailable = true;
      dbPromise = null;
      return null;
    });
  }
  return dbPromise;
}

/**
 * Adds an SOS request to the offline queue.
 * Should be called when navigator.onLine is false or fetch throws a Network Error.
 */
export async function enqueueSOS(data: Omit<SOSData, 'timestamp'>): Promise<void> {
  const db = await initDB();
  const sosEntry: SOSData = {
    ...data,
    apiUrl: PUBLIC_API_BASE_URL,
    timestamp: new Date().toISOString(),
  };

  if (!db) {
    const items = readFallbackQueue<SOSData>(SOS_FALLBACK_KEY);
    items.push(sosEntry);
    writeFallbackQueue(SOS_FALLBACK_KEY, items);
    return;
  }

  await db.add('sos-queue', sosEntry);
  
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const registration = (await navigator.serviceWorker.ready) as SyncManagerRegistration;
      await registration.sync?.register('sos-queue-flush');
    } catch {
      return;
    }
  }
}

export async function enqueueRoadReport(
  data: Omit<RoadReportQueueData, 'timestamp' | 'apiUrl'>
): Promise<void> {
  const db = await initDB();
  if (!db) {
    const items = readFallbackQueue<Omit<RoadReportQueueData, 'photo'>>(ROAD_REPORT_FALLBACK_KEY);
    items.push({
      lat: data.lat,
      lon: data.lon,
      issue_type: data.issue_type,
      severity: data.severity,
      description: data.description,
      apiUrl: PUBLIC_API_BASE_URL,
      timestamp: new Date().toISOString(),
    });
    writeFallbackQueue(ROAD_REPORT_FALLBACK_KEY, items);
    return;
  }

  await db.add('road-report-queue', {
    ...data,
    apiUrl: PUBLIC_API_BASE_URL,
    timestamp: new Date().toISOString(),
  });

  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const registration = (await navigator.serviceWorker.ready) as SyncManagerRegistration;
      await registration.sync?.register('road-report-queue-flush');
    } catch {
      return;
    }
  }
}

/**
 * Syncs all queued SOS requests to the backend.
 * Called automatically when connection is restored.
 *
 * C5 FIX: Uses per-item transactions instead of a single batch transaction.
 * Each item is deleted only after its sync is confirmed, preventing data loss
 * if sync fails partway through the queue.
 */
export async function syncOfflineSOSQueue(): Promise<void> {
  if (/* istanbul ignore next */
typeof window !== 'undefined' && !navigator.onLine) {
    return;
  }

  const db = await initDB();
  if (!db) {
    await syncFallbackSOSQueue();
    return;
  }

  // Read items in a readonly transaction first
  const readTx = db.transaction('sos-queue', 'readonly');
  const allKeys = await readTx.store.getAllKeys();
  const allItems = await readTx.store.getAll();
  await readTx.done;

  if (allItems.length === 0) {
    return;
  }

  const API_URL = PUBLIC_API_BASE_URL;

  for (let i = 0; i < allItems.length; i++) {
    const item = allItems[i];
    const key = allKeys[i];

    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), OFFLINE_SOS_SYNC_TIMEOUT_MS);
      const res = await fetch(`${API_URL}/api/v1/emergency/sos?lat=${item.lat}&lon=${item.lon}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
      });
      window.clearTimeout(timeout);

      if (res.ok) {
        // Delete in its own transaction — atomic per item
        const deleteTx = db.transaction('sos-queue', 'readwrite');
        await deleteTx.store.delete(key);
        await deleteTx.done;
      } else {
        // Server rejected — stop trying remaining items
        break;
      }
    } catch {
      // Network error — stop trying, will retry on next online event
      break;
    }
  }
  await syncFallbackSOSQueue();
}

/**
 * C5 FIX: Per-item transaction for road report sync as well.
 */
export async function syncOfflineRoadReportQueue(): Promise<void> {
  if (/* istanbul ignore next */
typeof window !== 'undefined' && !navigator.onLine) {
    return;
  }

  const db = await initDB();
  if (!db) {
    await syncFallbackRoadReportQueue();
    return;
  }

  // Read items in a readonly transaction first
  const readTx = db.transaction('road-report-queue', 'readonly');
  const allKeys = await readTx.store.getAllKeys();
  const allItems = await readTx.store.getAll();
  await readTx.done;

  if (allItems.length === 0) {
    return;
  }

  for (let i = 0; i < allItems.length; i += 1) {
    const item = allItems[i];
    const key = allKeys[i];
    const apiUrl = item.apiUrl ?? PUBLIC_API_BASE_URL;

    try {
      const formData = new FormData();
      formData.append('lat', String(item.lat));
      formData.append('lon', String(item.lon));
      formData.append('issue_type', item.issue_type);
      formData.append('severity', String(item.severity));
      if (item.description?.trim()) {
        formData.append('description', item.description.trim());
      }
      if (item.photo) {
        formData.append('photo', item.photo, item.photoName ?? 'road-report.webp');
      }

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), OFFLINE_SOS_SYNC_TIMEOUT_MS);
      const res = await fetch(`${apiUrl.replace(/\/+$/, '')}/api/v1/roads/report`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      window.clearTimeout(timeout);

      if (res.ok) {
        // Delete in its own transaction — atomic per item
        const deleteTx = db.transaction('road-report-queue', 'readwrite');
        await deleteTx.store.delete(key);
        await deleteTx.done;
      } else {
        break;
      }
    } catch {
      break;
    }
  }
  await syncFallbackRoadReportQueue();
}

async function syncFallbackSOSQueue(): Promise<void> {
  const items = readFallbackQueue<SOSData>(SOS_FALLBACK_KEY);
  if (items.length === 0) return;

  const remaining: SOSData[] = [];
  for (const item of items) {
    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), OFFLINE_SOS_SYNC_TIMEOUT_MS);
      const res = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/emergency/sos?lat=${item.lat}&lon=${item.lon}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
      });
      window.clearTimeout(timeout);
      if (!res.ok) remaining.push(item);
    } catch {
      remaining.push(item);
    }
  }
  writeFallbackQueue(SOS_FALLBACK_KEY, remaining);
}

async function syncFallbackRoadReportQueue(): Promise<void> {
  const items = readFallbackQueue<Omit<RoadReportQueueData, 'photo'>>(ROAD_REPORT_FALLBACK_KEY);
  if (items.length === 0) return;

  const remaining: Omit<RoadReportQueueData, 'photo'>[] = [];
  for (const item of items) {
    try {
      const formData = new FormData();
      formData.append('lat', String(item.lat));
      formData.append('lon', String(item.lon));
      formData.append('issue_type', item.issue_type);
      formData.append('severity', String(item.severity));
      if (item.description?.trim()) formData.append('description', item.description.trim());

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), OFFLINE_SOS_SYNC_TIMEOUT_MS);
      const res = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/roads/report`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      window.clearTimeout(timeout);
      if (!res.ok) remaining.push(item);
    } catch {
      remaining.push(item);
    }
  }
  writeFallbackQueue(ROAD_REPORT_FALLBACK_KEY, remaining);
}

/**
 * Attaches event listeners to sync automatically when the network returns.
 * Should be called once in the root App or Layout component.
 */
export function registerOfflineSyncListeners() {
  if (/* istanbul ignore next */
typeof window !== 'undefined' && !offlineSyncListenersRegistered) {
    void ensureServiceWorkerRegistration();
    window.addEventListener('online', () => {
      void syncOfflineSOSQueue();
      void syncOfflineRoadReportQueue();
    });
    offlineSyncListenersRegistered = true;
  }
}
