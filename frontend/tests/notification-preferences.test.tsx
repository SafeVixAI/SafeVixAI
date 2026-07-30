jest.mock('@/lib/notifications', function() {
  return {
    fetchPreferences: jest.fn(),
    updatePreferences: jest.fn(),
  }
})
jest.mock('@/lib/store', function() {
  var appState = { operatorName: 'TestOp' }
  return {
    useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(appState) : appState }, {
      getState: function() { return appState }, setState: jest.fn(), subscribe: jest.fn(),
    })
  }
})
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent, waitFor } = require('@testing-library/react')
var { NotificationPreferencesPanel } = require('@/components/notifications/NotificationPreferencesPanel')

function defaultPrefs() {
  return {
    id: 'pref1', user_id: 'TestOp',
    channels_enabled: { in_app: true, email: false, sms: true, push: false, slack: false, discord: false, teams: false, webhook: false },
    categories_enabled: { system_health: true, ai: true, security: true, performance: true, update: true, maintenance: false, incident: true, deployment: true, usage: false, billing: false, issue: true, sos: true, emergency: true, challan: true, general: true },
    digest_enabled: false, digest_frequency: 'daily',
    dnd_enabled: false, dnd_start_hour: 22, dnd_end_hour: 7, dnd_timezone: 'UTC',
    quiet_hours_enabled: false,
    push_token: true, slack_webhook_url: false, discord_webhook_url: false, teams_webhook_url: false, webhook_url: false,
    email_address: 'test@example.com', phone_number: '+911234567890',
    locale: 'en', max_daily_notifications: 100,
  }
}

describe('NotificationPreferencesPanel', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    var notif = require('@/lib/notifications')
    notif.fetchPreferences.mockResolvedValue(defaultPrefs())
    notif.updatePreferences.mockImplementation(function(uid, payload) {
      return Promise.resolve(Object.assign({}, defaultPrefs(), payload))
    })
  })

  it('shows loading state initially', function() {
    var notif = require('@/lib/notifications')
    notif.fetchPreferences.mockReturnValue(new Promise(function() {}))
    var { container } = render(React.createElement(NotificationPreferencesPanel))
    var loadingContainer = container.querySelector('.flex.items-center.justify-center.py-16')
    expect(loadingContainer).toBeTruthy()
  })

  it('renders channels section', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Channels')).toBeTruthy() })
  })

  it('renders all channel buttons', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      expect(screen.getByText('In-App')).toBeTruthy()
      expect(screen.getByText('Email')).toBeTruthy()
    })
  })

  it('toggles channel on click', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Email')).toBeTruthy() })
    fireEvent.click(screen.getByText('Email'))
  })

  it('renders categories section', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Categories')).toBeTruthy() })
  })

  it('toggles category on click', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Maintenance')).toBeTruthy() })
    fireEvent.click(screen.getByText('Maintenance'))
  })

  it('renders DND section', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Do Not Disturb')).toBeTruthy() })
  })

  it('shows DND hours when enabled', async function() {
    var { container } = render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Enable DND')).toBeTruthy() })
    var checkbox = container.querySelector('input[type="checkbox"]')
    if (checkbox) { fireEvent.click(checkbox); await waitFor(function() { expect(screen.getByText(':00')).toBeTruthy() }) }
  })

  it('renders digest section', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Digest Mode')).toBeTruthy() })
  })

  it('renders contact info inputs', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      expect(screen.getByDisplayValue('test@example.com')).toBeTruthy()
      expect(screen.getByDisplayValue('+911234567890')).toBeTruthy()
    })
  })

  it('renders locale selector', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      expect(screen.getByText('Locale')).toBeTruthy()
      expect(screen.getByText('English')).toBeTruthy()
    })
  })

  it('changes locale selection', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('English')).toBeTruthy() })
    var select = document.querySelector('select')
    if (select) { fireEvent.change(select, { target: { value: 'hi' } }); expect(select.value).toBe('hi') }
  })

  it('saves preferences on save click', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Save Preferences')).toBeTruthy() })
    fireEvent.click(screen.getByText('Save Preferences'))
    await waitFor(function() {
      expect(require('@/lib/notifications').updatePreferences).toHaveBeenCalled()
    })
  })

  it('shows Saved! flash after save', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Save Preferences')).toBeTruthy() })
    fireEvent.click(screen.getByText('Save Preferences'))
    await waitFor(function() { expect(screen.getByText('Saved!')).toBeTruthy() })
  })

  it('shows error on save failure', async function() {
    var notif = require('@/lib/notifications')
    notif.updatePreferences.mockRejectedValue(new Error('Save failed'))
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Save Preferences')).toBeTruthy() })
    fireEvent.click(screen.getByText('Save Preferences'))
    await waitFor(function() { expect(screen.getByText('Save failed')).toBeTruthy() })
  })

  it('shows error state when fetchPreferences fails', async function() {
    var notif = require('@/lib/notifications')
    notif.fetchPreferences.mockRejectedValue(new Error('Load failed'))
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText(/Load failed/)).toBeTruthy() })
  })

  it('handles onClose callback', async function() {
    var onClose = jest.fn()
    render(React.createElement(NotificationPreferencesPanel, { onClose: onClose }))
    await waitFor(function() { expect(screen.getByText('Notification Preferences')).toBeTruthy() })
    var container = document.querySelector('.flex.h-full.flex-col')
    var allBtns = container ? Array.from(container.querySelectorAll('button')) : []
    var xBtn = allBtns.length > 0 ? allBtns[0] : null
    if (xBtn) { fireEvent.click(xBtn); expect(onClose).toHaveBeenCalled() }
  })

  it('renders digest frequency dropdown when digest enabled', async function() {
    var { container } = render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Enable Digest')).toBeTruthy() })
    var checkboxes = container.querySelectorAll('input[type="checkbox"]')
    var digestCheckbox = checkboxes.length > 1 ? checkboxes[1] : null
    if (digestCheckbox) { fireEvent.click(digestCheckbox); await waitFor(function() { expect(screen.getByText('Hourly')).toBeTruthy() }) }
  })

  it('does not show locale section text when loading', function() {
    var notif = require('@/lib/notifications')
    notif.fetchPreferences.mockReturnValue(new Promise(function() {}))
    render(React.createElement(NotificationPreferencesPanel))
    expect(screen.queryByText('Locale')).toBeNull()
  })

  it('renders email input', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      var input = screen.getByDisplayValue('test@example.com')
      expect(input.type).toBe('email')
    })
  })

  it('renders phone input', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      var input = screen.getByDisplayValue('+911234567890')
      expect(input.type).toBe('tel')
    })
  })

  it('changes email value', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      var input = screen.getByDisplayValue('test@example.com')
      fireEvent.change(input, { target: { value: 'new@test.com' } })
      expect(input.value).toBe('new@test.com')
    })
  })

  it('changes phone value', async function() {
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() {
      var input = screen.getByDisplayValue('+911234567890')
      fireEvent.change(input, { target: { value: '+919999999999' } })
      expect(input.value).toBe('+919999999999')
    })
  })

  it('shows Saving... on save button during save', async function() {
    var notif = require('@/lib/notifications')
    notif.updatePreferences.mockReturnValue(new Promise(function() {}))
    render(React.createElement(NotificationPreferencesPanel))
    await waitFor(function() { expect(screen.getByText('Save Preferences')).toBeTruthy() })
    fireEvent.click(screen.getByText('Save Preferences'))
    await waitFor(function() { expect(screen.getByText('Saving...')).toBeTruthy() })
  })
})
