jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/guide/MunicipalityCard', function() { return function() { return null } })
jest.mock('@/lib/api', function() { return { fetchMunicipalities: jest.fn().mockResolvedValue({ municipalities: [] }), fetchNearbyMunicipalities: jest.fn().mockResolvedValue([]) } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var Page = require('../app/guide/page').default

describe('GuidePage', function() {
  it('renders Municipality Guide sr-only heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Municipality Guide')).toBeTruthy()
  })

  it('renders search input', function() {
    render(React.createElement(Page))
    expect(screen.getByPlaceholderText('Search municipality...')).toBeTruthy()
  })

  it('renders Find Nearby button', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Find Nearby')).toBeTruthy()
  })

  it('renders Filter button', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Filter')).toBeTruthy()
  })
})
