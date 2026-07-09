// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

type LogDetail = unknown;

const isDevelopment = process.env.NODE_ENV !== 'production';
/* istanbul ignore next */const sentryAvailable = typeof window !== 'undefined' && (window as any).Sentry;

// Batched error reporting — accumulate errors and flush on threshold
interface ErrorRecord {
  level: 'error' | 'warn';
  message: string;
  detail?: LogDetail;
  timestamp: number;
}

const errorQueue: ErrorRecord[] = [];
const BATCH_FLUSH_THRESHOLD = 5;
const BATCH_FLUSH_INTERVAL_MS = 60_000;
let batchTimer: ReturnType<typeof setInterval> | null = null;

function startBatchTimer() {
  if (batchTimer) return;
  batchTimer = setInterval(() => {
    flushErrorBatch();
  }, BATCH_FLUSH_INTERVAL_MS);
}

function flushErrorBatch() {
  if (errorQueue.length === 0) return;
  const batch = errorQueue.splice(0, errorQueue.length);
  try {
    const posthog = (globalThis as any).posthog;
    if (posthog && posthog.capture) {
      posthog.capture('client_error_batch', {
        count: batch.length,
        errors: batch.map((r) => ({
          level: r.level,
          message: r.message,
          detail: r.detail,
          timestamp: new Date(r.timestamp).toISOString(),
        })),
      });
    }
  } catch {
    // PostHog unavailable — batch silently dropped
  }
}

function enqueue(level: 'error' | 'warn', message: string, detail?: LogDetail) {
  errorQueue.push({ level, message, detail, timestamp: Date.now() });
  startBatchTimer();
  if (errorQueue.length >= BATCH_FLUSH_THRESHOLD) {
    flushErrorBatch();
  }
}

function emit(level: 'error' | 'warn', message: string, detail?: LogDetail) {
  if (typeof globalThis === 'undefined') return;

  const sink = globalThis['console'];

  // Enqueue for batched reporting
  if (!isDevelopment) {
    enqueue(level, message, detail);
  }

  // Send errors to Sentry in production
  if (!isDevelopment && sentryAvailable) {
    try {
      const sentry = (window as any).Sentry;
      if (level === 'error') {
        sentry.captureException(detail instanceof Error ? detail : new Error(message), {
          extra: { detail, message },
          level: 'error',
        });
      } else if (level === 'warn') {
        sentry.captureMessage(message, {
          level: 'warning',
          extra: { detail },
        });
      }
    } catch {
      // Sentry not initialized — fall through to console
    }
  }

  // Always log to console in development
  if (isDevelopment && sink) {
    if (detail === undefined) {
      sink[level](message);
    } else {
      sink[level](message, detail);
    }
  }
}

// Flush on page unload
/* istanbul ignore next */if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    flushErrorBatch();
    if (batchTimer) clearInterval(batchTimer);
  });
}

export function logClientError(message: string, detail?: LogDetail) {
  emit('error', message, detail);
}

export function logClientWarning(message: string, detail?: LogDetail) {
  emit('warn', message, detail);
}

/** Immediately flush any queued error batch (useful before critical navigation) */
export function flushErrors() {
  flushErrorBatch();
}
