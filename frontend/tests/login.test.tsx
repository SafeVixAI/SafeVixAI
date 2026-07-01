jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { var React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { return null } } })
jest.mock('@/lib/store', function() {
  var state = { isAuthenticated: false }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/use-form-validation', function() { return { useFormValidation: function() { return { errors: {}, handleChange: jest.fn(), handleBlur: jest.fn(), handleSubmit: function(values, fn) { fn(); return Promise.resolve(true) } } } } })
jest.mock('@/lib/validation-schemas', function() { return { LOGIN_RULES: function() { return {} } } })
jest.mock('@/components/ui/Logo', function() { return { Logo: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent } = require('@testing-library/react')
var LoginPage = require('../app/login/page').default

describe('Login Page', function() {
  it('renders SafeVixAI heading', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders operator_authentication heading', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('operator_authentication')).toBeTruthy()
  })

  it('renders email input', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByPlaceholderText(/operator@/)).toBeTruthy()
  })

  it('renders password input with placeholder', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByPlaceholderText('••••••••••••')).toBeTruthy()
  })

  it('renders submit button', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('Enter Command Center')).toBeTruthy()
  })

  it('renders Create one link', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('Create one')).toBeTruthy()
  })

  it('renders forgot password link', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('Forgot password?')).toBeTruthy()
  })

  it('renders Sentinel Online badge', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('Sentinel Online')).toBeTruthy()
  })

  it('renders Secure badge', function() {
    render(React.createElement(LoginPage))
    expect(screen.getByText('Secure')).toBeTruthy()
  })
})
