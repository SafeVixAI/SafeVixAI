// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import axios from 'axios';
import { toast } from 'sonner';
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';
import { useAppStore } from '@/lib/store';

export const BASE_URL = PUBLIC_API_BASE_URL;
export const CHATBOT_URL = PUBLIC_CHATBOT_BASE_URL;

export type RoadIssueStatus =
  | 'open'
  | 'acknowledged'
  | 'in_progress'
  | 'resolved'
  | 'rejected';

// In-memory CSRF token (httponly cookie is not readable from JS)
let _csrfToken: string | null = null;

/** Fetch CSRF token from the dedicated endpoint (sets httponly cookie + returns token in body) */
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/auth/csrf-token`, {
      credentials: 'include',
    });
    if (!res.ok) return null;
    const data = await res.json();
    _csrfToken = data.csrf_token ?? null;
    return _csrfToken;
  } catch {
    return null;
  }
}

/** Override the in-memory CSRF token (e.g. after SSR hydration) */
export function setCsrfToken(token: string | null) {
  _csrfToken = token;
}

export const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  withCredentials: true,
});

client.interceptors.request.use((config) => {
  if (_csrfToken) {
    config.headers['X-CSRF-Token'] = _csrfToken;
  }
  const token = useAppStore.getState().authToken;
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  const preferredLang = useAppStore.getState().userProfile.preferredLanguage || 'en';
  config.headers['Accept-Language'] = preferredLang;
  return config;
});

function _addWarmingInterceptors(axiosInstance: ReturnType<typeof axios.create>) {
  axiosInstance.interceptors.request.use((config) => {
    // Only start warming timer on the very first attempt
    const cfg = config as any;
    if (!cfg._warmingTimer && !cfg._retryCount) {
      const timer = setTimeout(() => {
        useAppStore.getState().setServerWarming(true);
      }, 5000);
      cfg._warmingTimer = timer;
    }
    return config;
  });

  axiosInstance.interceptors.response.use(
    (response) => {
      const timer = (response.config as any)._warmingTimer;
      if (timer) clearTimeout(timer);
      useAppStore.getState().setServerWarming(false);
      return response;
    },
    (error) => {
      const config = error.config as any;
      const isNetworkError = !error.response;
      const isServerError = error.response?.status >= 500;
      const willRetry = config && (config._retryCount ?? 0) < 3 && (isNetworkError || isServerError);
      
      // ONLY clear warming state if we are giving up
      if (!willRetry) {
        const timer = config?._warmingTimer;
        if (timer) clearTimeout(timer);
        useAppStore.getState().setServerWarming(false);
      }
      return Promise.reject(error);
    }
  );
}

_addWarmingInterceptors(client);

// S20/F9: Exponential-backoff retry interceptor (up to 3 retries, 5s/10s/20s delays).
// Delays are tuned for Render free-tier cold starts (~30-50s spin-up).
function _withRetry(axiosInstance: ReturnType<typeof axios.create>, maxRetries = 3) {
  axiosInstance.interceptors.response.use(
    (res) => res,
    async (error) => {
      const config = error.config as (typeof error.config) & { _retryCount?: number };
      if (!config) return Promise.reject(error);

      config._retryCount = (config._retryCount ?? 0);
      const isNetworkError = !error.response;
      const isServerError = error.response?.status >= 500;
      if (config._retryCount >= maxRetries || (!isNetworkError && !isServerError)) {
        return Promise.reject(error);
      }
      config._retryCount += 1;
      // 5s → 10s → 20s  (total ≈ 35s, covers Render cold start)
      const delayMs = 5_000 * 2 ** (config._retryCount - 1);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return axiosInstance(config);
    }
  );
}
_withRetry(client);

// ── Chatbot Client ──

export const chatbotClient = axios.create({
  baseURL: CHATBOT_URL,
  timeout: 60_000,
  withCredentials: true,
});

chatbotClient.interceptors.request.use((config) => {
  if (_csrfToken) {
    config.headers['X-CSRF-Token'] = _csrfToken;
  }
  const token = useAppStore.getState().authToken;
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  const preferredLang = useAppStore.getState().userProfile.preferredLanguage || 'en';
  config.headers['Accept-Language'] = preferredLang;
  return config;
});
_addWarmingInterceptors(chatbotClient);
_withRetry(chatbotClient);

// ── ApiResponse<T> unwrapping interceptor ──
// Backend wraps all 2xx JSON responses in {success, data, error, timestamp}
// envelope. This interceptor unwraps it so downstream code gets the raw payload.
function _unwrapApiResponse(axiosInstance: ReturnType<typeof axios.create>) {
  axiosInstance.interceptors.response.use(
    (res) => {
      const body = res.data as Record<string, unknown> | undefined;
      if (body && typeof body === 'object' && 'success' in body && 'data' in body) {
        res.data = body.data;
      }
      return res;
    },
    (error) => {
      if (axios.isAxiosError(error) && error.response?.data) {
        const errBody = error.response.data as Record<string, unknown>;
        if (errBody && typeof errBody === 'object' && 'error' in errBody) {
          error.response.data = errBody;
        }
      }
      return Promise.reject(error);
    }
  );
}
_unwrapApiResponse(client);
_unwrapApiResponse(chatbotClient);

// ── Shared API error extraction ──

export function extractApiError(err: unknown): { message: string; code?: string; status?: number; details?: unknown } {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status;
    const data = err.response?.data as Record<string, unknown> | undefined;
    const detail = typeof data?.detail === 'string'
      ? data.detail
      : Array.isArray(data?.detail)
        ? (data.detail as Array<{ msg?: string; loc?: string[] }>).map(d => d.msg).filter(Boolean).join('; ')
        : undefined;
    return {
      message: detail || err.message || 'Something went wrong',
      code: data?.error_code as string | undefined,
      status,
      details: data,
    };
  }
  if (err instanceof Error) return { message: err.message || 'An unexpected error occurred' };
  return { message: 'An unexpected error occurred' };
}

// ── Global error toast interceptor ──
function _addGlobalErrorToastInterceptor(axiosInstance: ReturnType<typeof axios.create>) {
  axiosInstance.interceptors.response.use(
    (res) => res,
    (error) => {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        const isNetworkError = !error.response;
        const isWarming = useAppStore.getState().serverWarming;
        // Don't show network error toast when the warming banner is already visible
        // — the user already knows the server is waking up.
        if (isNetworkError && !isWarming) {
          toast.error('Network error — check your connection', { id: 'api-network-error', duration: 4000 });
        } else if (status && status >= 500) {
          const { message } = extractApiError(error);
          toast.error(message.length > 80 ? message.slice(0, 80) + '…' : message, { duration: 4000 });
        }
      }
      return Promise.reject(error);
    }
  );
}
_addGlobalErrorToastInterceptor(client);
_addGlobalErrorToastInterceptor(chatbotClient);

// ── Retrying indicator interceptor ──
let _retryCountGlobal = 0;
let _retryingToastId: string | number | null = null;

function _addRetryIndicatorInterceptor(axiosInstance: ReturnType<typeof axios.create>) {
  axiosInstance.interceptors.response.use(
    (res) => {
      if (_retryingToastId) { toast.dismiss(_retryingToastId); _retryingToastId = null; _retryCountGlobal = 0; }
      return res;
    },
    (error) => {
      const config = error.config as (typeof error.config) & { _retryCount?: number };
      const isWarming = useAppStore.getState().serverWarming;
      const isFinalFailure = config && (config._retryCount ?? 0) >= 3;
      
      // Don't show retrying toast when warming banner is already informing the user,
      // and definitely don't show it on the final failure!
      if (config?._retryCount && config._retryCount > 0 && !_retryingToastId && !isWarming && !isFinalFailure) {
        _retryingToastId = toast.info(`Retrying... (attempt ${config._retryCount}/3)`, {
          duration: 4000,
          id: 'retrying-indicator',
        });
      }
      return Promise.reject(error);
    }
  );
}
_addRetryIndicatorInterceptor(client);
_addRetryIndicatorInterceptor(chatbotClient);

export function csvParam(value?: string | string[]) {
  if (!value) return undefined;
  return Array.isArray(value) ? value.join(',') : value;
}
