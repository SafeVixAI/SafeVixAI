jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { var React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { return null } } })
jest.mock('@/lib/store', function() {
  var state = { isAuthenticated: false }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/use-form-validation', function() { return { useFormValidation: function() { return { errors: {}, handleChange: jest.fn(), handleBlur: jest.fn(), handleSubmit: function(values, fn) { fn(); return Promise.resolve(true) } } } } })
jest.mock('@/lib/validation-schemas', function() { return { SIGNUP_RULES: function() { return {} } } })
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: 'http://localhost:8000' } })
jest.mock('@/components/ui/Logo', function() { return { Logo: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent } = require('@testing-library/react')
var SignupPage = require('../app/signup/page').default

describe('Signup Page', function() {
  it('renders SafeVixAI heading', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders Create Operator Account text', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByText('Create Operator Account')).toBeTruthy()
  })

  it('renders Sentinel Online badge', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByText('Sentinel Online')).toBeTruthy()
  })

  it('renders name input with placeholder', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByPlaceholderText('Your full name')).toBeTruthy()
  })

  it('renders email input with placeholder', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByPlaceholderText('operator@safevixai.app')).toBeTruthy()
  })

  it('renders password input with placeholder', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByPlaceholderText('Min 8 characters')).toBeTruthy()
  })

  it('renders submit button', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByText('Create Account')).toBeTruthy()
  })

  it('renders sign in link for existing users', function() {
    render(React.createElement(SignupPage))
    expect(screen.getByText(/Sign in/i)).toBeTruthy()
  })
})
