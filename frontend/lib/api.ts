// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// Barrel file — re-exports all public API surface for backward compatibility.
// New code should import from specific sub-modules under lib/api/.

import { client, chatbotClient, fetchCsrfToken, setCsrfToken, extractApiError, csvParam } from './api/client';
import {
  normalizeEmergencyService, normalizeEmergencyResponse, normalizeGeocodeResult,
  normalizeRoadIssue, normalizeAuthorityPreview, normalizeInfrastructure,
  normalizeRoadReport, normalizeRoutePreview, normalizeMunicipality,
  normalizeMunicipalityDetail,
} from './api/normalizers';
import { getAddressFromGPS } from '@/lib/reverse-geocode';
import { calculateOfflineChallan } from '@/lib/duckdb-challan';
import type {
  EmergencyServiceCategory, RouteProfile,
  EmergencyService, EmergencyResponse, SosResponse,
  NearbyServicesParams, EmergencyNumbersResponse,
  GeocodeResult, GeocodeSearchResponse, ReverseGeocodeResponse,
  RoadIssue, RoadIssuesResponse,
  AuthorityPreviewResponse, RoadInfrastructureResponse,
  ReportPayload, RoadReportResponse,
  RoutePoint, RouteBounds, RouteInstruction, RouteOption, RoutePreviewResponse,
  ApiErrorDetail, ChatMessage, ChatRequest, ChatResponse,
  ChallanQuery, ChallanResult,
  Municipality, MunicipalityDetail, MunicipalitiesResponse, RawMunicipality,
  VehicleGarageItem, GarageSyncResponse,
  FinePredictionRequest, FinePredictionResponse,
  DisputeDraftRequest, DisputeDraftResponse,
} from './api/types';

export { client, chatbotClient, fetchCsrfToken, setCsrfToken, extractApiError, csvParam };
export type { RoadIssueStatus } from './api/client';

export type {
  EmergencyServiceCategory, RouteProfile,
  EmergencyService, EmergencyResponse, SosResponse,
  NearbyServicesParams, EmergencyNumbersResponse,
  GeocodeResult, GeocodeSearchResponse, ReverseGeocodeResponse,
  RoadIssue, RoadIssuesResponse,
  AuthorityPreviewResponse, RoadInfrastructureResponse,
  ReportPayload, RoadReportResponse,
  RoutePoint, RouteBounds, RouteInstruction, RouteOption, RoutePreviewResponse,
  ApiErrorDetail, ChatMessage, ChatRequest, ChatResponse,
  ChallanQuery, ChallanResult,
  Municipality, MunicipalityDetail, MunicipalitiesResponse, RawMunicipality,
  VehicleGarageItem, GarageSyncResponse,
  FinePredictionRequest, FinePredictionResponse,
  DisputeDraftRequest, DisputeDraftResponse,
};

export { normalizeEmergencyService, normalizeEmergencyResponse, normalizeGeocodeResult };

// ── Emergency API ──
export async function fetchNearbyServices(params: NearbyServicesParams): Promise<EmergencyResponse> {
  const { data } = await client.get('/api/v1/emergency/nearby', {
    params: {
      lat: params.lat, lon: params.lon, radius: params.radius,
      categories: params.categories instanceof Array ? params.categories.join(',') : params.categories,
      limit: params.limit,
    },
    signal: params.signal,
  });
  return normalizeEmergencyResponse(data);
}

export async function fetchSosPayload(params: { lat: number; lon: number }): Promise<SosResponse> {
  const { data } = await client.get('/api/v1/emergency/sos', { params });
  return { ...normalizeEmergencyResponse(data), numbers: data.numbers ?? {} };
}

export async function triggerSos(params: { lat: number; lon: number }): Promise<SosResponse> {
  const { data } = await client.post('/api/v1/emergency/sos', null, { params });
  return { ...normalizeEmergencyResponse(data), numbers: data.numbers ?? {} };
}

export async function fetchEmergencyNumbers(): Promise<EmergencyNumbersResponse> {
  const { data } = await client.get('/api/v1/emergency/numbers');
  return data;
}

