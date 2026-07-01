jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { var React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var OfflinePage = require('../app/offline/page').default

describe('Offline Page', function() {
  it('renders Offline Mode label', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('Offline Mode')).toBeTruthy()
  })

  it('renders offline title', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('SafeVixAI is running from cached emergency tools.')).toBeTruthy()
  })

  it('renders emergency numbers section title', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('Emergency Numbers')).toBeTruthy()
  })

  it('renders emergency number 112', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('112')).toBeTruthy()
  })

  it('renders SOS link', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('Open Emergency SOS')).toBeTruthy()
  })

  it('renders First Aid link', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('Open First Aid Guides')).toBeTruthy()
  })

  it('renders Locator link', function() {
    render(React.createElement(OfflinePage))
    expect(screen.getByText('Open Cached Locator')).toBeTruthy()
  })
})
