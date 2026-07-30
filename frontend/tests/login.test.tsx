jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { const React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { return null } } })
jest.mock('@/lib/store', function() {
  const state = { isAuthenticated: false }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/use-form-validation', function() { return { useFormValidation: function() { return { errors: {}, handleChange: jest.fn(), handleBlur: jest.fn(), handleSubmit: function(values, fn) { fn(); return Promise.resolve(true) } } } } })
jest.mock('@/lib/validation-schemas', function() { return { LOGIN_RULES: function() { return {} } } })
jest.mock('@/components/ui/Logo', function() { return { Logo: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen, fireEvent } = require('@testing-library/react')
const LoginPage = require('../app/login/page').default

describe('Login Page', function() {
  it('renders SafeVixAI heading', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders operator_authentication heading', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('operator_authentication')).toBeTruthy()
  })

  it('renders email input', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByPlaceholderText(/operator@/)).toBeTruthy()
  })

  it('renders password input with placeholder', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByPlaceholderText('••••••••••••')).toBeTruthy()
  })

  it('renders submit button', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('Enter Command Center')).toBeTruthy()
  })

  it('renders Create one link', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('Create one')).toBeTruthy()
  })

  it('renders forgot password link', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('Forgot password?')).toBeTruthy()
  })

  it('renders Sentinel Online badge', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('Sentinel Online')).toBeTruthy()
  })

  it('renders Secure badge', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('Secure')).toBeTruthy()
  })

  it('renders JWT Secured badge', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('JWT Secured')).toBeTruthy()
  })

  it('renders version footer text', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText(/SafeVixAI v2\.4/)).toBeTruthy()
  })

  it('renders password visibility toggle button', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByLabelText('Show password')).toBeTruthy()
  })

  it('renders account prompt text', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText("Don't have an account?")).toBeTruthy()
  })

  it('renders operator_email label', function() {
    render(React.createElement(LoginPage))
    expect(rtlScreen.getByText('operator_email')).toBeTruthy()
  })

  it('toggles password visibility', function() {
    render(React.createElement(LoginPage))
    const toggle = rtlScreen.getByLabelText('Show password')
    fireEvent.click(toggle)
    expect(rtlScreen.getByLabelText('Hide password')).toBeTruthy()
  })
})