// ── Geocode API ──
export async function reverseGeocode(params: { lat: number; lon: number }): Promise<ReverseGeocodeResponse> {
  const result = await getAddressFromGPS(params.lat, params.lon);
  if (!result) return { displayName: 'Unknown Location', lat: params.lat, lon: params.lon };
  return { displayName: result.displayAddress, city: result.city, state: result.state, lat: params.lat, lon: params.lon };
}

export async function searchGeocode(q: string): Promise<GeocodeSearchResponse> {
  const { data } = await client.get('/api/v1/geocode/search', { params: { q } });
  return { results: (data.results ?? []).map(normalizeGeocodeResult) };
}

// ── RoadWatch API ──
export async function fetchRoadIssues(params: {
  lat: number; lon: number; radius?: number; limit?: number;
  statuses?: string | string[]; signal?: AbortSignal;
}): Promise<RoadIssuesResponse> {
  const { data } = await client.get('/api/v1/roads/issues', {
    params: {
      lat: params.lat, lon: params.lon, radius: params.radius,
      limit: params.limit, statuses: csvParam(params.statuses),
    },
    signal: params.signal,
  });
  const issues = (data.issues ?? []).map(normalizeRoadIssue);
  return { issues, count: data.count ?? issues.length, radiusUsed: data.radius_used ?? 0 };
}

export async function fetchAuthorityPreview(params: { lat: number; lon: number }): Promise<AuthorityPreviewResponse> {
  const { data } = await client.get('/api/v1/roads/authority', { params });
  return normalizeAuthorityPreview(data);
}

export async function fetchRoadInfrastructure(params: { lat: number; lon: number }): Promise<RoadInfrastructureResponse> {
  const { data } = await client.get('/api/v1/roads/infrastructure', { params });
  return normalizeInfrastructure(data);
}

export async function submitReport(payload: ReportPayload): Promise<RoadReportResponse> {
  const issueType = payload.issue_type ?? payload.type;
  if (!issueType) throw new Error('submitReport requires either "issue_type" or "type".');
  const formData = new FormData();
  formData.append('lat', String(payload.lat));
  formData.append('lon', String(payload.lon));
  formData.append('issue_type', issueType);
  formData.append('severity', String(payload.severity));
  if (payload.description?.trim()) formData.append('description', payload.description.trim());
  if (payload.photo) formData.append('photo', payload.photo);
  if (payload.citizen_phone) formData.append('citizen_phone', payload.citizen_phone);
  const { data } = await client.post('/api/v1/roads/report', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return normalizeRoadReport(data);
}

// ── Routing API ──
export async function fetchRoutePreview(params: {
  originLat: number; originLon: number;
  destinationLat: number; destinationLon: number;
  profile?: RouteProfile; alternatives?: number;
}): Promise<RoutePreviewResponse> {
  const { data } = await client.get('/api/v1/routing/preview', {
    params: {
      origin_lat: params.originLat, origin_lon: params.originLon,
      destination_lat: params.destinationLat, destination_lon: params.destinationLon,
      profile: params.profile ?? 'driving-car', alternatives: params.alternatives ?? 2,
    },
  });
  return normalizeRoutePreview(data);
}

// ── Chat API ──
export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const { data } = await chatbotClient.post('/api/v1/chat/', req);
  return data;
}

// ── Challan API ──
export async function calculateChallan(query: ChallanQuery): Promise<ChallanResult> {
  try {
    const { data } = await client.post('/api/v1/challan/calculate', query);
    return { ...data, source: data.source || 'online' };
  } catch (error) {
    console.warn('SafeVixAI: API challan calculation failed, falling back to local offline DB:', error);
    try {
      const offlineResult = await calculateOfflineChallan(
        query.violation_code, query.vehicle_class, query.is_repeat, query.state_code,
      );
      return {
        violation_code: query.violation_code, vehicle_class: query.vehicle_class,
        state_code: query.state_code, base_fine: offlineResult.base_fine,
        repeat_fine: offlineResult.repeat_fine,
        amount_due: query.is_repeat && offlineResult.repeat_fine ? offlineResult.repeat_fine : offlineResult.base_fine,
        section: offlineResult.section, description: offlineResult.description, source: 'offline',
      };
    } catch (fallbackError) {
      console.error('SafeVixAI: Offline challan fallback also failed:', fallbackError);
      throw error;
    }
  }
}

