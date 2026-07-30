jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { const React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const OfflinePage = require('../app/offline/page').default

describe('Offline Page', function() {
  it('renders Offline Mode label', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Offline Mode')).toBeTruthy()
  })

  it('renders offline title', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('SafeVixAI is running from cached emergency tools.')).toBeTruthy()
  })

  it('renders emergency numbers section title', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Emergency Numbers')).toBeTruthy()
  })

  it('renders emergency number 112', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('112')).toBeTruthy()
  })

  it('renders SOS link', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Open Emergency SOS')).toBeTruthy()
  })

  it('renders First Aid link', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Open First Aid Guides')).toBeTruthy()
  })

  it('renders Locator link', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Open Cached Locator')).toBeTruthy()
  })

  it('renders offline description text', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Network services are unavailable right now. SOS, first aid, emergency numbers, and queued reports remain available.')).toBeTruthy()
  })

  it('renders Police emergency number', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('Police')).toBeTruthy()
    expect(rtlScreen.getByText('100')).toBeTruthy()
  })

  it('renders Fire emergency number', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('101')).toBeTruthy()
  })

  it('renders Ambulance emergency number', function() {
    render(React.createElement(OfflinePage))
    expect(rtlScreen.getByText('102')).toBeTruthy()
  })

  it('renders SOS link with correct href', function() {
    render(React.createElement(OfflinePage))
    const sosLink = rtlScreen.getByText('Open Emergency SOS').closest('a')
    expect(sosLink.getAttribute('href')).toBe('/sos')
  })

  it('renders First Aid link with correct href', function() {
    render(React.createElement(OfflinePage))
    const firstAidLink = rtlScreen.getByText('Open First Aid Guides').closest('a')
    expect(firstAidLink.getAttribute('href')).toBe('/first-aid')
  })
})
