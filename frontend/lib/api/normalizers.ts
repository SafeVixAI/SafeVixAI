// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type {
  EmergencyService, EmergencyResponse, GeocodeResult,
  RoadIssue, AuthorityPreviewResponse, RoadInfrastructureResponse,
  RoadReportResponse, RoutePoint, RouteInstruction, RouteOption,
  RoutePreviewResponse, Municipality, MunicipalityDetail, RawMunicipality,
} from './types';
import type { RoadIssueStatus } from './client';

export function normalizeEmergencyService(item: {
  id: string; name: string; category: string;
  sub_category?: string | null; phone?: string | null;
  phone_emergency?: string | null; lat: number; lon: number;
  distance_meters: number; has_trauma?: boolean; has_icu?: boolean;
  is_24hr?: boolean; address?: string | null; source?: string;
}): EmergencyService {
  return {
    id: item.id, name: item.name, category: item.category,
    subCategory: item.sub_category ?? null, phone: item.phone ?? null,
    phoneEmergency: item.phone_emergency ?? null, lat: item.lat, lon: item.lon,
    distanceMeters: item.distance_meters, hasTrauma: Boolean(item.has_trauma),
    hasIcu: Boolean(item.has_icu), is24Hr: item.is_24hr ?? true,
    address: item.address ?? null, source: item.source ?? 'api',
  };
}

export function normalizeEmergencyResponse(data: {
  services?: Array<Parameters<typeof normalizeEmergencyService>[0]>;
  count?: number; radius_used?: number; source?: string;
}): EmergencyResponse {
  const services = (data.services ?? []).map(normalizeEmergencyService);
  return {
    services, count: data.count ?? services.length,
    radiusUsed: data.radius_used ?? 0, source: data.source ?? 'api',
  };
}

export function normalizeGeocodeResult(result: {
  display_name: string; city?: string | null; state?: string | null;
  state_code?: string | null; country_code?: string | null;
  postcode?: string | null; lat?: number | null; lon?: number | null;
}): GeocodeResult {
  return {
    displayName: result.display_name, city: result.city ?? null,
    state: result.state ?? null, stateCode: result.state_code ?? null,
    countryCode: result.country_code ?? null, postcode: result.postcode ?? null,
    lat: result.lat ?? null, lon: result.lon ?? null,
  };
}

export function normalizeRoadIssue(issue: {
  uuid: string; issue_type: string; severity: number;
  description?: string | null; lat: number; lon: number;
  location_address?: string | null; road_name?: string | null;
  road_type?: string | null; road_number?: string | null;
  authority_name?: string | null; status: RoadIssueStatus;
  created_at: string; distance_meters: number;
}): RoadIssue {
  return {
    uuid: issue.uuid, issueType: issue.issue_type, severity: issue.severity,
    description: issue.description ?? null, lat: issue.lat, lon: issue.lon,
    locationAddress: issue.location_address ?? null,
    roadName: issue.road_name ?? null, roadType: issue.road_type ?? null,
    roadNumber: issue.road_number ?? null, authorityName: issue.authority_name ?? null,
    status: issue.status, createdAt: issue.created_at, distanceMeters: issue.distance_meters,
  };
}

export function normalizeAuthorityPreview(data: {
  road_type: string; road_type_code: string; road_name?: string | null;
  road_number?: string | null; authority_name: string; helpline: string;
  complaint_portal: string; escalation_path: string;
  exec_engineer?: string | null; exec_engineer_phone?: string | null;
  contractor_name?: string | null; budget_sanctioned?: number | null;
  budget_spent?: number | null; last_relayed_date?: string | null;
  next_maintenance?: string | null; data_source_url?: string | null; source: string;
}): AuthorityPreviewResponse {
  return {
    roadType: data.road_type, roadTypeCode: data.road_type_code,
    roadName: data.road_name ?? null, roadNumber: data.road_number ?? null,
    authorityName: data.authority_name, helpline: data.helpline,
    complaintPortal: data.complaint_portal, escalationPath: data.escalation_path,
    execEngineer: data.exec_engineer ?? null, execEngineerPhone: data.exec_engineer_phone ?? null,
    contractorName: data.contractor_name ?? null, budgetSanctioned: data.budget_sanctioned ?? null,
    budgetSpent: data.budget_spent ?? null, lastRelayedDate: data.last_relayed_date ?? null,
    nextMaintenance: data.next_maintenance ?? null, dataSourceUrl: data.data_source_url ?? null,
    source: data.source,
  };
}

