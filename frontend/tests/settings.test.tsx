jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } } } })
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/components/ui/SettingRow', function() { return { SettingRow: function({ title, description }) { var React = require('react'); return React.createElement('div', { 'data-testid': 'setting-row' }, title, description) } } })
jest.mock('@/components/dashboard/Toggle', function() { return function() { return null } })
jest.mock('@/components/dashboard/ProfileCard', function() { return function() { return null } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/dashboard/Toast', function() { return function() { return null } })
jest.mock('@/components/ui/LanguageSelector', function() { return function() { return null } })
jest.mock('@/lib/store', function() {
  var state = { crashDetectionEnabled: false, isAuthenticated: true, operatorName: 'TestOp', userProfile: {}, speedAlert: false, hazardNotifs: true, locationTracking: false, sosVibration: true, autoOffline: false, analyticsOptIn: false, navApp: 'google', soundsEnabled: true, setCrashDetectionEnabled: jest.fn(), setSpeedAlert: jest.fn(), setHazardNotifs: jest.fn(), setLocationTracking: jest.fn(), setSosVibration: jest.fn(), setAutoOffline: jest.fn(), setAnalyticsOptIn: jest.fn(), setNavApp: jest.fn(), setSoundsEnabled: jest.fn(), updateInfo: { hasUpdate: false, version: null, channel: 'stable', releaseDate: null, releaseNotes: null, downloadSize: null, isMandatory: false, isSecurity: false, downloadProgress: null, status: 'idle' }, setUpdateInfo: jest.fn(), setUpdateStatus: jest.fn(), dismissUpdateBanner: jest.fn(), resetUpdateBanner: jest.fn(), setDownloadProgress: jest.fn() }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }), useUpdateInfo: function() { return state.updateInfo } }
})
jest.mock('@/components/ThemeProvider', function() { return { useTheme: function() { return { theme: 'dark', setTheme: jest.fn() } } } })
jest.mock('@/lib/navigation-launch', function() { return { setPreferredNavApp: jest.fn() } })
jest.mock('@/lib/analytics-provider', function() { return { ANALYTICS_CONSENT_KEY: 'analytics-consent' } })
jest.mock('posthog-js', function() { return { opt_in_capturing: jest.fn(), opt_out_capturing: jest.fn() } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var SettingsPage = require('../app/settings/page').default

describe('Settings Page', function() {
  it('renders sr-only Settings heading', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('Settings')).toBeTruthy()
  })

  it('renders setting rows', function() {
    render(React.createElement(SettingsPage))
    var rows = rtlScreen.getAllByTestId('setting-row')
    expect(rows.length).toBeGreaterThan(0)
  })

  it('renders theme buttons', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('settings.light')).toBeTruthy()
    expect(rtlScreen.getByText('settings.dark')).toBeTruthy()
    expect(rtlScreen.getByText('settings.system')).toBeTruthy()
  })

  it('renders signed in status when authenticated', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('settings.signed_in')).toBeTruthy()
  })

  it('renders operator name', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('TestOp')).toBeTruthy()
  })

  it('renders JWT badge when authenticated', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('JWT')).toBeTruthy()
  })

  it('renders active user badge', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('settings.active_user')).toBeTruthy()
  })

  it('renders sign out button when authenticated', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText(/profile.sign_out/)).toBeTruthy()
  })

  it('renders purge cache button', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('settings.purge')).toBeTruthy()
  })

  it('renders export profile button', function() {
    render(React.createElement(SettingsPage))
    expect(rtlScreen.getByText('settings.export')).toBeTruthy()
  })
})
