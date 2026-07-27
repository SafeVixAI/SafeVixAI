// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

export interface QueuedUpdate {
  version: string;
  bundleData: Record<string, unknown>;
  queuedAt: number;
  status: 'queued' | 'applied' | 'failed';
}

export interface UpdateSWResponse {
  type: string;
  version: string;
  success: boolean;
  error?: string;
}

function getSW(): ServiceWorkerContainer | null {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return null;
  return navigator.serviceWorker;
}

export function queueOfflineUpdate(
  version: string,
  bundleData: Record<string, unknown> = {},
): Promise<UpdateSWResponse> {
  return new Promise((resolve) => {
    const sw = getSW();
    if (!sw) {
      resolve({ type: 'UPDATE_QUEUED', version, success: false, error: 'ServiceWorker not available' });
      return;
    }

    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'UPDATE_QUEUED' && event.data?.version === version) {
        sw.removeEventListener('message', handler);
        resolve(event.data as UpdateSWResponse);
      }
    };
    sw.addEventListener('message', handler);

    sw.ready.then((registration) => {
      registration.active?.postMessage({ type: 'QUEUE_OFFLINE_UPDATE', version, bundleData });
    });

    setTimeout(() => {
      sw.removeEventListener('message', handler);
      resolve({ type: 'UPDATE_QUEUED', version, success: false, error: 'Timeout waiting for SW response' });
    }, 10000);
  });
}

export function applyQueuedUpdate(version: string): Promise<UpdateSWResponse> {
  return new Promise((resolve) => {
    const sw = getSW();
    if (!sw) {
      resolve({ type: 'UPDATE_APPLIED', version, success: false, error: 'ServiceWorker not available' });
      return;
    }

    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'UPDATE_APPLIED' && event.data?.version === version) {
        sw.removeEventListener('message', handler);
        resolve(event.data as UpdateSWResponse);
      }
    };
    sw.addEventListener('message', handler);

    sw.ready.then((registration) => {
      registration.active?.postMessage({ type: 'APPLY_QUEUED_UPDATE', version });
    });

    setTimeout(() => {
      sw.removeEventListener('message', handler);
      resolve({ type: 'UPDATE_APPLIED', version, success: false, error: 'Timeout waiting for SW response' });
    }, 10000);
  });
}

export function cancelQueuedUpdate(version: string): Promise<UpdateSWResponse> {
  return new Promise((resolve) => {
    const sw = getSW();
    if (!sw) {
      resolve({ type: 'UPDATE_QUEUE_CANCELLED', version, success: false, error: 'ServiceWorker not available' });
      return;
    }

    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'UPDATE_QUEUE_CANCELLED' && event.data?.version === version) {
        sw.removeEventListener('message', handler);
        resolve(event.data as UpdateSWResponse);
      }
    };
    sw.addEventListener('message', handler);

    sw.ready.then((registration) => {
      registration.active?.postMessage({ type: 'CANCEL_QUEUED_UPDATE', version });
    });

    setTimeout(() => {
      sw.removeEventListener('message', handler);
      resolve({ type: 'UPDATE_QUEUE_CANCELLED', version, success: false, error: 'Timeout' });
    }, 10000);
  });
}
