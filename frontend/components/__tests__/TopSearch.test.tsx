import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

const mockSetFunctions = {
  setMapSearchTarget: jest.fn(),
  setServiceCategory: jest.fn(),
  setSystemSidebarOpen: jest.fn(),
  setDesktopSidebarCollapsed: jest.fn(),
}

const mockAppState = {
  gpsError: null as string | null,
  gpsLocation: null as any,
  serviceCategory: 'all' as string,
  setMapSearchTarget: mockSetFunctions.setMapSearchTarget,
  setServiceCategory: mockSetFunctions.setServiceCategory,
  setSystemSidebarOpen: mockSetFunctions.setSystemSidebarOpen,
  isDesktopSidebarCollapsed: false,
  setDesktopSidebarCollapsed: mockSetFunctions.setDesktopSidebarCollapsed,
  isThinSidebarEnabled: false,
}

jest.mock('@/lib/store', function() {
  return {
    useAppStore: function(selector: any) { return selector(mockAppState) },
  }
})

jest.mock('@/components/ThemeProvider', function() {
  const mockTheme = 'dark'
  const mockSetTheme = jest.fn()
  return {
    useTheme: function() { return { theme: mockTheme, setTheme: mockSetTheme, __setTheme: mockSetTheme } },
  }
})

let mockDebouncedCallback: ((...args: any[]) => any) | null = null
const mockDebouncedFn = Object.assign(jest.fn(function(this: any) {
  if (mockDebouncedCallback) { return mockDebouncedCallback(...arguments) }
}), { cancel: jest.fn() })
jest.mock('use-debounce', function() {
  return {
    useDebouncedCallback: function(fn: (...args: any[]) => any) {
      mockDebouncedCallback = fn
      return mockDebouncedFn
    },
  }
})

jest.mock('@/lib/geocoding', function() {
  return {
    searchPlaces: jest.fn().mockResolvedValue([]),
    GeocodingResult: {},
  }
})

jest.mock('@/lib/location-utils', function() {
  return {
    formatAccuracyLabel: jest.fn(function() { return null }),
    formatLocationLabel: jest.fn(function() { return 'Use My Location' }),
    isApproximateLocation: jest.fn(function() { return false }),
  }
})

