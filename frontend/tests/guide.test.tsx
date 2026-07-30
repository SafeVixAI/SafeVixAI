jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/guide/MunicipalityCard', function() { return { MunicipalityCard: function(p) { const React = require('react'); return React.createElement('div', { 'data-testid': 'municipality-card' }, p.municipality.name) } } })
const mockMunicipalities = [
  { slug: 'chennai', name: 'Chennai', shortName: 'CHN', city: 'Chennai', stateCode: 'TN', municipalityType: 'municipal_corporation', wardCount: 200, population: 11000000, helplinePhone: '044-2538', centroidLat: 13.08, centroidLon: 80.27 },
  { slug: 'mumbai', name: 'Mumbai', shortName: 'BOM', city: 'Mumbai', stateCode: 'MH', municipalityType: 'municipal_corporation', wardCount: 227, population: 19000000, helplinePhone: '022-2262', centroidLat: 19.07, centroidLon: 72.87 },
  { slug: 'bangalore', name: 'Bangalore', shortName: 'BLR', city: 'Bangalore', stateCode: 'KA', municipalityType: 'municipal_corporation', wardCount: 198, population: 13000000, helplinePhone: '080-2297', centroidLat: 12.97, centroidLon: 77.59 },
  { slug: 'kanchipuram', name: 'Kanchipuram', shortName: 'KAN', city: 'Kanchipuram', stateCode: 'TN', municipalityType: 'municipality', wardCount: 51, population: 230000, helplinePhone: null, centroidLat: 12.83, centroidLon: 79.70 },
]

const mockFetchMunicipalities = jest.fn().mockResolvedValue({ municipalities: mockMunicipalities })
const mockFetchNearby = jest.fn().mockResolvedValue([])
jest.mock('@/lib/api', function() {
  return { fetchMunicipalities: mockFetchMunicipalities, fetchNearbyMunicipalities: mockFetchNearby }
})
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen, fireEvent, waitFor } = require('@testing-library/react')
const Page = require('../app/guide/page').default

describe('GuidePage', function() {
  it('renders Municipality Guide sr-only heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Municipality Guide')).toBeTruthy()
  })

  it('renders search input', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByPlaceholderText('Search municipality...')).toBeTruthy()
  })

  it('renders Find Nearby button', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Find Nearby')).toBeTruthy()
  })

  it('renders Filter button', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Filter')).toBeTruthy()
  })

  it('renders municipality cards after loading', async function() {
    render(React.createElement(Page))
    const cards = await rtlScreen.findAllByTestId('municipality-card', {}, { timeout: 5000 })
    expect(cards.length).toBeGreaterThanOrEqual(3)
  })

  it('filters municipalities by search query', async function() {
    render(React.createElement(Page))
    await rtlScreen.findByText('Chennai', {}, { timeout: 5000 })
    const input = rtlScreen.getByPlaceholderText('Search municipality...')
    fireEvent.change(input, { target: { value: 'Kanchi' } })
    expect(rtlScreen.getByText('Kanchipuram')).toBeTruthy()
    expect(rtlScreen.queryByText('Chennai')).toBeFalsy()
  })

  it('shows filters when Filter button clicked', async function() {
    render(React.createElement(Page))
    const cards = await rtlScreen.findAllByTestId('municipality-card', {}, { timeout: 5000 })
    expect(cards.length).toBeGreaterThanOrEqual(1)
    fireEvent.click(rtlScreen.getByText('Filter'))
    expect(rtlScreen.getByText('State')).toBeTruthy()
    expect(rtlScreen.getByText('Type')).toBeTruthy()
  })

  it('filters by state chip when active', async function() {
    render(React.createElement(Page))
    await rtlScreen.findByText('Mumbai', {}, { timeout: 5000 })
    fireEvent.click(rtlScreen.getByText('Filter'))
    fireEvent.click(rtlScreen.getByText('MH'))
    expect(rtlScreen.getByText('Mumbai')).toBeTruthy()
    expect(rtlScreen.queryByText('Chennai')).toBeFalsy()
  })

  it('shows all state chips in filter panel', async function() {
    render(React.createElement(Page))
    const cards = await rtlScreen.findAllByTestId('municipality-card', {}, { timeout: 5000 })
    expect(cards.length).toBeGreaterThanOrEqual(1)
    fireEvent.click(rtlScreen.getByText('Filter'))
    expect(rtlScreen.getByText('TN')).toBeTruthy()
    expect(rtlScreen.getByText('KA')).toBeTruthy()
  })
})

describe('GuidePage fetch', function() {
  it('calls fetchMunicipalities on mount', function() {
    render(React.createElement(Page))
    expect(mockFetchMunicipalities).toHaveBeenCalled()
  })
})
