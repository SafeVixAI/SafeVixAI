import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';

// --- LocatorComponents mocks ---
const mockFormatCoverageRadius = jest.fn((m: number) => m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${m} m`);
const mockFormatDistance = jest.fn((m: number) => m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${m} m`);
const mockFormatDuration = jest.fn((s: number) => {
  const min = Math.floor(s / 60);
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
});
const mockFallbackNumber = jest.fn((_: string) => '+91-108');
const mockFilterChips: string[] = ['All', 'Hospital', 'Ambulance', 'Police', 'Fire', 'Towing', 'Mechanic', 'Pharmacy'];

jest.mock('@/app/locator/locator-utils', () => ({
  formatCoverageRadius: (...args: unknown[]) => mockFormatCoverageRadius(...args),
  formatDistance: (...args: unknown[]) => mockFormatDistance(...args),
  formatDuration: (...args: unknown[]) => mockFormatDuration(...args),
  fallbackNumber: (...args: unknown[]) => mockFallbackNumber(...args),
  FILTER_CHIPS: mockFilterChips,
  ServiceCardType: {},
  Filter: {},
  LocatorService: {},
}));

jest.mock('@/lib/api', () => ({
  RouteOption: {},
  RoutePreviewResponse: {},
}));

jest.mock('@/lib/store', () => ({
  ServiceSearchMeta: {},
}));

// --- EmergencyCardClient mocks ---
jest.mock('@/app/emergency-card/[userId]/PrintButton', () => ({
  PrintButton: function MockPrintButton() {
    return React.createElement('button', { 'data-testid': 'print-button' }, 'Print / Save');
  },
}));

// --- LocatorResults mocks ---
jest.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: () => ({
    getTotalSize: () => 760,
    getVirtualItems: () => [
      { key: 0, index: 0, start: 0, size: 190 },
      { key: 1, index: 1, start: 190, size: 190 },
    ],
  }),
}));

const mockGsapFromTo = jest.fn();
jest.mock('@/lib/gsap', () => ({
  gsap: { fromTo: (...args: unknown[]) => mockGsapFromTo(...args) },
}));

jest.mock('@gsap/react', () => ({
  useGSAP: jest.fn(),
}));

// --- LocatorMap mocks ---
jest.mock('@/components/EmergencyMap', () => ({
  EmergencyMap: function MockEmergencyMap() {
    return React.createElement('div', { 'data-testid': 'emergency-map' }, 'Map');
  },
}));

// --- Imports ---
const { ServiceIcon, EmptyState, RouteStatusCard } = require('@/app/locator/locator-components');
const { LocatorFilters } = require('@/app/locator/components/LocatorFilters');
const { LocatorMap } = require('@/app/locator/components/LocatorMap');
const { MobileResultsList, DesktopResultsList } = require('@/app/locator/components/LocatorResults');
const {
  EmergencyCardClient,
  decodeBase64Url,
  parseHashPayload,
  dialablePhone,
} = require('@/app/emergency-card/[userId]/EmergencyCardClient');

