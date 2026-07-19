jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { var React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/client-logger', function() { return { logClientError: jest.fn() } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render } = require('@testing-library/react')
var GlobalError = require('../app/error').default

describe('Error Page', function() {
  it('renders System Recovery text', function() {
    var err = new Error('Test error')
    err.digest = 'abc123'
    var { getByText } = render(React.createElement(GlobalError, { error: err, reset: function() {} }))
    expect(getByText('System Recovery')).toBeTruthy()
  })

  it('renders error digest for debugging', function() {
    var err = new Error('Test error')
    err.digest = 'abc123'
    var { getByText } = render(React.createElement(GlobalError, { error: err, reset: function() {} }))
    expect(getByText(/abc123/)).toBeTruthy()
  })

  it('renders retry button', function() {
    var err = new Error('Network error')
    err.digest = 'def456'
    var { getByText } = render(React.createElement(GlobalError, { error: err, reset: function() {} }))
    expect(getByText('Retry')).toBeTruthy()
  })

  it('renders home link', function() {
    var err = new Error('Timeout error')
    err.digest = 'xyz789'
    var { getByText } = render(React.createElement(GlobalError, { error: err, reset: function() {} }))
    expect(getByText('Home')).toBeTruthy()
  })

  it('renders emergency call prompt', function() {
    var err = new Error('Auth failure')
    err.digest = 'auth001'
    var { getByText } = render(React.createElement(GlobalError, { error: err, reset: function() {} }))
    expect(getByText(/CALL 112/)).toBeTruthy()
  })
})