export function normalizeInfrastructure(data: {
  road_type: string; road_type_code: string; road_name?: string | null;
  road_number?: string | null; contractor_name?: string | null;
  exec_engineer?: string | null; exec_engineer_phone?: string | null;
  budget_sanctioned?: number | null; budget_spent?: number | null;
  last_relayed_date?: string | null; next_maintenance?: string | null;
  data_source_url?: string | null; source: string;
}): RoadInfrastructureResponse {
  return {
    roadType: data.road_type, roadTypeCode: data.road_type_code,
    roadName: data.road_name ?? null, roadNumber: data.road_number ?? null,
    contractorName: data.contractor_name ?? null, execEngineer: data.exec_engineer ?? null,
    execEngineerPhone: data.exec_engineer_phone ?? null, budgetSanctioned: data.budget_sanctioned ?? null,
    budgetSpent: data.budget_spent ?? null, lastRelayedDate: data.last_relayed_date ?? null,
    nextMaintenance: data.next_maintenance ?? null, dataSourceUrl: data.data_source_url ?? null,
    source: data.source,
  };
}

export function normalizeRoadReport(data: {
  uuid: string; complaint_ref?: string | null; authority_name: string;
  authority_phone: string; complaint_portal: string; road_type: string;
  road_type_code: string; road_number?: string | null; road_name?: string | null;
  exec_engineer?: string | null; exec_engineer_phone?: string | null;
  contractor_name?: string | null; last_relayed_date?: string | null;
  next_maintenance?: string | null; budget_sanctioned?: number | null;
  budget_spent?: number | null; photo_url?: string | null; status: RoadIssueStatus;
  category?: string | null; sub_category?: string | null; ward_id?: string | null;
  ward_name?: string | null; sla_deadline?: string | null; duplicate_of_uuid?: string | null;
}): RoadReportResponse {
  return {
    uuid: data.uuid, complaintRef: data.complaint_ref ?? null,
    authorityName: data.authority_name, authorityPhone: data.authority_phone,
    complaintPortal: data.complaint_portal, roadType: data.road_type,
    roadTypeCode: data.road_type_code, roadNumber: data.road_number ?? null,
    roadName: data.road_name ?? null, execEngineer: data.exec_engineer ?? null,
    execEngineerPhone: data.exec_engineer_phone ?? null, contractorName: data.contractor_name ?? null,
    lastRelayedDate: data.last_relayed_date ?? null, nextMaintenance: data.next_maintenance ?? null,
    budgetSanctioned: data.budget_sanctioned ?? null, budgetSpent: data.budget_spent ?? null,
    photoUrl: data.photo_url ?? null, status: data.status, category: data.category ?? null,
    subCategory: data.sub_category ?? null, wardId: data.ward_id ?? null,
    wardName: data.ward_name ?? null, slaDeadline: data.sla_deadline ?? null,
    duplicateOfUuid: data.duplicate_of_uuid ?? null,
  };
}

export function normalizeRoutePoint(point: { lat: number; lon: number; label?: string | null }): RoutePoint {
  return { lat: point.lat, lon: point.lon, label: point.label ?? null };
}

export function normalizeRouteInstruction(step: {
  index: number; instruction: string; distance_meters: number; duration_seconds: number;
  street_name?: string | null; instruction_type?: number | null; exit_number?: number | null;
}): RouteInstruction {
  return {
    index: step.index, instruction: step.instruction, distanceMeters: step.distance_meters,
    durationSeconds: step.duration_seconds, streetName: step.street_name ?? null,
    instructionType: step.instruction_type ?? null, exitNumber: step.exit_number ?? null,
  };
}