describe('locator-components', () => {
  describe('ServiceIcon', () => {
    it('renders Hospital icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Hospital' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Ambulance icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Ambulance' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Pharmacy icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Pharmacy' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Police icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Police' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Fire icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Fire' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Towing icon', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Towing' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders Mechanic icon with default', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Mechanic' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('renders unknown type with default Wrench', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Unknown' as never }));
      expect(container.querySelector('svg')).toBeTruthy();
    });
    it('applies className prop', () => {
      const { container } = render(React.createElement(ServiceIcon, { type: 'Police' as never, className: 'w-8 h-8' }));
      const svg = container.querySelector('svg');
      expect(svg?.classList.contains('w-8')).toBe(true);
    });
  });

  describe('EmptyState', () => {
    const baseMeta = { radiusUsed: 5000, count: 0 };
    it('renders locating state', () => {
      render(React.createElement(EmptyState, {
        locating: true,
        activeFilter: 'All' as never,
        searchMeta: baseMeta as never,
      }));
      expect(screen.getByText('Finding nearest hospitals...')).toBeTruthy();
    });
    it('renders "not found in other filters" message', () => {
      render(React.createElement(EmptyState, {
        locating: false,
        activeFilter: 'Police' as never,
        searchMeta: { radiusUsed: 5000, count: 3 } as never,
      }));
      expect(screen.getByText(/none matched the police filter/i)).toBeTruthy();
    });
    it('renders "expanding search radius" message', () => {
      render(React.createElement(EmptyState, {
        locating: false,
        activeFilter: 'All' as never,
        searchMeta: { radiusUsed: 10000, count: 0 } as never,
      }));
      expect(screen.getByText(/Search widened to 10.0 km/i)).toBeTruthy();
    });
    it('renders default suggestion when radius is default and no other filters have services', () => {
      render(React.createElement(EmptyState, {
        locating: false,
        activeFilter: 'All' as never,
        searchMeta: { radiusUsed: 5000, count: 0 } as never,
      }));
      expect(screen.getByText(/switching the filter/i)).toBeTruthy();
    });
  });

  describe('RouteStatusCard', () => {
    const baseRoute = {
      provider: 'OSRM',
      warnings: [],
      routes: [
        { routeId: 'r1', label: 'Fastest', durationSeconds: 600, distanceMeters: 5000, path: [], steps: [{ index: 1, instruction: 'Turn left', streetName: 'Main St', distanceMeters: 100, durationSeconds: 30 }] },
      ],
    };
    const baseOption = { routeId: 'r1', label: 'Fastest', durationSeconds: 600, distanceMeters: 5000, path: [], steps: [{ index: 1, instruction: 'Turn left', streetName: 'Main St', distanceMeters: 100, durationSeconds: 30 }] };
    const onSelect = jest.fn();

    it('returns null when no route/error/loading', () => {
      const { container } = render(React.createElement(RouteStatusCard, {
        activeRoute: null, activeRouteOption: null, routeError: null, loadingLabel: null,
        selectedServiceName: null, navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(container.innerHTML).toBe('');
    });
    it('renders route error state', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: null, activeRouteOption: null, routeError: 'No route found', loadingLabel: null,
        selectedServiceName: null, navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText('No route found')).toBeTruthy();
      expect(screen.getByText('Route Unavailable')).toBeTruthy();
    });
    it('renders loading state', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: null, activeRouteOption: null, routeError: null, loadingLabel: 'City Hospital',
        selectedServiceName: null, navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText('Building Route')).toBeTruthy();
    });
    it('renders ready route with steps', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: 'https://maps.google.com', selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText(/Route Ready/i)).toBeTruthy();
      expect(screen.getByText('City Hospital')).toBeTruthy();
    });
    it('renders rerouting state', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: true,
      }));
      expect(screen.getByText(/Rerouting/i)).toBeTruthy();
    });
    it('renders route warnings', () => {
      const routeWithWarning = { ...baseRoute, warnings: ['Traffic congestion ahead'] };
      render(React.createElement(RouteStatusCard, {
        activeRoute: routeWithWarning as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText('Traffic congestion ahead')).toBeTruthy();
    });
    it('renders route options when multiple routes', () => {
      const multiRoute = {
        provider: 'ORS',
        warnings: [],
        routes: [
          { routeId: 'r1', label: 'Fastest', durationSeconds: 600, distanceMeters: 5000, path: [], steps: [] },
          { routeId: 'r2', label: 'Shortest', durationSeconds: 900, distanceMeters: 3000, path: [], steps: [] },
        ],
      };
      render(React.createElement(RouteStatusCard, {
        activeRoute: multiRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: 'https://maps.google.com', selectedRouteId: 'r1',
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText(/Fastest/)).toBeTruthy();
      expect(screen.getByText(/Shortest/)).toBeTruthy();
    });
    it('calls onSelectRoute when route option clicked', () => {
      const multiRoute = {
        provider: 'ORS',
        warnings: [],
        routes: [
          { routeId: 'r1', label: 'Fastest', durationSeconds: 600, distanceMeters: 5000, path: [], steps: [] },
          { routeId: 'r2', label: 'Shortest', durationSeconds: 900, distanceMeters: 3000, path: [], steps: [] },
        ],
      };
      render(React.createElement(RouteStatusCard, {
        activeRoute: multiRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: 'https://maps.google.com', selectedRouteId: 'r1',
        onSelectRoute: onSelect, rerouting: false,
      }));
      const buttons = screen.getAllByText(/Shortest/);
      fireEvent.click(buttons[0]);
      expect(onSelect).toHaveBeenCalledWith('r2');
    });
    it('renders external navigation link when navigationHref provided', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: 'https://maps.google.com', selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText('Open External Navigation')).toBeTruthy();
    });
    it('does not show navigation link when navigationHref is null', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.queryByText('Open External Navigation')).toBeNull();
    });
    it('returns null when activeRoute is set but activeRouteOption is null', () => {
      const { container } = render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: null, routeError: null, loadingLabel: null,
        selectedServiceName: 'City Hospital', navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(container.innerHTML).toBe('');
    });
    it('shows "Destination selected" when selectedServiceName is null', () => {
      render(React.createElement(RouteStatusCard, {
        activeRoute: baseRoute as never, activeRouteOption: baseOption as never, routeError: null, loadingLabel: null,
        selectedServiceName: null, navigationHref: null, selectedRouteId: null,
        onSelectRoute: onSelect, rerouting: false,
      }));
      expect(screen.getByText('Destination selected')).toBeTruthy();
    });
  });
});