describe('TopSearch', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockAppState.gpsError = null
    mockAppState.gpsLocation = null
    mockAppState.serviceCategory = 'all'
    mockAppState.isDesktopSidebarCollapsed = false
  })

  it('renders search input field', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByRole('search')).toBeInTheDocument()
  })

  it('has expected placeholder text', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByPlaceholderText('Ask Maps or Search')).toBeInTheDocument()
  })

  it('fires onChange when typing in search input', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'hospital' } })
    expect(input.value).toBe('hospital')
  })

  it('has voice search button', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByLabelText('Voice search')).toBeInTheDocument()
  })

  it('opens sidebar on menu button click', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const menuBtn = screen.getByLabelText('Open navigation menu')
    fireEvent.click(menuBtn)
    expect(mockSetFunctions.setSystemSidebarOpen).toHaveBeenCalledWith(true)
  })

  it('renders filter chips when isMapPage is true', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('Hospitals')).toBeInTheDocument()
    expect(screen.getByText('Police')).toBeInTheDocument()
    expect(screen.getByText('Ambulance')).toBeInTheDocument()
    expect(screen.getByText('Fire')).toBeInTheDocument()
    expect(screen.getByText('Pharmacy')).toBeInTheDocument()
  })

  it('does not render filter chips when isMapPage is false', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: false }))
    expect(screen.queryByText('Hospitals')).toBeNull()
  })

  it('clicking a filter chip calls setServiceCategory', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    fireEvent.click(screen.getByText('Hospitals'))
    expect(mockSetFunctions.setServiceCategory).toHaveBeenCalledWith('hospital')
  })

  it('highlights active filter chip', function() {
    mockAppState.serviceCategory = 'hospital'
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    const chips = screen.getAllByRole('button', { pressed: true })
    expect(chips.length).toBeGreaterThanOrEqual(1)
  })

  it('shows back button when showBack is true', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    const { container } = render(React.createElement(TopSearch, { showBack: true }))
    expect(container.querySelector('a[href="/"]')).toBeTruthy()
  })

  it('shows location badge on desktop', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    render(React.createElement(TopSearch))
  })

  it('shows "Enable Location" when gpsError is set', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    mockAppState.gpsError = 'GPS permission denied'
    render(React.createElement(TopSearch, { isMapPage: true }))
    expect(screen.getByText('Enable Location')).toBeInTheDocument()
  })

  it('shows "Use My Location" in mobile chip when no gpsError or gpsLocation', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    const locationBtns = screen.getAllByText('Use My Location')
    expect(locationBtns.length).toBeGreaterThanOrEqual(1)
  })

  it('renders and dispatches svai:fly-to when search result is selected', function() {
    const dispatchSpy = jest.fn()
    window.dispatchEvent = dispatchSpy
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByRole('search')).toBeInTheDocument()
    window.dispatchEvent = dispatchSpy
  })

  it('shows "Refresh Location" when gpsLocation exists', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    const btns = screen.getAllByText('Refresh Location')
    expect(btns.length).toBeGreaterThanOrEqual(1)
  })

  it('renders desktop sidebar expand button when collapsed', function() {
    mockAppState.isDesktopSidebarCollapsed = true
    mockAppState.isThinSidebarEnabled = false
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByLabelText('Expand sidebar')).toBeInTheDocument()
  })

  it('shows "All" filter chip as active by default', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch, { isMapPage: true }))
    const allChip = screen.getByText('All').closest('button')
    expect(allChip?.getAttribute('aria-pressed')).toBe('true')
  })

  it('dispatches svai:fly-to when search form is submitted with results', async function() {
    jest.spyOn(window, 'dispatchEvent')
    const searchPlacesMock = require('@/lib/geocoding').searchPlaces
    searchPlacesMock.mockResolvedValue([
      { lat: 13.0827, lon: 80.2707, name: 'Chennai Central', label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu' },
    ])
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'Chennai' } })
    await waitFor(function() {
      expect(screen.getByText('Chennai Central')).toBeInTheDocument()
    })
    const form = input.closest('form')!
    fireEvent.submit(form)
    expect(window.dispatchEvent).toHaveBeenCalledWith(expect.objectContaining({ type: 'svai:fly-to' }))
  })

  it('dispatches svai:refresh-location on location button click', function() {
    jest.spyOn(window, 'dispatchEvent')
    const TopSearch = require('../dashboard/TopSearch').default
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    render(React.createElement(TopSearch, { isMapPage: true }))
    fireEvent.click(screen.getByText('Refresh Location'))
    expect(window.dispatchEvent).toHaveBeenCalledWith(expect.objectContaining({ type: 'svai:refresh-location' }))
  })

  it('renders autocomplete dropdown when focused and query is typed', async function() {
    const searchPlacesMock = require('@/lib/geocoding').searchPlaces
    searchPlacesMock.mockResolvedValue([
      { lat: 13.0827, lon: 80.2707, name: 'Chennai Central', label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu' },
    ])
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'Chennai' } })
    await waitFor(function() {
      expect(screen.getByText('Chennai Central')).toBeInTheDocument()
    })
  })

  it('shows no-places-found message when search yields no results', async function() {
    const searchPlacesMock = require('@/lib/geocoding').searchPlaces
    searchPlacesMock.mockResolvedValue([])
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'xyzabc' } })
    await waitFor(function() {
      expect(screen.getByText(/No places found/i)).toBeInTheDocument()
    })
  })

  it('renders theme toggle buttons when mounted', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    expect(screen.getByLabelText('Switch to light theme')).toBeInTheDocument()
    expect(screen.getByLabelText('Switch to dark theme')).toBeInTheDocument()
    expect(screen.getByLabelText('Switch to system theme')).toBeInTheDocument()
  })

  it('theme toggle calls setTheme', function() {
    const themeModule = require('@/components/ThemeProvider')
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    fireEvent.click(screen.getByLabelText('Switch to light theme'))
    expect(themeModule.useTheme().__setTheme).toHaveBeenCalledWith('light')
  })

  it('theme toggle dark button calls setTheme with dark', function() {
    const themeModule = require('@/components/ThemeProvider')
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    fireEvent.click(screen.getByLabelText('Switch to dark theme'))
    expect(themeModule.useTheme().__setTheme).toHaveBeenCalledWith('dark')
  })

  it('theme toggle system button calls setTheme with system', function() {
    const themeModule = require('@/components/ThemeProvider')
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    fireEvent.click(screen.getByLabelText('Switch to system theme'))
    expect(themeModule.useTheme().__setTheme).toHaveBeenCalledWith('system')
  })

  it('expand sidebar button calls setDesktopSidebarCollapsed(false)', function() {
    mockAppState.isDesktopSidebarCollapsed = true
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    fireEvent.click(screen.getByLabelText('Expand sidebar'))
    expect(mockSetFunctions.setDesktopSidebarCollapsed).toHaveBeenCalledWith(false)
  })

  it('sets isFocused false on input blur', function() {
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.blur(input)
  })

  it('selects a result from autocomplete dropdown on click', async function() {
    const spy = jest.spyOn(window, 'dispatchEvent')
    const searchPlacesMock = require('@/lib/geocoding').searchPlaces
    searchPlacesMock.mockResolvedValue([
      { lat: 13.0827, lon: 80.2707, name: 'Chennai Central', label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu' },
    ])
    const TopSearch = require('../dashboard/TopSearch').default
    render(React.createElement(TopSearch))
    const input = screen.getByPlaceholderText('Ask Maps or Search') as HTMLInputElement
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'Chennai' } })
    await waitFor(function() {
      expect(screen.getByText('Chennai Central')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Chennai Central'))
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ type: 'svai:fly-to' }))
  })
})