export function normalizeRouteOption(route: {
  route_id: string; label: string; distance_meters: number; duration_seconds: number;
  path: Array<{ lat: number; lon: number; label?: string | null }>;
  bounds: import('./types').RouteBounds;
  steps?: Array<{
    index: number; instruction: string; distance_meters: number; duration_seconds: number;
    street_name?: string | null; instruction_type?: number | null; exit_number?: number | null;
  }>;
}): RouteOption {
  return {
    routeId: route.route_id, label: route.label, distanceMeters: route.distance_meters,
    durationSeconds: route.duration_seconds, path: (route.path ?? []).map(normalizeRoutePoint),
    bounds: route.bounds, steps: (route.steps ?? []).map(normalizeRouteInstruction),
  };
}

export function normalizeRoutePreview(data: {
  provider: string; profile: import('./types').RouteProfile | string;
  distance_meters: number; duration_seconds: number;
  path: Array<{ lat: number; lon: number; label?: string | null }>;
  bounds: import('./types').RouteBounds;
  origin: { lat: number; lon: number; label?: string | null };
  destination: { lat: number; lon: number; label?: string | null };
  steps?: Array<{
    index: number; instruction: string; distance_meters: number; duration_seconds: number;
    street_name?: string | null; instruction_type?: number | null; exit_number?: number | null;
  }>;
  routes?: Array<{
    route_id: string; label: string; distance_meters: number; duration_seconds: number;
    path: Array<{ lat: number; lon: number; label?: string | null }>;
    bounds: import('./types').RouteBounds;
    steps?: Array<{
      index: number; instruction: string; distance_meters: number; duration_seconds: number;
      street_name?: string | null; instruction_type?: number | null; exit_number?: number | null;
    }>;
  }>;
  selected_route_id?: string; reroute_threshold_meters?: number; warnings?: string[];
}): RoutePreviewResponse {
  const routes = (data.routes ?? []).map(normalizeRouteOption);
  return {
    provider: data.provider, profile: data.profile, distanceMeters: data.distance_meters,
    durationSeconds: data.duration_seconds, path: (data.path ?? []).map(normalizeRoutePoint),
    bounds: data.bounds, origin: normalizeRoutePoint(data.origin),
    destination: normalizeRoutePoint(data.destination),
    steps: (data.steps ?? []).map(normalizeRouteInstruction), routes,
    selectedRouteId: data.selected_route_id ?? routes[0]?.routeId ?? 'route-1',
    rerouteThresholdMeters: data.reroute_threshold_meters ?? 75, warnings: data.warnings ?? [],
  };
}

export function normalizeMunicipality(d: RawMunicipality): Municipality {
  return {
    slug: d.slug ?? '', name: d.name ?? '',
    shortName: d.short_name ?? d.shortName ?? '', city: d.city ?? '',
    stateCode: d.state_code ?? d.stateCode ?? '',
    municipalityType: d.municipality_type ?? d.municipalityType ?? '',
    wardCount: d.ward_count ?? d.wardCount ?? null, population: d.population ?? null,
    helplinePhone: d.helpline_phone ?? d.helplinePhone ?? null,
    centroidLat: d.centroid_lat ?? d.centroidLat ?? 0,
    centroidLon: d.centroid_lon ?? d.centroidLon ?? 0,
    distanceKm: d.distance_km ?? d.distanceKm ?? null,
  };
}

export function normalizeMunicipalityDetail(d: RawMunicipality): MunicipalityDetail {
  return {
    ...normalizeMunicipality(d),
    headquartersAddress: d.headquarters_address ?? null, email: d.email ?? null,
    websiteUrl: d.website_url ?? null, whatsappNumber: d.whatsapp_number ?? null,
    appName: d.app_name ?? null, appUrl: d.app_url ?? null,
    grievancePortalUrl: d.grievance_portal_url ?? null, mayorName: d.mayor_name ?? null,
    mayorPhotoUrl: d.mayor_photo_url ?? null, commissionerName: d.commissioner_name ?? null,
    commissionerPhone: d.commissioner_phone ?? null, areaSqkm: d.area_sqkm ?? null,
    description: d.description ?? null, servicesOffered: d.services_offered ?? null,
  };
}
