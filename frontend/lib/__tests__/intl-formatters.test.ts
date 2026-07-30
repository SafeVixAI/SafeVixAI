// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

let mockLanguage = 'en';

jest.mock('../i18n', () => ({
  __esModule: true,
  default: {
    get language() { return mockLanguage; },
  },
}));

import {
  getLocale,
  formatNumber,
  formatCurrency,
  formatDecimal,
  formatCompactNumber,
  formatDistance,
  formatDuration,
  formatCoordinate,
  formatDate,
  formatTime,
  formatDateTime,
  formatRelativeTime,
} from '../intl-formatters';

describe('intl-formatters', function() {
  beforeEach(function() {
    mockLanguage = 'en';
  });

  // ── getLocale ──

  describe('getLocale', function() {
    it('returns en-IN for English', function() {
      expect(getLocale()).toBe('en-IN');
    });

    it('returns hi-IN for Hindi', function() {
      mockLanguage = 'hi';
      expect(getLocale()).toBe('hi-IN');
    });

    it('returns ta-IN for Tamil', function() {
      mockLanguage = 'ta';
      expect(getLocale()).toBe('ta-IN');
    });

    it('returns ur-PK for Urdu', function() {
      mockLanguage = 'ur';
      expect(getLocale()).toBe('ur-PK');
    });

    it('returns en-IN for unknown language', function() {
      mockLanguage = 'zz';
      expect(getLocale()).toBe('en-IN');
    });
  });

  // ── formatNumber ──

  describe('formatNumber', function() {
    it('formats a small number', function() {
      expect(formatNumber(42)).toBe('42');
    });

    it('formats a number with Indian grouping separators', function() {
      const result = formatNumber(1234567);
      expect(result).toMatch(/\d{2}[,.]\d{2}[,.]\d{3}/);
    });

    it('formats zero', function() {
      expect(formatNumber(0)).toBe('0');
    });

    it('formats a negative number', function() {
      const result = formatNumber(-500);
      expect(result).toContain('500');
    });

    it('formats a decimal number', function() {
      const result = formatNumber(3.14);
      expect(result).toMatch(/3[.,]14/);
    });
  });

  // ── formatCurrency ──

  describe('formatCurrency', function() {
    it('formats amount with ₹ symbol', function() {
      const result = formatCurrency(500);
      expect(result).toMatch(/₹/);
    });

    it('formats zero amount', function() {
      const result = formatCurrency(0);
      expect(result).toMatch(/0/);
    });

    it('formats a large fine amount', function() {
      const result = formatCurrency(25000);
      expect(result).toMatch(/₹/);
    });

    it('produces no decimal fraction digits', function() {
      const result = formatCurrency(100);
      expect(result).not.toMatch(/\.\d{2}/);
    });

    it('formats negative amount', function() {
      const result = formatCurrency(-1000);
      expect(result).toMatch(/₹/);
    });
  });

  // ── formatDecimal ──

  describe('formatDecimal', function() {
    it('formats with default 1 decimal place', function() {
      const result = formatDecimal(3.456);
      expect(result).toMatch(/3[.,]/);
    });

    it('formats with custom decimal places', function() {
      const result = formatDecimal(3.456, 3);
      expect(result).toMatch(/3[.,]456/);
    });

    it('formats zero', function() {
      expect(formatDecimal(0, 1)).toBe('0.0');
    });

    it('rounds to specified decimals', function() {
      const result = formatDecimal(2.999, 0);
      expect(result).toBe('3');
    });

    it('formats with 0 decimal places', function() {
      expect(formatDecimal(42.7, 0)).toBe('43');
    });
  });

  // ── formatCompactNumber ──

  describe('formatCompactNumber', function() {
    it('formats crore values', function() {
      expect(formatCompactNumber(15000000)).toMatch(/ Cr$/);
    });

    it('formats lakh values', function() {
      expect(formatCompactNumber(500000)).toMatch(/ L$/);
    });

    it('formats thousand values', function() {
      expect(formatCompactNumber(5000)).toMatch(/ K$/);
    });

    it('returns plain number for values under 1000', function() {
      expect(formatCompactNumber(999)).toBe('999');
    });

    it('formats zero', function() {
      expect(formatCompactNumber(0)).toBe('0');
    });

    it('formats exact crore boundary', function() {
      expect(formatCompactNumber(10000000)).toMatch(/ Cr$/);
    });

    it('formats exact lakh boundary', function() {
      expect(formatCompactNumber(100000)).toMatch(/ L$/);
    });

    it('formats non-round lakh value', function() {
      const result = formatCompactNumber(250500);
      expect(result).toMatch(/ L$/);
    });

    it('formats non-round thousand value', function() {
      const result = formatCompactNumber(2500);
      expect(result).toMatch(/ K$/);
    });
  });

  // ── formatDistance ──

  describe('formatDistance', function() {
    it('formats kilometers for >= 1000m', function() {
      expect(formatDistance(1500)).toMatch(/ km$/);
    });

    it('formats meters for < 1000m', function() {
      expect(formatDistance(500)).toMatch(/ m$/);
    });

    it('formats zero meters', function() {
      expect(formatDistance(0)).toMatch(/ m$/);
    });

    it('formats exact 1km', function() {
      expect(formatDistance(1000)).toMatch(/ km$/);
    });

    it('formats large distance in kilometers', function() {
      expect(formatDistance(12345)).toMatch(/ km$/);
    });
  });

  // ── formatDuration ──

  describe('formatDuration', function() {
    it('formats hours and minutes', function() {
      expect(formatDuration(3661)).toMatch(/hr/);
    });

    it('formats only hours when minutes are zero', function() {
      const result = formatDuration(7200);
      expect(result).toContain('hr');
      expect(result).not.toContain('min');
    });

    it('formats only minutes for < 1 hour', function() {
      expect(formatDuration(300)).toMatch(/min/);
    });

    it('formats seconds for < 1 minute', function() {
      expect(formatDuration(45)).toMatch(/sec/);
    });

    it('formats zero seconds', function() {
      expect(formatDuration(0)).toMatch(/sec/);
    });

    it('formats exactly 1 hour', function() {
      expect(formatDuration(3600)).toContain('hr');
    });
  });

  // ── formatCoordinate ──

  describe('formatCoordinate', function() {
    it('formats lat/lon with 4 decimal places', function() {
      const result = formatCoordinate(13.0827, 80.2707);
      expect(result).toMatch(/13\.\d{4}, 80\.\d{4}/);
    });

    it('formats negative coordinates', function() {
      const result = formatCoordinate(-33.8688, 151.2093);
      expect(result).toContain(',');
    });

    it('formats zero coordinate', function() {
      expect(formatCoordinate(0, 0)).toBe('0.0000, 0.0000');
    });
  });

  // ── formatDate ──

  describe('formatDate', function() {
    it('formats a Date object', function() {
      const d = new Date(2026, 5, 22);
      const result = formatDate(d);
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a date string', function() {
      const result = formatDate('2026-06-22');
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a timestamp number', function() {
      const result = formatDate(1769000000000);
      expect(result.length).toBeGreaterThan(0);
    });

    it('returns string for invalid date', function() {
      const result = formatDate('not-a-date');
      expect(typeof result).toBe('string');
    });
  });

  // ── formatTime ──

  describe('formatTime', function() {
    it('formats time with hours and minutes', function() {
      const d = new Date(2026, 5, 22, 14, 30, 0);
      const result = formatTime(d);
      expect(result).toMatch(/:/);
    });

    it('formats a date string', function() {
      const result = formatTime('2026-06-22T09:15:00');
      expect(result).toMatch(/:/);
    });

    it('formats a timestamp number', function() {
      const result = formatTime(1769000000000);
      expect(typeof result).toBe('string');
    });
  });

  // ── formatDateTime ──

  describe('formatDateTime', function() {
    it('formats datetime with date and time', function() {
      const d = new Date(2026, 5, 22, 14, 30, 0);
      const result = formatDateTime(d);
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a date string', function() {
      const result = formatDateTime('2026-06-22T09:15:00');
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a timestamp number', function() {
      const result = formatDateTime(1769000000000);
      expect(typeof result).toBe('string');
    });
  });

  // ── formatRelativeTime ──

  describe('formatRelativeTime', function() {
    it('returns "now" for current time', function() {
      const result = formatRelativeTime(new Date());
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a past date', function() {
      const past = new Date(Date.now() - 60000);
      const result = formatRelativeTime(past);
      expect(result.length).toBeGreaterThan(0);
    });

    it('formats a future date', function() {
      const future = new Date(Date.now() + 3600000);
      const result = formatRelativeTime(future);
      expect(result.length).toBeGreaterThan(0);
    });

    it('handles a date string input', function() {
      const past = new Date(Date.now() - 86400000);
      const result = formatRelativeTime(past.toISOString());
      expect(result.length).toBeGreaterThan(0);
    });

    it('handles a timestamp number input', function() {
      const past = Date.now() - 7200000;
      const result = formatRelativeTime(past);
      expect(result.length).toBeGreaterThan(0);
    });
  });

  // ── Catch block fallbacks ──

  describe('catch block fallbacks', function() {
    afterEach(function() {
      jest.restoreAllMocks();
    });

    it('formatNumber falls back to toLocaleString when Intl.NumberFormat throws (line 38)', function() {
      jest.spyOn(Intl, 'NumberFormat').mockImplementation(function() { throw new Error('mock'); });
      expect(formatNumber(42)).toBe('42');
    });

    it('formatCurrency falls back when Intl.NumberFormat throws (line 53)', function() {
      jest.spyOn(Intl, 'NumberFormat').mockImplementation(function() { throw new Error('mock'); });
      const result = formatCurrency(500);
      expect(result).toMatch(/₹/);
      expect(result).toContain('500');
    });

    it('formatDecimal falls back to toFixed when Intl.NumberFormat throws (line 67)', function() {
      jest.spyOn(Intl, 'NumberFormat').mockImplementation(function() { throw new Error('mock'); });
      expect(formatDecimal(3.456, 1)).toBe('3.5');
    });

    it('formatTime falls back to toTimeString when Intl.DateTimeFormat throws (line 154)', function() {
      jest.spyOn(Intl, 'DateTimeFormat').mockImplementation(function() { throw new Error('mock'); });
      const d = new Date(2026, 5, 22, 14, 30, 0);
      const result = formatTime(d);
      expect(result).toMatch(/14:30/);
    });

    it('formatDateTime falls back when Intl.DateTimeFormat throws (lines 168-169)', function() {
      jest.spyOn(Intl, 'DateTimeFormat').mockImplementation(function() { throw new Error('mock'); });
      const d = new Date(2026, 5, 22, 14, 30, 0);
      const result = formatDateTime(d);
      expect(result).toMatch(/Jun/);
    });

    it('formatRelativeTime falls back when Intl.RelativeTimeFormat throws (lines 203-210)', function() {
      jest.spyOn(Intl, 'RelativeTimeFormat').mockImplementation(function() { throw new Error('mock'); });
      const past = new Date(Date.now() - 60000);
      const result = formatRelativeTime(past);
      expect(result).toMatch(/min ago|just now/);
    });

    it('formatRelativeTime catch block returns hr ago for 2-hour gap', function() {
      jest.spyOn(Intl, 'RelativeTimeFormat').mockImplementation(function() { throw new Error('mock'); });
      const past = new Date(Date.now() - 7200000);
      const result = formatRelativeTime(past);
      expect(result).toMatch(/hr ago/);
    });

    it('formatRelativeTime catch block returns toLocaleDateString for 3-day gap', function() {
      jest.spyOn(Intl, 'RelativeTimeFormat').mockImplementation(function() { throw new Error('mock'); });
      const past = new Date(Date.now() - 259200000);
      const result = formatRelativeTime(past);
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('getLocale', function() {
    it('falls back to en when language is falsy', function() {
      mockLanguage = null;
      expect(getLocale()).toBe('en-IN');
    });
  });
});
