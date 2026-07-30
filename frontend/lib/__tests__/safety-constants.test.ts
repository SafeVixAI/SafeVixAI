// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import * as constants from '../safety-constants';

describe('safety-constants', function() {
  it('STANDARD_GRAVITY_MS2 is 9.81', function() {
    expect(constants.STANDARD_GRAVITY_MS2).toBe(9.81);
  });

  it('CRASH_THRESHOLD_G is 15', function() {
    expect(constants.CRASH_THRESHOLD_G).toBe(15);
  });

  it('CRASH_DEBOUNCE_MS is 60000', function() {
    expect(constants.CRASH_DEBOUNCE_MS).toBe(60_000);
  });

  it('CRASH_COUNTDOWN_SECONDS is 20', function() {
    expect(constants.CRASH_COUNTDOWN_SECONDS).toBe(20);
  });

  it('W3W_LOOKUP_TIMEOUT_MS is 3000', function() {
    expect(constants.W3W_LOOKUP_TIMEOUT_MS).toBe(3_000);
  });

  it('OFFLINE_SOS_SYNC_TIMEOUT_MS is 8000', function() {
    expect(constants.OFFLINE_SOS_SYNC_TIMEOUT_MS).toBe(8_000);
  });

  it('OFFLINE_CHALLAN_LOOKUP_DELAY_MS is 600', function() {
    expect(constants.OFFLINE_CHALLAN_LOOKUP_DELAY_MS).toBe(600);
  });

  it('LIVE_TRACKING_POLL_INTERVAL_MS is 5000', function() {
    expect(constants.LIVE_TRACKING_POLL_INTERVAL_MS).toBe(5_000);
  });

  it('GROUP_TRACKING_BROADCAST_INTERVAL_MS is 3000', function() {
    expect(constants.GROUP_TRACKING_BROADCAST_INTERVAL_MS).toBe(3_000);
  });

  it('EMERGENCY_NUMBER is "112"', function() {
    expect(constants.EMERGENCY_NUMBER).toBe('112');
  });

  it('AMBULANCE_NUMBER is "108"', function() {
    expect(constants.AMBULANCE_NUMBER).toBe('108');
  });

  it('all constants are frozen exports', function() {
    const allExports = Object.keys(constants);
    expect(allExports.length).toBeGreaterThan(0);
    for (const key of allExports) {
      expect(typeof (constants as any)[key]).toMatch(/number|string/);
    }
  });
});


