// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

const GUEST_ID_KEY = 'safevixai_guest_id';
const GUEST_PROFILE_KEY = 'safevixai_guest_profile';

interface GuestProfile {
  id: string;
  createdAt: number;
  preferredLanguage?: string;
  emergencyContacts?: Array<{ name: string; phone: string; relation: string }>;
  bloodGroup?: string;
}

function generateGuestId(): string {
  const arr = new Uint8Array(16);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('');
}

// Guest profile is device-local only — contains no server-side secrets or credentials
// See: AGENTS.md "Privacy by design" — blood group stays on device
export function getOrCreateGuestId(): string {
  let id = localStorage.getItem(GUEST_ID_KEY);
  if (!id) {
    id = generateGuestId();
    localStorage.setItem(GUEST_ID_KEY, id);
    const profile: GuestProfile = { id, createdAt: Date.now() };
    localStorage.setItem(GUEST_PROFILE_KEY, JSON.stringify(profile));
  }
  return id;
}

export function getGuestProfile(): GuestProfile | null {
  try {
    const raw = localStorage.getItem(GUEST_PROFILE_KEY);
    return raw ? (JSON.parse(raw) as GuestProfile) : null;
  } catch {
    return null;
  }
}

export function updateGuestProfile(updates: Partial<GuestProfile>): void {
  const current = getGuestProfile() || { id: getOrCreateGuestId(), createdAt: Date.now() };
  Object.assign(current, updates);
  localStorage.setItem(GUEST_PROFILE_KEY, JSON.stringify(current));
}

export function isGuestMode(): boolean {
  return !!localStorage.getItem(GUEST_ID_KEY);
}

export function clearGuestSession(): void {
  localStorage.removeItem(GUEST_ID_KEY);
  localStorage.removeItem(GUEST_PROFILE_KEY);
}
