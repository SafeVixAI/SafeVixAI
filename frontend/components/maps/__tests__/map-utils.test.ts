import React from 'react' // eslint-disable-line @typescript-eslint/no-unused-vars

var utils = require('../map-utils')

describe('map-utils', function () {

  describe('iconForType', function () {
    it('returns H for hospital', function () {
      expect(utils.iconForType('hospital')).toBe('H')
    })

    it('returns A for ambulance', function () {
      expect(utils.iconForType('ambulance')).toBe('A')
    })

    it('returns Rx for pharmacy', function () {
      expect(utils.iconForType('pharmacy')).toBe('Rx')
    })

    it('returns P for police', function () {
      expect(utils.iconForType('police_station')).toBe('P')
    })

    it('returns F for fire', function () {
      expect(utils.iconForType('fire_station')).toBe('F')
    })

    it('returns T for tow', function () {
      expect(utils.iconForType('towing_service')).toBe('T')
    })

    it('returns M for mechanic', function () {
      expect(utils.iconForType('mechanic')).toBe('M')
    })

    it('returns L for unknown types', function () {
      expect(utils.iconForType('school')).toBe('L')
    })

    it('is case insensitive', function () {
      expect(utils.iconForType('Hospital')).toBe('H')
      expect(utils.iconForType('AMBULANCE')).toBe('A')
    })
  })

  describe('buildFacilityCollection', function () {
    var facilities = [
      { id: 'f1', name: 'City Hospital', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' },
      { id: 'f2', name: 'Police HQ', type: 'police', coords: [13.1, 80.1], accentColor: '#2563eb' },
    ]

    it('returns a FeatureCollection', function () {
      var result = utils.buildFacilityCollection(facilities, null)
      expect(result.type).toBe('FeatureCollection')
      expect(Array.isArray(result.features)).toBe(true)
    })

    it('creates features for each facility', function () {
      var result = utils.buildFacilityCollection(facilities, null)
      expect(result.features).toHaveLength(2)
    })

    it('sets selected property to 1 for selected facility', function () {
      var result = utils.buildFacilityCollection(facilities, 'f1')
      var f1 = result.features.find(function(f) { return f.properties.id === 'f1' })
      expect(f1.properties.selected).toBe(1)
      var f2 = result.features.find(function(f) { return f.properties.id === 'f2' })
      expect(f2.properties.selected).toBe(0)
    })

    it('coordinate order is [lon, lat]', function () {
      var result = utils.buildFacilityCollection(facilities, null)
      expect(result.features[0].geometry.coordinates).toEqual([80.0, 13.0])
    })

    it('filters out facilities without coords', function () {
      var bad = { id: 'f3', name: 'Bad', type: 'unknown', coords: null, accentColor: '#fff' }
      var result = utils.buildFacilityCollection(facilities.concat([bad]), null)
      expect(result.features).toHaveLength(2)
    })

    it('resolves icon via iconForType when not provided', function () {
      var result = utils.buildFacilityCollection(facilities, null)
      expect(result.features[0].properties.icon).toBe('H')
    })

    it('uses custom icon when provided', function () {
      var withIcon = [{ id: 'f3', name: 'Custom', type: 'school', coords: [12, 81], accentColor: '#fff', icon: 'X' }]
      var result = utils.buildFacilityCollection(withIcon, null)
      expect(result.features[0].properties.icon).toBe('X')
    })
  })

  describe('buildAccuracyFeature', function () {
    it('returns a Polygon Feature', function () {
      var result = utils.buildAccuracyFeature(13.0, 80.0, 100)
      expect(result.type).toBe('Feature')
      expect(result.geometry.type).toBe('Polygon')
    })

    it('generates coordinates with steps+1 points', function () {
      var result = utils.buildAccuracyFeature(13.0, 80.0, 100)
      expect(result.geometry.coordinates[0].length).toBe(49)
    })

    it('returns different shape for different accuracy', function () {
      var small = utils.buildAccuracyFeature(13.0, 80.0, 10)
      var large = utils.buildAccuracyFeature(13.0, 80.0, 1000)
      expect(small.geometry.coordinates[0]).not.toEqual(large.geometry.coordinates[0])
    })
  })

  describe('buildMarkerElement', function () {
    it('returns an HTMLDivElement', function () {
      var el = utils.buildMarkerElement({ color: '#00c896', icon: 'H', kind: 'standard' })
      expect(el instanceof HTMLDivElement).toBe(true)
    })

    it('sets aria-label for standard kind', function () {
      var el = utils.buildMarkerElement({ color: '#00c896', icon: 'H', kind: 'standard' })
      expect(el.getAttribute('aria-label')).toContain('Location: H')
    })

    it('sets aria-label for current kind', function () {
      var el = utils.buildMarkerElement({ color: '#2563eb', icon: '', kind: 'current' })
      expect(el.getAttribute('aria-label')).toContain('Your current location')
    })

    it('sets aria-label for issue kind', function () {
      var el = utils.buildMarkerElement({ color: '#ef4444', icon: '!', kind: 'issue' })
      expect(el.getAttribute('aria-label')).toContain('Issue: !')
    })

    it('includes GPS text for current kind', function () {
      var el = utils.buildMarkerElement({ color: '#2563eb', icon: '', kind: 'current' })
      expect(el.textContent).toContain('GPS')
    })

    it('applies selected transform when selected is true', function () {
      var el = utils.buildMarkerElement({ color: '#00c896', icon: 'H', kind: 'standard', selected: true })
      var shell = el.firstChild
      expect(shell.style.transform).toContain('scale(1.08)')
    })

    it('does not apply selected transform when selected is false', function () {
      var el = utils.buildMarkerElement({ color: '#00c896', icon: 'H', kind: 'standard', selected: false })
      var shell = el.firstChild
      expect(shell.style.transform).not.toContain('scale')
    })

    it('uses kind="standard" by default when kind is omitted', function () {
      var el = utils.buildMarkerElement({ color: '#00c896', icon: 'H' })
      expect(el.getAttribute('aria-label')).toContain('Location: H')
    })
  })

  describe('buildPopupContent', function () {
    it('returns an HTMLDivElement with title', function () {
      var el = utils.buildPopupContent('City Hospital')
      expect(el instanceof HTMLDivElement).toBe(true)
      expect(el.textContent).toContain('City Hospital')
    })

    it('includes overline when provided', function () {
      var el = utils.buildPopupContent('City Hospital', 'Hospital')
      expect(el.textContent).toContain('Hospital')
    })

    it('does not include overline section when not provided', function () {
      var el = utils.buildPopupContent('City Hospital')
      expect(el.childNodes.length).toBe(1)
    })

    it('renders detail rows', function () {
      var el = utils.buildPopupContent('City Hospital', null, ['Open 24/7', 'Emergency + 911'])
      expect(el.textContent).toContain('Open 24/7')
      expect(el.textContent).toContain('Emergency + 911')
    })

    it('filters out falsy detail strings while keeping valid ones', function () {
      var el = utils.buildPopupContent('City Hospital', null, ['Detail 1', '', 'Detail 3'])
      expect(el.textContent).toContain('Detail 1')
      expect(el.textContent).toContain('Detail 3')
    })
  })

  describe('constants', function () {
    it('exports ACCURACY_SOURCE_ID', function () {
      expect(utils.ACCURACY_SOURCE_ID).toBe('svai-current-location-accuracy')
    })

    it('exports ROUTE_SOURCE_ID', function () {
      expect(utils.ROUTE_SOURCE_ID).toBe('svai-active-route')
    })

    it('exports FACILITY_SOURCE_ID', function () {
      expect(utils.FACILITY_SOURCE_ID).toBe('svai-facilities')
    })

    it('exports HEATMAP_SOURCE_ID', function () {
      expect(utils.HEATMAP_SOURCE_ID).toBe('svai-heatmap-source')
    })
  })
})