// ── Municipality / Civic API ──
export async function fetchMunicipalities(params?: {
  q?: string; stateCode?: string; municipalityType?: string;
  page?: number; pageSize?: number;
}): Promise<MunicipalitiesResponse> {
  const { data } = await client.get('/api/v1/civic/municipalities', {
    params: {
      q: params?.q, state_code: params?.stateCode,
      municipality_type: params?.municipalityType,
      page: params?.page ?? 1, page_size: params?.pageSize ?? 50,
    },
  });
  return {
    municipalities: (data.municipalities ?? data.items ?? []).map(normalizeMunicipality),
    total: data.total ?? 0, page: data.page ?? 1, pageSize: data.page_size ?? 50,
  };
}

export async function fetchMunicipalityBySlug(slug: string): Promise<MunicipalityDetail> {
  const { data } = await client.get(`/api/v1/civic/municipalities/${slug}`);
  return normalizeMunicipalityDetail(data);
}

export async function fetchNearbyMunicipalities(lat: number, lon: number, limit?: number): Promise<Municipality[]> {
  const { data } = await client.get('/api/v1/civic/municipalities/nearby', { params: { lat, lon, limit: limit ?? 10 } });
  return (data.municipalities ?? data ?? []).map(normalizeMunicipality);
}

// ── Enterprise Civic Workflow APIs ──
export async function authorityAcceptComplaint(uuid: string): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/authority/complaints/${uuid}/accept`);
  return data;
}

export async function authorityRejectComplaint(uuid: string, reason: string): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/authority/complaints/${uuid}/reject`, { reason });
  return data;
}

export async function citizenConfirmResolution(ref: string, rating?: number, notes?: string): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/citizen/complaints/${ref}/confirm`, { rating, notes });
  return data;
}

export async function citizenRejectResolution(ref: string, reason: string): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/citizen/complaints/${ref}/reject`, { reason });
  return data;
}

export async function fetchPublicWardRankings(): Promise<Record<string, unknown>[]> {
  const { data } = await client.get('/api/v1/public/ward-rankings');
  return data;
}

export async function fetchPublicStats(): Promise<Record<string, unknown>> {
  const { data } = await client.get('/api/v1/public/stats');
  return data;
}

export async function fieldStartWork(uuid: string, lat: number, lon: number): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/field/complaints/${uuid}/start-work`, { lat, lon });
  return data;
}

export async function fieldUploadEvidence(uuid: string, formData: FormData): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/field/complaints/${uuid}/upload-evidence`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function fieldCompleteWork(
  uuid: string, afterPhotoUrl: string | null, notes: string | null,
  lat: number, lon: number,
): Promise<Record<string, unknown>> {
  const { data } = await client.post(`/api/v1/field/complaints/${uuid}/complete`, {
    after_photo_url: afterPhotoUrl, notes, lat, lon,
  });
  return data;
}

// ── Garage, Prediction & Dispute API ──
export async function syncGarage(vehicleNumber?: string): Promise<GarageSyncResponse> {
  const { data } = await client.post('/api/v1/garage/sync', null, {
    params: vehicleNumber ? { vehicle_number: vehicleNumber } : undefined,
  });
  return data;
}

export async function predictFineLiability(req: FinePredictionRequest): Promise<FinePredictionResponse> {
  const { data } = await client.post('/api/v1/challan/predict', req);
  return data;
}

export async function draftDisputeAppeal(req: DisputeDraftRequest): Promise<DisputeDraftResponse> {
  const { data } = await client.post('/api/v1/challan/dispute', req);
  return data;
}
