jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: 'http://test' } })

const React = require('react')
const { render, screen: rtlScreen, waitFor } = require('@testing-library/react')
const Page = require('../app/share-receive/page').default

describe('ShareReceivePage', function() {
  it('renders SafeVixAI branding', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders Share Target Active text', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Share Target Active')).toBeTruthy()
  })

  it('renders sr-only Share Receive heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Share Receive')).toBeTruthy()
  })

  it('shows no-gps message after timeout with empty params', async function() {
    render(React.createElement(Page))
    await waitFor(function() { expect(rtlScreen.getByText('No GPS Coordinates Found')).toBeTruthy() }, { timeout: 2000 })
  })

  it('shows redirecting to locator message', async function() {
    render(React.createElement(Page))
    await waitFor(function() { expect(rtlScreen.getByText(/Redirecting to locator/)).toBeTruthy() }, { timeout: 2000 })
  })
})
