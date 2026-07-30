// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import {
  isApproximateLocation,
  formatAccuracyLabel,
  formatLocationLabel,
  formatLocationSubtitle,
} from '../location-utils';

function makeLocation(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    lat: 13.0827,
    lon: 80.2707,
    accuracy: 100,
    timestamp: Date.now(),
    ...overrides,
  };
}

describe('location-utils', function() {
  describe('isApproximateLocation', function() {
    it('returns false for null', function() {
      expect(isApproximateLocation(null)).toBe(false);
    });

    it('returns false for undefined', function() {
      expect(isApproximateLocation(undefined)).toBe(false);
    });

    it('returns false for accuracy below threshold', function() {
      expect(isApproximateLocation(makeLocation({ accuracy: 100 }))).toBe(false);
    });

    it('returns true for accuracy equal to threshold', function() {
      expect(isApproximateLocation(makeLocation({ accuracy: 2500 }))).toBe(true);
    });

    it('returns true for accuracy above threshold', function() {
      expect(isApproximateLocation(makeLocation({ accuracy: 5000 }))).toBe(true);
    });
  });

  describe('formatAccuracyLabel', function() {
    it('returns null for null', function() {
      expect(formatAccuracyLabel(null)).toBeNull();
    });

    it('returns null for undefined', function() {
      expect(formatAccuracyLabel(undefined)).toBeNull();
    });

    it('formats accuracy in meters when < 1000', function() {
      expect(formatAccuracyLabel(makeLocation({ accuracy: 50 }))).toBe('50 m accuracy');
    });

    it('rounds meter accuracy', function() {
      expect(formatAccuracyLabel(makeLocation({ accuracy: 505 }))).toBe('505 m accuracy');
    });

    it('formats accuracy in km when >= 1000', function() {
      expect(formatAccuracyLabel(makeLocation({ accuracy: 1000 }))).toBe('1.0 km accuracy');
    });

    it('formats accuracy in km with one decimal', function() {
      expect(formatAccuracyLabel(makeLocation({ accuracy: 2500 }))).toBe('2.5 km accuracy');
    });
  });

  describe('formatLocationLabel', function() {
    it('returns "Enable Location" when gpsError is truthy', function() {
      expect(formatLocationLabel(null, 'Permission denied')).toBe('Enable Location');
    });

    it('returns "Enable Location" when gpsError is set even with valid location', function() {
      const loc = makeLocation({ city: 'Chennai' });
      expect(formatLocationLabel(loc, 'Timeout')).toBe('Enable Location');
    });

    it('returns "Use My Location" when location is null and no gpsError', function() {
      expect(formatLocationLabel(null, null)).toBe('Use My Location');
    });

    it('returns "Use My Location" when location is undefined', function() {
      expect(formatLocationLabel(undefined, null)).toBe('Use My Location');
    });

    it('returns city and state for accurate location', function() {
      const loc = makeLocation({ city: 'Chennai', state: 'Tamil Nadu', accuracy: 100 });
      expect(formatLocationLabel(loc, null)).toBe('Chennai, Tamil Nadu');
    });

    it('returns city only when no state', function() {
      const loc = makeLocation({ city: 'Chennai', accuracy: 100 });
      expect(formatLocationLabel(loc, null)).toBe('Chennai');
    });

    it('returns "Approx." prefix for approximate location with city', function() {
      const loc = makeLocation({ city: 'Chennai', accuracy: 2500 });
      expect(formatLocationLabel(loc, null)).toBe('Approx. Chennai');
    });

    it('falls back to displayName when no city', function() {
      const loc = makeLocation({
        displayName: 'Anna Nagar, Chennai',
        accuracy: 100,
        city: undefined,
      });
      expect(formatLocationLabel(loc, null)).toBe('Anna Nagar, Chennai');
    });

    it('falls back to lat/lon when no city or displayName', function() {
      const loc = makeLocation({
        accuracy: 100,
        city: undefined,
        displayName: undefined,
      });
      expect(formatLocationLabel(loc, null)).toBe('13.083, 80.271');
    });

    it('prefixes "Approx." for lat/lon fallback', function() {
      const loc = makeLocation({
        accuracy: 2500,
        city: undefined,
        displayName: undefined,
      });
      expect(formatLocationLabel(loc, null)).toBe('Approx. 13.083, 80.271');
    });

    it('handles city with trailing comma', function() {
      const loc = makeLocation({ city: 'Chennai,', state: '', accuracy: 100 });
      expect(formatLocationLabel(loc, null)).toBe('Chennai');
    });
  });

  describe('formatLocationSubtitle', function() {
    it('returns default message for null', function() {
      expect(formatLocationSubtitle(null)).toBe(
        'Enable location for live nearby results',
      );
    });

    it('returns default message for undefined', function() {
      expect(formatLocationSubtitle(undefined)).toBe(
        'Enable location for live nearby results',
      );
    });

    it('returns accuracy info for approximate location', function() {
      const loc = makeLocation({
        accuracy: 2500,
        city: undefined,
        displayName: undefined,
      });
      expect(formatLocationSubtitle(loc)).toBe(
        'Approximate browser/device location \u00B7 2.5 km accuracy',
      );
    });

    it('falls back to lat/lon when accuracy is below threshold and no city', function() {
      const loc = makeLocation({
        accuracy: 0,
        city: undefined,
        displayName: undefined,
      });
      expect(formatLocationSubtitle(loc)).toBe('13.083, 80.271');
    });

    it('returns displayName for accurate location', function() {
      const loc = makeLocation({
        displayName: 'T. Nagar, Chennai',
        accuracy: 100,
        city: undefined,
      });
      expect(formatLocationSubtitle(loc)).toBe('T. Nagar, Chennai');
    });

    it('returns city label for accurate location without displayName', function() {
      const loc = makeLocation({
        city: 'Chennai',
        state: 'Tamil Nadu',
        accuracy: 100,
      });
      expect(formatLocationSubtitle(loc)).toBe('Chennai, Tamil Nadu');
    });
  });
});


