// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type { RoadIssueStatus } from './client';

export type EmergencyServiceCategory =
  | 'hospital'
  | 'police'
  | 'ambulance'
  | 'fire'
  | 'towing'
  | 'pharmacy'
  | 'puncture'
  | 'showroom';

export type RouteProfile = 'driving-car' | 'cycling-regular' | 'foot-walking';

export interface EmergencyService {
  id: string;
  name: string;
  category: EmergencyServiceCategory | string;
  subCategory?: string | null;
  phone?: string | null;
  phoneEmergency?: string | null;
  lat: number;
  lon: number;
  distanceMeters: number;
  hasTrauma: boolean;
  hasIcu: boolean;
  is24Hr: boolean;
  address?: string | null;
  source: string;
}

export interface EmergencyResponse {
  services: EmergencyService[];
  count: number;
  radiusUsed: number;
  source: string;
}

export interface SosResponse extends EmergencyResponse {
  numbers: Record<string, { service: string; coverage: string; notes?: string | null }>;
}

export interface NearbyServicesParams {
  lat: number;
  lon: number;
  radius?: number;
  categories?: EmergencyServiceCategory | EmergencyServiceCategory[] | string | string[];
  limit?: number;
  signal?: AbortSignal;
}

export interface EmergencyNumbersResponse {
  numbers: Record<string, { service: string; coverage: string; notes?: string | null }>;
}

export interface GeocodeResult {
  displayName: string;
  city?: string | null;
  state?: string | null;
  stateCode?: string | null;
  countryCode?: string | null;
  postcode?: string | null;
  lat?: number | null;
  lon?: number | null;
}

export interface GeocodeSearchResponse {
  results: GeocodeResult[];
}

export interface ReverseGeocodeResponse extends GeocodeResult {}

export interface RoadIssue {
  uuid: string;
  issueType: string;
  severity: number;
  description?: string | null;
  lat: number;
  lon: number;
  locationAddress?: string | null;
  roadName?: string | null;
  roadType?: string | null;
  roadNumber?: string | null;
  authorityName?: string | null;
  status: RoadIssueStatus;
  createdAt: string;
  distanceMeters: number;
}

export interface RoadIssuesResponse {
  issues: RoadIssue[];
  count: number;
  radiusUsed: number;
}

export interface AuthorityPreviewResponse {
  roadType: string;
  roadTypeCode: string;
  roadName?: string | null;
  roadNumber?: string | null;
  authorityName: string;
  helpline: string;
  complaintPortal: string;
  escalationPath: string;
  execEngineer?: string | null;
  execEngineerPhone?: string | null;
  contractorName?: string | null;
  budgetSanctioned?: number | null;
  budgetSpent?: number | null;
  lastRelayedDate?: string | null;
  nextMaintenance?: string | null;
  dataSourceUrl?: string | null;
  source: string;
}

export interface RoadInfrastructureResponse {
  roadType: string;
  roadTypeCode: string;
  roadName?: string | null;
  roadNumber?: string | null;
  contractorName?: string | null;
  execEngineer?: string | null;
  execEngineerPhone?: string | null;
  budgetSanctioned?: number | null;
  budgetSpent?: number | null;
  lastRelayedDate?: string | null;
  nextMaintenance?: string | null;
  dataSourceUrl?: string | null;
  source: string;
}

export interface ReportPayload {
  lat: number;
  lon: number;
  severity: number;
  description?: string;
  type?: string;
  issue_type?: string;
  photo?: File | Blob | null;
  citizen_phone?: string;
}

export interface RoadReportResponse {
  uuid: string;
  complaintRef?: string | null;
  authorityName: string;
  authorityPhone: string;
  complaintPortal: string;
  roadType: string;
  roadTypeCode: string;
  roadNumber?: string | null;
  roadName?: string | null;
  execEngineer?: string | null;
  execEngineerPhone?: string | null;
  contractorName?: string | null;
  lastRelayedDate?: string | null;
  nextMaintenance?: string | null;
  budgetSanctioned?: number | null;
  budgetSpent?: number | null;
  photoUrl?: string | null;
  status: RoadIssueStatus;
  category?: string | null;
  subCategory?: string | null;
  wardId?: string | null;
  wardName?: string | null;
  slaDeadline?: string | null;
  duplicateOfUuid?: string | null;
}

export interface RoutePoint {
  lat: number;
  lon: number;
  label?: string | null;
}

