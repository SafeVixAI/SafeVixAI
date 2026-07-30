// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { client } from './client';
import type {
  IssueDetail,
  IssueListResponse,
  IssueStatsResponse,
  CreateIssueRequest,
  UpdateIssueRequest,
  IssueTemplate,
  TimelineEvent,
} from './types';

export type { IssueDetail, IssueListResponse, IssueStatsResponse, IssueTemplate };

export async function fetchIssues(params: {
  page?: number;
  pageSize?: number;
  status?: string;
  issueType?: string;
  category?: string;
  severity?: string;
  search?: string;
  includeSpam?: boolean;
}): Promise<IssueListResponse> {
  const { data } = await client.get('/api/v1/issues', { params });
  return data;
}

export async function fetchIssue(issueUuid: string): Promise<IssueDetail> {
  const { data } = await client.get(`/api/v1/issues/${issueUuid}`);
  return data;
}

export async function fetchIssueByTracking(trackingNumber: string): Promise<IssueDetail> {
  const { data } = await client.get(`/api/v1/issues/tracking/${trackingNumber}`);
  return data;
}

export async function createIssue(payload: CreateIssueRequest): Promise<IssueDetail> {
  const { data } = await client.post('/api/v1/issues', payload);
  return data;
}

export async function updateIssue(
  issueUuid: string,
  payload: UpdateIssueRequest,
): Promise<IssueDetail> {
  const { data } = await client.patch(`/api/v1/issues/${issueUuid}`, payload);
  return data;
}

export async function fetchIssueStats(): Promise<IssueStatsResponse> {
  const { data } = await client.get('/api/v1/issues/stats');
  return data;
}

export async function fetchIssueTemplates(): Promise<IssueTemplate[]> {
  const { data } = await client.get('/api/v1/issues/templates');
  return data;
}

export async function fetchTimeline(issueUuid: string): Promise<TimelineEvent[]> {
  const { data } = await client.get(`/api/v1/issues/${issueUuid}/timeline`);
  return data;
}

export async function markSpam(issueUuid: string, reason?: string): Promise<IssueDetail> {
  const { data } = await client.post(`/api/v1/issues/${issueUuid}/spam`, null, {
    params: { reason: reason || 'manually flagged' },
  });
  return data;
}

export async function markDuplicate(
  issueUuid: string,
  originalUuid: string,
): Promise<IssueDetail> {
  const { data } = await client.post(`/api/v1/issues/${issueUuid}/duplicate/${originalUuid}`);
  return data;
}

export async function fetchDuplicates(
  issueUuid: string,
  threshold?: number,
): Promise<Array<{ uuid: string; trackingNumber: string; title: string; score: number }>> {
  const { data } = await client.get(`/api/v1/issues/${issueUuid}/duplicates`, {
    params: { threshold: threshold || 0.7 },
  });
  return data;
}
