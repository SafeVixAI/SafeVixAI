import { PUBLIC_API_BASE_URL } from '@/lib/public-env';

export interface ProviderConfig {
  id?: string;
  providerName: string;
  displayName: string;
  apiKey?: string;
  apiKeyMasked?: string;
  baseUrl?: string;
  defaultModel?: string;
  isActive: boolean;
  priority: number;
  isCustom: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface BuiltinProvider {
  name: string;
  display: string;
  base_url: string;
  models: string[];
}

export interface ProviderTestResult {
  status: 'ok' | 'error';
  message: string;
  provider?: string;
  model?: string;
}

const BASE_URL = `${PUBLIC_API_BASE_URL}/api/v1/providers`;

async function handleResponse<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`HTTP ${resp.status}: ${body.slice(0, 200)}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export async function fetchBuiltinProviders(): Promise<BuiltinProvider[]> {
  const resp = await fetch(`${BASE_URL}/builtins`);
  return handleResponse<BuiltinProvider[]>(resp);
}

export async function fetchProviderConfigs(): Promise<ProviderConfig[]> {
  const resp = await fetch(BASE_URL);
  return handleResponse<ProviderConfig[]>(resp);
}

export async function createProviderConfig(data: Omit<ProviderConfig, 'id' | 'createdAt' | 'updatedAt'>): Promise<ProviderConfig> {
  const resp = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider_name: data.providerName,
      display_name: data.displayName,
      api_key: data.apiKey || undefined,
      base_url: data.baseUrl || undefined,
      default_model: data.defaultModel || undefined,
      is_active: data.isActive,
      priority: data.priority,
      is_custom: data.isCustom,
    }),
  });
  return handleResponse<ProviderConfig>(resp);
}

export async function updateProviderConfig(id: string, data: Partial<ProviderConfig>): Promise<ProviderConfig> {
  const resp = await fetch(`${BASE_URL}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      display_name: data.displayName,
      api_key: data.apiKey || undefined,
      base_url: data.baseUrl || undefined,
      default_model: data.defaultModel || undefined,
      is_active: data.isActive,
      priority: data.priority,
    }),
  });
  return handleResponse<ProviderConfig>(resp);
}

export async function deleteProviderConfig(id: string): Promise<void> {
  const resp = await fetch(`${BASE_URL}/${id}`, { method: 'DELETE' });
  return handleResponse<void>(resp);
}

export async function testProviderConnection(data: {
  providerName: string;
  apiKey: string;
  baseUrl?: string;
  model?: string;
}): Promise<ProviderTestResult> {
  const resp = await fetch(`${BASE_URL}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider_name: data.providerName,
      api_key: data.apiKey,
      base_url: data.baseUrl || undefined,
      model: data.model || undefined,
    }),
  });
  return handleResponse<ProviderTestResult>(resp);
}

export async function syncProvidersToChatbot(): Promise<{ synced: number; providers: string[] }> {
  const resp = await fetch(`${BASE_URL}/sync`, { method: 'POST' });
  return handleResponse<{ synced: number; providers: string[] }>(resp);
}