describe('LocatorFilters', () => {
  const setFilter = jest.fn();
  beforeEach(() => { setFilter.mockClear(); });

  it('renders all filter chips', () => {
    render(React.createElement(LocatorFilters, { activeFilter: 'All' as never, setActiveFilter: setFilter }));
    expect(screen.getByRole('radiogroup')).toBeTruthy();
    mockFilterChips.forEach((chip: string) => {
      expect(screen.getByLabelText('Filter by ' + chip)).toBeTruthy();
    });
  });
  it('highlights active filter', () => {
    render(React.createElement(LocatorFilters, { activeFilter: 'Police' as never, setActiveFilter: setFilter }));
    const radio = screen.getByLabelText('Filter by Police');
    expect(radio.getAttribute('aria-checked')).toBe('true');
  });
  it('calls setActiveFilter on click', () => {
    render(React.createElement(LocatorFilters, { activeFilter: 'All' as never, setActiveFilter: setFilter }));
    fireEvent.click(screen.getByLabelText('Filter by Hospital'));
    expect(setFilter).toHaveBeenCalledWith('Hospital');
  });
  it('applies custom className', () => {
    const { container } = render(React.createElement(LocatorFilters, {
      activeFilter: 'All' as never, setActiveFilter: setFilter, className: 'custom-class',
    }));
    expect(container.querySelector('.custom-class')).toBeTruthy();
  });
});

describe('LocatorMap', () => {
  const mockFiltered = [{
    id: '1', name: 'City Hospital', coords: [13.0, 80.2] as [number, number],
    type: 'Hospital' as never, accentColor: '#0070f3', distance: '1.2 km',
  }];
  const mockRouteOption = {
    routeId: 'r1', label: 'Fastest', durationSeconds: 600, distanceMeters: 5000,
    path: [[13.0, 80.2], [13.1, 80.3]] as [number, number][], steps: [],
  };

  it('renders EmergencyMap with facilities', () => {
    render(React.createElement(LocatorMap, {
      coords: [13.0, 80.2] as [number, number],
      filtered: mockFiltered as never[],
      activeRouteOption: null,
      alternativeRoutes: [],
      currentLocation: null,
      address: '',
      selectedServiceId: null,
    }));
    expect(screen.getByTestId('emergency-map')).toBeTruthy();
  });
  it('renders with currentLocation and route', () => {
    render(React.createElement(LocatorMap, {
      coords: [13.0, 80.2] as [number, number],
      filtered: mockFiltered as never[],
      activeRouteOption: mockRouteOption as never,
      alternativeRoutes: [],
      currentLocation: { lat: 13.0, lon: 80.2, accuracy: 10, displayName: 'Test Location' },
      address: 'Test Address',
      selectedServiceId: '1',
    }));
    expect(screen.getByTestId('emergency-map')).toBeTruthy();
  });
});

