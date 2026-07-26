// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type { AuthSlice } from './auth-slice';
import type { MapSlice, MapSearchTarget, MapProvider, MapStatus } from './map-slice';
import type { SettingsSlice } from './settings-slice';
import type { UISlice } from './ui-slice';
import type { DataSlice, GpsLocation, NearbyService, NearbyRoadIssue, ServiceSearchMeta, RoadIssueSearchMeta, UserProfile, AiMode, ConnectivityState, ChallanState } from './data-slice';
import type { ProvidersSlice, ProviderSelection } from './providers-slice';
import type { UpdateSlice, UpdateInfo, ReleaseChannel, UpdateStatus } from './update-slice';

export type AppState = AuthSlice & MapSlice & SettingsSlice & UISlice & DataSlice & ProvidersSlice & UpdateSlice;

export type {
  AuthSlice, MapSlice, MapSearchTarget, MapProvider, MapStatus,
  SettingsSlice, UISlice, ProvidersSlice, ProviderSelection,
  DataSlice, GpsLocation, NearbyService, NearbyRoadIssue,
  ServiceSearchMeta, RoadIssueSearchMeta, UserProfile,
  AiMode, ConnectivityState, ChallanState,
  UpdateSlice, UpdateInfo, ReleaseChannel, UpdateStatus,
};
