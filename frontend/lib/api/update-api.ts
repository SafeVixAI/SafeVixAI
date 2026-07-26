// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { client } from './client';

export interface VersionInfo {
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  channel: string;
  last_checked_at: string | null;
  uptime_seconds?: number;
}

export interface ReleaseSummary {
  id: number;
  version: string;
  channel: string;
  title: string;
  is_mandatory: boolean;
  is_security: boolean;
  published_at: string | null;
  created_at: string;
}

export interface ReleaseDetail extends ReleaseSummary {
  uuid: string;
  previous_version: string | null;
  body: string | null;
  download_url: string | null;
  checksum_sha256: string | null;
  signature_gpg: string | null;
  asset_size_bytes: number | null;
  release_notes_url: string | null;
  github_release_id: number | null;
  github_tag_name: string | null;
  is_draft: boolean;
  is_prerelease: boolean;
  updated_at: string;
}

export interface UpdateCheckResponse {
  update_available: boolean;
  current_version: string;
  latest_version: string | null;
  latest_release: ReleaseSummary | null;
  is_mandatory: boolean;
  is_security: boolean;
  channel: string;
  last_checked_at: string | null;
}

export interface InstallationRecord {
  id: number;
  uuid: string;
  release_id: number;
  release_version: string;
  previous_version: string | null;
  channel: string;
  status: string;
  error_message: string | null;
  downloaded_bytes: number;
  total_bytes: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  is_offline: boolean;
}

export interface UpdateHistoryResponse {
  installations: InstallationRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface UpdateActionResponse {
  success: boolean;
  message: string;
  installation_id: number | null;
  version: string | null;
}

export interface ChannelInfo {
  channel: string;
  display_name: string;
  release_count: number;
  latest_version: string | null;
  latest_release_title: string | null;
}

export interface UpdateSettings {
  auto_update_enabled: boolean;
  channel: string;
  schedule: string;
  background_download: boolean;
  auto_restart: boolean;
  notify_on_update: boolean;
}

export interface UpdateSettingsResponse extends UpdateSettings {
  id: number;
  uuid: string;
  last_checked_at: string | null;
  last_check_result: string | null;
  last_update_version: string | null;
  created_at: string;
  updated_at: string;
}

// ── API Functions ──

export async function fetchVersionInfo(): Promise<VersionInfo> {
  const { data } = await client.get('/api/v1/updates/version');
  return data;
}

export async function checkForUpdates(channel = 'stable'): Promise<UpdateCheckResponse> {
  const { data } = await client.get('/api/v1/updates/check', { params: { channel } });
  return data;
}

export async function fetchReleases(channel?: string, limit = 20, offset = 0): Promise<ReleaseSummary[]> {
  const { data } = await client.get('/api/v1/updates/releases', {
    params: { channel, limit, offset },
  });
  return data;
}

export async function fetchRelease(version: string): Promise<ReleaseDetail> {
  const { data } = await client.get(`/api/v1/updates/releases/${version}`);
  return data;
}

export async function fetchUpdateHistory(limit = 20, offset = 0): Promise<UpdateHistoryResponse> {
  const { data } = await client.get('/api/v1/updates/history', {
    params: { limit, offset },
  });
  return data;
}

export async function syncReleases(): Promise<{ success: boolean; new_releases: number; message: string }> {
  const { data } = await client.post('/api/v1/updates/sync');
  return data;
}

export async function downloadRelease(version: string): Promise<UpdateActionResponse> {
  const { data } = await client.post(`/api/v1/updates/download/${version}`);
  return data;
}

export async function installRelease(version: string): Promise<UpdateActionResponse> {
  const { data } = await client.post(`/api/v1/updates/install/${version}`);
  return data;
}

export async function rollbackUpdate(version?: string): Promise<UpdateActionResponse> {
  const { data } = await client.post('/api/v1/updates/rollback', null, {
    params: version ? { version } : undefined,
  });
  return data;
}

export async function fetchChannels(): Promise<ChannelInfo[]> {
  const { data } = await client.get('/api/v1/updates/channels');
  return data;
}

export async function fetchUpdateSettings(): Promise<UpdateSettingsResponse> {
  const { data } = await client.get('/api/v1/updates/settings');
  return data;
}

export async function updateUpdateSettings(settings: Partial<UpdateSettings>): Promise<UpdateSettingsResponse> {
  const { data } = await client.put('/api/v1/updates/settings', settings);
  return data;
}