describe('MobileResultsList / DesktopResultsList', () => {
  const mockServices = [
    { id: '1', name: 'City Hospital', type: 'Hospital', distance: '1.2 km', address: '123 Main St', accentColor: '#0070f3', phone: '+91-9876543210', coords: [13.0, 80.2], filterType: 'Hospital' },
    { id: '2', name: 'Fire Station 1', type: 'Fire', distance: '2.5 km', address: '456 Oak Ave', accentColor: '#ff4500', phone: null, coords: [13.1, 80.3], filterType: 'Fire' },
  ];
  const onLocate = jest.fn();
  const onPreview = jest.fn();

  beforeEach(() => {
    onLocate.mockClear();
    onPreview.mockClear();
  });

  describe('MobileResultsList', () => {
    it('renders filtered services', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      expect(screen.getByText('City Hospital')).toBeTruthy();
      expect(screen.getByText('Fire Station 1')).toBeTruthy();
    });
    it('highlights selected service', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: '1',
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const cards = document.querySelectorAll('.locator-result-card');
      expect(cards.length).toBe(2);
    });
    it('shows loading spinner when routing for a service', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: '1',
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      expect(screen.getAllByText('Routing').length).toBe(1);
    });
    it('calls onLocateService on Locate button click', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const locateButtons = screen.getAllByText('Locate');
      fireEvent.click(locateButtons[0]);
      expect(onLocate).toHaveBeenCalledWith(mockServices[0]);
    });
    it('calls onPreviewService on Focus button click', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const focusButtons = screen.getAllByText('Focus');
      fireEvent.click(focusButtons[1]);
      expect(onPreview).toHaveBeenCalledWith(mockServices[1]);
    });
    it('disables Locate button when routing for that service', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: '1',
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const locateButtons = screen.getAllByText('Routing');
      expect(locateButtons[0].closest('button')?.getAttribute('disabled')).toBe('');
    });
    it('renders phone link for services', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const links = document.querySelectorAll('a[href^="tel:"]');
      expect(links.length).toBe(2);
      expect(links[0].getAttribute('href')).toBe('tel:+91-9876543210');
    });
    it('uses fallback number when phone is null', () => {
      render(React.createElement(MobileResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const links = document.querySelectorAll('a[href^="tel:"]');
      expect(links[1].getAttribute('href')).toBe('tel:+91-108');
    });
  });

  describe('DesktopResultsList', () => {
    it('renders filtered services', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      expect(screen.getByText('City Hospital')).toBeTruthy();
    });
    it('highlights selected service', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: '1',
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const cards = document.querySelectorAll('.locator-result-card');
      expect(cards.length).toBe(2);
    });
    it('shows loading when routing', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: '2',
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      expect(screen.getAllByText('Routing').length).toBe(1);
    });
    it('calls onLocateService', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      fireEvent.click(screen.getAllByText('Locate')[0]);
      expect(onLocate).toHaveBeenCalledWith(mockServices[0]);
    });
    it('calls onPreviewService', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      fireEvent.click(screen.getAllByText('Focus')[0]);
      expect(onPreview).toHaveBeenCalledWith(mockServices[0]);
    });
    it('disables Locate button when routing', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: '1',
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const routingButtons = screen.getAllByText('Routing');
      expect(routingButtons[0].closest('button')?.getAttribute('disabled')).toBe('');
    });
    it('uses fallback number when phone is null', () => {
      render(React.createElement(DesktopResultsList, {
        filtered: mockServices as never,
        selectedServiceId: null,
        routeLoadingId: null,
        onLocateService: onLocate,
        onPreviewService: onPreview,
      }));
      const links = document.querySelectorAll('a[href^="tel:"]');
      expect(links[1].getAttribute('href')).toBe('tel:+91-108');
    });
  });
});

