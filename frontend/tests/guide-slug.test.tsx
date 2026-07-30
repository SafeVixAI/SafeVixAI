jest.mock('next/navigation', function() { return { useParams: function() { return { slug: 'chennai' } }, useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, Link: function({ children, ...rest }) { const React = require('react'); return React.createElement('a', rest, children) } } })
jest.mock('@/lib/api', function() { return { fetchMunicipalityBySlug: jest.fn() } })
jest.mock('@/components/guide/ContactChannels', function() { return { ContactChannels: function() { return null } } })
jest.mock('@/components/guide/LeadershipCard', function() { return { LeadershipCard: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen, act } = require('@testing-library/react')
const Page = require('../app/guide/[slug]/page').default
const api = require('@/lib/api')

const mockData = { slug: 'chennai', name: 'Chennai Corporation', shortName: 'Chennai', stateCode: 'TN', city: 'Chennai', municipalityType: 'municipal_corporation', wardCount: 200, population: 11000000, helplinePhone: '1913', centroidLat: 13.08, centroidLon: 80.27, areaSqkm: 426, description: 'Capital of Tamil Nadu', servicesOffered: ['Water', 'Roads'] }

describe('MunicipalityDetailPage', function() {
  it('shows loading state initially', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Loading municipality...')).toBeTruthy()
  })

  it('renders municipality name after load', async function() {
    api.fetchMunicipalityBySlug.mockResolvedValue(mockData)
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getAllByText('Chennai Corporation').length).toBe(2)
  })

  it('renders stat cards', async function() {
    api.fetchMunicipalityBySlug.mockResolvedValue(mockData)
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText('Population')).toBeTruthy()
    expect(rtlScreen.getByText('200')).toBeTruthy()
  })

  it('renders city and state in hero', async function() {
    api.fetchMunicipalityBySlug.mockResolvedValue(mockData)
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText(/Chennai, TN/)).toBeTruthy()
  })

  it('renders about description', async function() {
    api.fetchMunicipalityBySlug.mockResolvedValue(mockData)
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText('Capital of Tamil Nadu')).toBeTruthy()
  })

  it('renders service tags', async function() {
    api.fetchMunicipalityBySlug.mockResolvedValue(mockData)
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText('Water')).toBeTruthy()
    expect(rtlScreen.getByText('Roads')).toBeTruthy()
  })

  it('shows error state when API fails', async function() {
    api.fetchMunicipalityBySlug.mockRejectedValue(new Error('Network error'))
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText('Failed to load municipality details')).toBeTruthy()
  })

  it('shows fallback error and back link when municipality not found', async function() {
    api.fetchMunicipalityBySlug.mockRejectedValue(new Error('Not found'))
    render(React.createElement(Page))
    await act(function() { return new Promise(function(r) { return setTimeout(r, 100) }) })
    expect(rtlScreen.getByText(/Back to Guide/)).toBeTruthy()
  })
})
