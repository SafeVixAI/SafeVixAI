import { formatDistance, formatCoverageRadius, buildNavigationHref, formatDuration, haversineMeters, minimumRouteDeviationMeters, mapService, fallbackNumber } from '@/app/locator/locator-utils'

describe('locator-utils', function() {
  describe('formatDistance', function() {
    it('formats meters as "X m"', function() { expect(formatDistance(500)).toBe('500 m') })
    it('formats 999m as "999 m"', function() { expect(formatDistance(999)).toBe('999 m') })
    it('formats 1000m as "1.0 km"', function() { expect(formatDistance(1000)).toBe('1.0 km') })
    it('formats 1500m as "1.5 km"', function() { expect(formatDistance(1500)).toBe('1.5 km') })
    it('formats 0m', function() { expect(formatDistance(0)).toBe('0 m') })
  })

  describe('formatCoverageRadius', function() {
    it('formats meters under 1000', function() { expect(formatCoverageRadius(800)).toBe('800 m') })
    it('formats 1000m as "1 km"', function() { expect(formatCoverageRadius(1000)).toBe('1 km') })
    it('formats 5000m as "5 km"', function() { expect(formatCoverageRadius(5000)).toBe('5 km') })
  })

  describe('buildNavigationHref', function() {
    it('builds Google Maps URL with origin and destination', function() {
      const url = buildNavigationHref([12.9716, 77.5946], [13.0827, 80.2707])
      expect(url).toContain('google.com/maps/dir/')
      expect(url).toContain('origin=12.9716%2C77.5946')
      expect(url).toContain('destination=13.0827%2C80.2707')
      expect(url).toContain('travelmode=driving')
    })
  })

  describe('formatDuration', function() {
    it('formats 0s as "1 min"', function() { expect(formatDuration(0)).toBe('1 min') })
    it('formats 60s as "1 min"', function() { expect(formatDuration(60)).toBe('1 min') })
    it('formats 3000s as "50 min"', function() { expect(formatDuration(3000)).toBe('50 min') })
    it('formats 3600s as "1 hr"', function() { expect(formatDuration(3600)).toBe('1 hr') })
    it('formats 5400s as "1 hr 30 min"', function() { expect(formatDuration(5400)).toBe('1 hr 30 min') })
  })

  describe('haversineMeters', function() {
    it('returns 0 for same point', function() { expect(haversineMeters([13, 80], [13, 80])).toBe(0) })
    it('returns ~111km for 1 degree latitude', function() {
      const dist = haversineMeters([0, 0], [1, 0])
      expect(dist).toBeGreaterThan(110000)
      expect(dist).toBeLessThan(112000)
    })
  })

  describe('minimumRouteDeviationMeters', function() {
    it('returns Infinity for empty path', function() { expect(minimumRouteDeviationMeters({ path: [] }, [13, 80])).toBe(Number.POSITIVE_INFINITY) })

    it('returns minimum distance to any route point', function() {
      const route = { path: [{ lat: 13.0, lon: 80.0 }, { lat: 13.1, lon: 80.1 }] }
      const dist = minimumRouteDeviationMeters(route, [13.0, 80.0])
      expect(dist).toBe(0)
    })
  })

  describe('mapService', function() {
    const base = { id: 's1', name: 'Test', distance: 500, address: 'Addr', lat: 13, lon: 80, phone: '123', category: 'hospital' as const }

    it('maps hospital category', function() {
      const result = mapService(base)
      expect(result.type).toBe('Hospital')
      expect(result.accentColor).toBe('#ef4444')
      expect(result.filterType).toBe('Hospital')
    })

    it('maps ambulance category', function() {
      const result = mapService({ ...base, category: 'ambulance' as const })
      expect(result.type).toBe('Ambulance')
      expect(result.accentColor).toBe('#10b981')
    })

    it('maps police category', function() {
      const result = mapService({ ...base, category: 'police' as const })
      expect(result.type).toBe('Police')
      expect(result.accentColor).toBe('#3b82f6')
    })

    it('maps fire category', function() {
      const result = mapService({ ...base, category: 'fire' as const })
      expect(result.type).toBe('Fire')
      expect(result.accentColor).toBe('#f97316')
    })

    it('maps towing category', function() {
      const result = mapService({ ...base, category: 'towing' as const })
      expect(result.type).toBe('Towing')
      expect(result.accentColor).toBe('#f59e0b')
    })

    it('maps pharmacy category', function() {
      const result = mapService({ ...base, category: 'pharmacy' as const })
      expect(result.type).toBe('Pharmacy')
      expect(result.accentColor).toBe('#06b6d4')
    })

    it('maps unknown category to Mechanic', function() {
      const result = mapService({ ...base, category: 'showroom' as any })
      expect(result.type).toBe('Mechanic')
      expect(result.accentColor).toBe('#8b5cf6')
    })

    it('maps puncture category to Mechanic', function() {
      const result = mapService({ ...base, category: 'puncture' as any })
      expect(result.type).toBe('Mechanic')
      expect(result.filterType).toBe('Mechanic')
    })
  })

  describe('fallbackNumber', function() {
    it('returns "108" for Hospital', function() { expect(fallbackNumber('Hospital')).toBe('108') })
    it('returns "100" for Police', function() { expect(fallbackNumber('Police')).toBe('100') })
    it('returns "101" for Fire', function() { expect(fallbackNumber('Fire')).toBe('101') })
    it('returns "1033" for Mechanic', function() { expect(fallbackNumber('Mechanic')).toBe('1033') })
    it('returns "1033" for Towing', function() { expect(fallbackNumber('Towing')).toBe('1033') })
  })
})
