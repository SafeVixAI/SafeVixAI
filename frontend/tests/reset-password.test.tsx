jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), replace: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/link', function() { return function({ children, ...rest }) { const React = require('react'); return React.createElement('a', rest, children) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { return null } } })
jest.mock('@/lib/store', function() {
  const state = { isAuthenticated: false }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: 'http://localhost:8000' } })
jest.mock('@/components/ui/Logo', function() { return { Logo: function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen: rtlScreen, fireEvent, waitFor } = require('@testing-library/react')
const ResetPasswordPage = require('../app/reset-password/page').default

describe('ResetPassword Page', function() {
  it('renders SafeVixAI heading', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders Set New Password text', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByText('Set New Password')).toBeTruthy()
  })

  it('renders description text', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByText(/Choose a new access key/)).toBeTruthy()
  })

  it('renders password input', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByPlaceholderText('Min 8 characters')).toBeTruthy()
  })

  it('renders confirm password input', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByPlaceholderText('Re-enter access key')).toBeTruthy()
  })

  it('renders Confirm Access Key label', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByText('Confirm Access Key')).toBeTruthy()
  })

  it('renders submit button', function() {
    render(React.createElement(ResetPasswordPage))
    expect(rtlScreen.getByText('Update Password')).toBeTruthy()
  })

  it('shows error when password is too short', function() {
    render(React.createElement(ResetPasswordPage))
    const input = rtlScreen.getByPlaceholderText('Min 8 characters')
    fireEvent.change(input, { target: { value: '123' } })
    fireEvent.click(rtlScreen.getByText('Update Password'))
    expect(rtlScreen.getByText(/at least 8 characters/)).toBeTruthy()
  })

  it('shows mismatch error when passwords differ', function() {
    render(React.createElement(ResetPasswordPage))
    const pwd = rtlScreen.getByPlaceholderText('Min 8 characters')
    const confirm = rtlScreen.getByPlaceholderText('Re-enter access key')
    fireEvent.change(pwd, { target: { value: 'password123' } })
    fireEvent.change(confirm, { target: { value: 'different' } })
    fireEvent.click(rtlScreen.getByText('Update Password'))
    expect(rtlScreen.getByText(/do not match/)).toBeTruthy()
  })
})
