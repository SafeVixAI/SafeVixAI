jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { const React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { return null } } })
jest.mock('@/lib/store', function() {
  const state = { isAuthenticated: false }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: 'http://localhost:8000' } })
jest.mock('@/lib/validation-schemas', function() { return { RESET_RULES: {} } })
jest.mock('@/lib/use-form-validation', function() { return { useFormValidation: function() { return { errors: {}, handleChange: jest.fn(), handleBlur: jest.fn(), handleSubmit: function(values, cb) { return cb() } } } } })
jest.mock('@/components/ui/Logo', function() { return { Logo: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const ForgotPasswordPage = require('../app/forgot-password/page').default

describe('Forgot Password Page', function() {
  it('renders Password Recovery heading', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('Password Recovery')).toBeTruthy()
  })

  it('renders SafeVixAI heading', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders email input', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByPlaceholderText(/operator@/)).toBeTruthy()
  })

  it('renders submit button', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('Send Reset Link')).toBeTruthy()
  })

  it('renders back to login link', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('Back to Login')).toBeTruthy()
  })

  it('renders description text', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText(/operator email/)).toBeTruthy()
  })

  it('renders email label', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('Operator Email')).toBeTruthy()
  })

  it('renders LoadingMunicipalities heading', function() {
    render(React.createElement(ForgotPasswordPage))
    expect(rtlScreen.getByText('Password Recovery')).toBeTruthy()
  })
})
