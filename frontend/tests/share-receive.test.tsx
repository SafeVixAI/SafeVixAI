jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: 'http://test' } })

var React = require('react')
var { render, screen, waitFor } = require('@testing-library/react')
var Page = require('../app/share-receive/page').default

describe('ShareReceivePage', function() {
  it('renders SafeVixAI branding', function() {
    render(React.createElement(Page))
    expect(screen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders Share Target Active text', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Share Target Active')).toBeTruthy()
  })

  it('renders sr-only Share Receive heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Share Receive')).toBeTruthy()
  })

  it('shows no-gps message after timeout with empty params', async function() {
    render(React.createElement(Page))
    await waitFor(function() { expect(screen.getByText('No GPS Coordinates Found')).toBeTruthy() }, { timeout: 2000 })
  })

  it('shows redirecting to locator message', async function() {
    render(React.createElement(Page))
    await waitFor(function() { expect(screen.getByText(/Redirecting to locator/)).toBeTruthy() }, { timeout: 2000 })
  })
})