export interface RouteBounds {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface RouteInstruction {
  index: number;
  instruction: string;
  distanceMeters: number;
  durationSeconds: number;
  streetName?: string | null;
  instructionType?: number | null;
  exitNumber?: number | null;
}

export interface RouteOption {
  routeId: string;
  label: string;
  distanceMeters: number;
  durationSeconds: number;
  path: RoutePoint[];
  bounds: RouteBounds;
  steps: RouteInstruction[];
}

export interface RoutePreviewResponse {
  provider: string;
  profile: RouteProfile | string;
  distanceMeters: number;
  durationSeconds: number;
  path: RoutePoint[];
  bounds: RouteBounds;
  origin: RoutePoint;
  destination: RoutePoint;
  steps: RouteInstruction[];
  routes: RouteOption[];
  selectedRouteId: string;
  rerouteThresholdMeters: number;
  warnings: string[];
}

export interface ApiErrorDetail {
  message: string;
  code?: string;
  status?: number;
  details?: unknown;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  lat?: number;
  lon?: number;
}

export interface ChatResponse {
  response: string;
  intent?: string;
  sources?: string[];
  session_id: string;
}

export interface ChallanQuery {
  violation_code: string;
  vehicle_class: string;
  state_code: string;
  is_repeat: boolean;
}

export interface ChallanResult {
  violation_code: string;
  vehicle_class: string;
  state_code: string;
  base_fine: number;
  repeat_fine: number | null;
  amount_due: number;
  section: string;
  description: string;
  state_override?: string;
  source?: string;
}

export interface Municipality {
  slug: string;
  name: string;
  shortName: string;
  city: string;
  stateCode: string;
  municipalityType: string;
  wardCount: number | null;
  population: number | null;
  helplinePhone: string | null;
  centroidLat: number;
  centroidLon: number;
  distanceKm?: number | null;
}

export interface MunicipalityDetail extends Municipality {
  headquartersAddress: string | null;
  email: string | null;
  websiteUrl: string | null;
  whatsappNumber: string | null;
  appName: string | null;
  appUrl: string | null;
  grievancePortalUrl: string | null;
  mayorName: string | null;
  mayorPhotoUrl: string | null;
  commissionerName: string | null;
  commissionerPhone: string | null;
  areaSqkm: number | null;
  description: string | null;
  servicesOffered: string[] | null;
}

export interface MunicipalitiesResponse {
  municipalities: Municipality[];
  total: number;
  page: number;
  pageSize: number;
}

export interface RawMunicipality {
  slug?: string;
  name?: string;
  short_name?: string;
  shortName?: string;
  city?: string;
  state_code?: string;
  stateCode?: string;
  municipality_type?: string;
  municipalityType?: string;
  ward_count?: number | null;
  wardCount?: number | null;
  population?: number | null;
  helpline_phone?: string | null;
  helplinePhone?: string | null;
  centroid_lat?: number;
  centroidLat?: number;
  centroid_lon?: number;
  centroidLon?: number;
  distance_km?: number | null;
  distanceKm?: number | null;
  headquarters_address?: string | null;
  email?: string | null;
  website_url?: string | null;
  whatsapp_number?: string | null;
  app_name?: string | null;
  app_url?: string | null;
  grievance_portal_url?: string | null;
  mayor_name?: string | null;
  mayor_photo_url?: string | null;
  commissioner_name?: string | null;
  commissioner_phone?: string | null;
  area_sqkm?: number | null;
  description?: string | null;
  services_offered?: string[] | null;
}

export interface VehicleGarageItem {
  id: string;
  vehicle_number: string;
  owner_name: string;
  vehicle_make: string;
  vehicle_model: string;
  rc_status: string;
  insurance_expiry?: string | null;
  puc_expiry?: string | null;
  created_at: string;
}

export interface GarageSyncResponse {
  vehicles: VehicleGarageItem[];
  sync_status: string;
  last_synced_at: string;
}

export interface FinePredictionRequest {
  vehicle_number: string;
  state_code: string;
  telemetry: {
    speeding_events: number;
    harsh_braking_events: number;
    night_driving_minutes: number;
    total_km_driven: number;
  };
}

export interface FinePredictionResponse {
  predicted_violations_count: number;
  estimated_annual_liability: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  recommendations: string[];
}

export interface DisputeDraftRequest {
  challan_ref: string;
  violation_code: string;
  fine_amount: number;
  mitigating_factors: string;
}

export interface DisputeDraftResponse {
  dispute_ref: string;
  appeal_letter: string;
  cited_mva_sections: string[];
  confidence_score: number;
  instructions: string[];
}
