import { render, screen, act, waitFor } from '@testing-library/react'
import React from 'react'
import maplibregl from 'maplibre-gl'
import MapLibreDashboard from '../command-center/MapLibreDashboard'

jest.mock('maplibre-gl', function() {
  const fakeCanvas = { style: {} }
  return {
    Map: jest.fn(function() { return {
      on: jest.fn(),
      remove: jest.fn(),
      resize: jest.fn(),
      getCenter: jest.fn(function() { return { lat: 0, lng: 0 } }),
      getZoom: jest.fn(function() { return 5 }),
      setCenter: jest.fn(),
      setZoom: jest.fn(),
      flyTo: jest.fn(),
      addSource: jest.fn(),
      addLayer: jest.fn(),
      removeLayer: jest.fn(),
      removeSource: jest.fn(),
      getSource: jest.fn(),
      getLayer: jest.fn(),
      project: jest.fn(function() { return { x: 0, y: 0 } }),
      unproject: jest.fn(function() { return { lat: 0, lng: 0 } }),
      getBounds: jest.fn(function() { return { getNorth: function() { return 1 }, getSouth: function() { return -1 }, getEast: function() { return 1 }, getWest: function() { return -1 } } }),
      fitBounds: jest.fn(),
      once: jest.fn(),
      off: jest.fn(),
      getCanvas: jest.fn(function() { return fakeCanvas }),
      loaded: jest.fn(function() { return true }),
    } }),
    Popup: jest.fn(function() { return {
      setLngLat: jest.fn().mockReturnThis(),
      setHTML: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
    } }),
    NavigationControl: jest.fn(),
    Marker: jest.fn(function() { return {
      setLngLat: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      on: jest.fn().mockReturnThis(),
      remove: jest.fn(),
    } }),
  }
})

jest.mock('@/lib/api', function() {
  return {
    client: {
      get: jest.fn().mockResolvedValue({ data: { type: 'FeatureCollection', features: [] } }),
    },
  }
}, { virtual: false })

describe('MapLibreDashboard', function() {
  beforeEach(function() {
    jest.clearAllMocks()
  })

  it('shows loading state initially', function() {
    render(React.createElement(MapLibreDashboard))
    expect(screen.getByText('Acquiring GIS Feeds...')).toBeInTheDocument()
  })

  it('renders map container', function() {
    render(React.createElement(MapLibreDashboard))
    expect(screen.getByText('Acquiring GIS Feeds...')).toBeInTheDocument()
  })

  it('has full width and height classes', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    const outer = container.firstChild as HTMLElement
    expect(outer.className).toContain('w-full')
    expect(outer.className).toContain('h-full')
  })

  it('renders with activeCategory prop', function() {
    render(React.createElement(MapLibreDashboard, { activeCategory: 'roads' }))
    expect(screen.getByText('Acquiring GIS Feeds...')).toBeInTheDocument()
  })

  it('has loading overlay with absolute positioning', function() {
    render(React.createElement(MapLibreDashboard))
    const loadingText = screen.getByText('Acquiring GIS Feeds...')
    expect(loadingText.closest('.absolute')).toBeTruthy()
  })

  it('has map container ref div', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    const innerDiv = container.querySelector('[class*="overflow-hidden"]')
    expect(innerDiv).toBeInTheDocument()
  })

  it('renders Loader2 icon in loading state', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('has loading overlay behind map', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    const loadingOverlay = container.querySelector('.absolute.inset-0')
    expect(loadingOverlay).toBeInTheDocument()
  })

  it('applies rounded corners to map container', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    const mapDiv = container.querySelector('[class*="rounded-\\[1\\.8rem\\]"]')
    expect(mapDiv).toBeInTheDocument()
  })

  it('renders with relative positioning wrapper', function() {
    const { container } = render(React.createElement(MapLibreDashboard))
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('relative')
  })

  it('cleans up map on unmount', function() {
    const { unmount } = render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    unmount()
    expect(mapMock.remove).toHaveBeenCalled()
  })

  it('triggers map load handler and adds source', async function() {
    render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    expect(loadHandler).toBeDefined()
    await act(async function() { await loadHandler() })
    expect(mapMock.addSource).toHaveBeenCalledWith('complaints', expect.any(Object))
    expect(mapMock.addLayer).toHaveBeenCalled()
    await waitFor(function() { expect(screen.queryByText('Acquiring GIS Feeds...')).toBeNull() })
  })

  it('passes activeCategory param to API', async function() {
    const { client } = require('@/lib/api')
    render(React.createElement(MapLibreDashboard, { activeCategory: 'roads' }))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    await act(async function() { await loadHandler() })
    expect(client.get).toHaveBeenCalledWith('/api/v1/analytics/heatmap', { params: { category: 'roads' } })
  })

  it('handles API error on map load', async function() {
    const { client } = require('@/lib/api')
    client.get.mockRejectedValueOnce(new Error('API error'))
    render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    await act(async function() { await loadHandler() })
    expect(mapMock.addSource).not.toHaveBeenCalled()
  })

  it('opens popup on complaints-point click', async function() {
    render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    await act(async function() { await loadHandler() })
    const clickHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'click' })?.[2]
    expect(clickHandler).toBeDefined()
    clickHandler({
      features: [{
        geometry: { coordinates: [80.2707, 13.0827] },
        properties: { severity: 4, category: 'roads', uuid: 'abc12345-xxxx' },
      }],
      lngLat: { lng: 80.2707, lat: 13.0827 },
    })
    expect(maplibregl.Popup).toHaveBeenCalledWith({ className: 'custom-maplibre-popup' })
    expect((maplibregl.Popup as jest.Mock).mock.results[0].value.setHTML).toHaveBeenCalled()
    expect((maplibregl.Popup as jest.Mock).mock.results[0].value.addTo).toHaveBeenCalled()
  })

  it('changes cursor on complaints-point mouseenter', async function() {
    render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    await act(async function() { await loadHandler() })
    const enterHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'mouseenter' })?.[2]
    expect(enterHandler).toBeDefined()
    enterHandler()
    expect(mapMock.getCanvas().style.cursor).toBe('pointer')
  })

  it('resets cursor on complaints-point mouseleave', async function() {
    render(React.createElement(MapLibreDashboard))
    const mapMock = (maplibregl.Map as jest.Mock).mock.results[0].value
    const loadHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'load' })?.[1]
    await act(async function() { await loadHandler() })
    const leaveHandler = mapMock.on.mock.calls.find(function(c: any[]) { return c[0] === 'mouseleave' })?.[2]
    expect(leaveHandler).toBeDefined()
    leaveHandler()
    expect(mapMock.getCanvas().style.cursor).toBe('')
  })
})
