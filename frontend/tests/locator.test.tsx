jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/api', function() { return { client: { get: jest.fn().mockResolvedValue({ data: {} }), post: jest.fn().mockResolvedValue({ data: {} }) }, RouteOption: undefined, RoutePreviewResponse: undefined } })
jest.mock('@/components/dashboard/DashboardMapBootstrap', function() { return function() { return null } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/ui/SkeletonCard', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('@/lib/emergency-numbers', function() { return { PRIMARY_EMERGENCY_BAR: [] } })
jest.mock('@/hooks/useLocatorSearch', function() {
  return {
    useLocatorSearch: function() {
      return {
        coords: [0, 0],
        gpsLocation: null,
        address: '',
        filtered: [],
        locating: false,
        serviceSearchMeta: {},
        coverageSummary: '5 services within 2 km',
        activeFilter: 'All',
        setActiveFilter: function() {},
        activeRoute: null,
        activeRouteOption: null,
        alternativeRoutes: [],
        routeError: null,
        routeLoadingId: null,
        selectedServiceId: null,
        selectedService: null,
        navigationHref: null,
        selectedRouteId: null,
        rerouting: false,
        handleLocateService: function() {},
        handleSelectRoute: function() {},
        handlePreviewService: function() {},
      }
    }
  }
})
jest.mock('@/hooks/useSwipe', function() {
  return {
    useSwipe: function() {
      return { onTouchStart: function() {}, onTouchEnd: function() {} }
    }
  }
})
jest.mock('../app/locator/components/LocatorFilters', function() { return { LocatorFilters: function() { return null } } })
jest.mock('../app/locator/components/LocatorMap', function() { return { LocatorMap: function() { return null } } })
jest.mock('../app/locator/components/LocatorResults', function() { return { DesktopResultsList: function() { return null }, MobileResultsList: function() { return null } } })
jest.mock('../app/locator/locator-components', function() { return { EmptyState: function() { return null }, RouteStatusCard: function() { return null } } })
jest.mock('../app/locator/locator-utils', function() { return {} })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const Page = require('../app/locator/page').default

describe('LocatorPage', function() {
  it('renders Emergency Locator sr-only heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Emergency Locator')).toBeTruthy()
  })

  it('renders coverage summary from hook', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('5 services within 2 km')).toBeTruthy()
  })

  it('renders mobile locator container', function() {
    const { container } = render(React.createElement(Page))
    expect(container).toBeTruthy()
    expect(container.querySelector('main') || container.querySelector('div[class*="locator"]')).toBeTruthy()
  })

  it('renders with translation context', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Emergency Locator')).toBeTruthy()
  })
})