describe('EmergencyCardClient utilities', () => {
  describe('decodeBase64Url', () => {
    it('decodes standard base64url to string', () => {
      const encoded = btoa('{"name":"John"}').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      const result = decodeBase64Url(encoded);
      expect(result).toBe('{"name":"John"}');
    });
    it('handles padding correctly', () => {
      const result = decodeBase64Url(btoa('ab').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''));
      expect(result).toBe('ab');
    });
  });

  describe('dialablePhone', () => {
    it('strips non-digit characters except +', () => {
      expect(dialablePhone('+91 (987) 654-3210')).toBe('+919876543210');
    });
    it('returns empty string for empty input', () => {
      expect(dialablePhone('')).toBe('');
    });
    it('preserves digits and plus sign', () => {
      expect(dialablePhone('+91100')).toBe('+91100');
    });
  });

  describe('parseHashPayload', () => {
    beforeEach(() => {
      window.location.hash = '';
    });

    it('returns null when no hash data', () => {
      expect(parseHashPayload()).toBeNull();
    });
    it('returns null when data param missing', () => {
      window.location.hash = '#other=value';
      expect(parseHashPayload()).toBeNull();
    });
    it('parses valid encoded payload', () => {
      const payload = { name: 'John', blood: 'O+' };
      const encoded = btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      window.location.hash = '#data=' + encoded;
      const result = parseHashPayload();
      expect(result?.name).toBe('John');
      expect(result?.blood).toBe('O+');
    });
    it('handles non-string fields gracefully', () => {
      const payload = { name: null, blood: 123 };
      const encoded = btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      window.location.hash = '#data=' + encoded;
      const result = parseHashPayload();
      expect(result?.name).toBe('');
      expect(result?.blood).toBe('');
    });
    it('returns null on invalid JSON', () => {
      const encoded = btoa('not-json').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      window.location.hash = '#data=' + encoded;
      expect(parseHashPayload()).toBeNull();
    });
  });
});

describe('EmergencyCardClient component', () => {
  const initialData = { name: 'John Doe', blood: 'O+', contact: '+91-9876543210', vehicle: 'TN01AB1234' };

  it('renders user data', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: initialData as never }));
    expect(screen.getByText('John Doe')).toBeTruthy();
    expect(screen.getByText('O+')).toBeTruthy();
    expect(screen.getByText('TN01AB1234')).toBeTruthy();
    expect(screen.getByText('First Responder Card Active')).toBeTruthy();
  });
  it('renders limited card when no data', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: {} as never }));
    expect(screen.getByText('Limited Emergency Card')).toBeTruthy();
  });
  it('renders print button', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: initialData as never }));
    expect(screen.getByTestId('print-button')).toBeTruthy();
  });
  it('renders emergency contact link', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: initialData as never }));
    const link = document.querySelector('a[href^="tel:"]');
    expect(link?.getAttribute('href')).toBe('tel:+919876543210');
  });
  it('renders India emergency lines', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: initialData as never }));
    expect(screen.getByText('100')).toBeTruthy();
    expect(screen.getByText('102')).toBeTruthy();
    expect(screen.getByText('101')).toBeTruthy();
    expect(screen.getByText('112')).toBeTruthy();
  });
  it('renders allergies section when data has allergies', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: { ...initialData, allergies: 'Peanuts' } as never }));
    expect(screen.getByText('Peanuts')).toBeTruthy();
    expect(screen.getByText('Known Allergies')).toBeTruthy();
  });
  it('does not render allergies section when not provided', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: initialData as never }));
    expect(screen.queryByText('Known Allergies')).toBeNull();
  });
  it('renders insurance section when data has insurance', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: { ...initialData, insurance: 'Star Health' } as never }));
    expect(screen.getByText('Star Health')).toBeTruthy();
    expect(screen.getByText('Insurance Provider')).toBeTruthy();
  });
  it('renders medical notes section when data has medical', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: { ...initialData, medical: 'Diabetic' } as never }));
    expect(screen.getByText('Diabetic')).toBeTruthy();
    expect(screen.getByText('Medical Notes')).toBeTruthy();
  });
  it('does NOT render contact link when contact is missing', () => {
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: { name: 'John' } as never }));
    expect(screen.queryByText('Call Emergency Contact')).toBeNull();
  });
  it('merges hash payload with initial data on mount', async function() {
    const payload = JSON.stringify({ name: 'Hash Name', contact: '+919999999999' });
    const encoded = btoa(payload).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    window.location.hash = '#data=' + encoded;
    render(React.createElement(EmergencyCardClient, { userId: 'user-1', initialData: { blood: 'O+' } as never }));
    await waitFor(function() { expect(screen.getByText('Hash Name')).toBeTruthy() });
    // contact from hash becomes dialable phone link
    expect(document.querySelector('a[href^="tel:"]')?.getAttribute('href')).toBe('tel:+919999999999');
  });
});
