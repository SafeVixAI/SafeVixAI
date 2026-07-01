jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/components/report/ReportProgressBar', function() { return { ReportProgressBar: function() { return null } } })
jest.mock('@/components/report/HazardViewfinder', function() { return function() { return null } })
jest.mock('@/components/report/LocationPicker', function() { return function() { return null } })
jest.mock('@/lib/validate-upload', function() { return { validateImageFile: jest.fn(), compressImageFile: jest.fn() } })
jest.mock('@/lib/api', function() {
  return {
    client: { get: jest.fn().mockResolvedValue({ data: {} }), post: jest.fn().mockResolvedValue({ data: {} }) },
    fetchAuthorityPreview: jest.fn().mockResolvedValue(null),
    fetchRoadInfrastructure: jest.fn().mockResolvedValue(null),
    reverseGeocode: jest.fn().mockResolvedValue(null),
    submitReport: jest.fn().mockResolvedValue(null),
  }
})
jest.mock('@/lib/geolocation', function() { return { useGeolocation: function() { return { location: null, error: null, loading: false, refresh: function() {} } } } })
jest.mock('@/lib/location-utils', function() { return { formatAccuracyLabel: function() { return '' }, formatLocationLabel: function() { return '' }, formatLocationSubtitle: function() { return '' }, isApproximateLocation: function() { return false } } })
jest.mock('@/hooks/useSwipe', function() { return { useSwipe: function() { return { onTouchStart: function() {}, onTouchEnd: function() {} } } } })
jest.mock('@/lib/store', function() { return { useSetGpsLocation: function() { return function() {} } } })
jest.mock('@/lib/analytics', function() { return { track: jest.fn() } })
jest.mock('next/link', function() { return function({ children, ...rest }) { var React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('next/image', function() { return function(props) { return null } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen } from '@testing-library/react'
import React from 'react'
import ReportPage from '../app/report/page'

describe('ReportPage', function() {
  it('renders without error', function() {
    var { container } = render(React.createElement(ReportPage))
    expect(container).toBeTruthy()
  })

  it('renders heading section', function() {
    var { container } = render(React.createElement(ReportPage))
    expect(container.querySelector('main')).toBeTruthy()
  })

  it('renders with page wrapper ref', function() {
    var { container } = render(React.createElement(ReportPage))
    expect(container.querySelector('[class*="sv-page"]')).toBeTruthy()
  })

  it('renders ambient glow effects', function() {
    var { container } = render(React.createElement(ReportPage))
    expect(container.querySelector('[class*="blur-"]')).toBeTruthy()
  })
})
