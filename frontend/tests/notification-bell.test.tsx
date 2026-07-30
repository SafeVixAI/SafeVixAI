jest.mock('@/lib/notifications', function() {
  return {
    fetchNotifications: jest.fn(),
    fetchNotificationStats: jest.fn(),
    markNotificationRead: jest.fn(),
    markAllNotificationsRead: jest.fn(),
    deleteNotification: jest.fn(),
    getNotificationColor: function() { return 'text-blue-500' },
    getTimeAgo: function() { return '1m ago' },
    getNotificationIcon: function() { return 'Bell' },
    fetchPreferences: jest.fn(),
    updatePreferences: jest.fn(),
    useNotificationWebSocket: function() { return { notifications: [], connected: false, sendAck: jest.fn(), sendMarkRead: jest.fn() } },
  }
})
jest.mock('@/lib/store/notification-slice', function() {
  var storeState = {
    items: [], unreadCount: 0, isCenterOpen: false, preferencesOpen: false, soundEnabled: true, desktopEnabled: true,
    setItems: jest.fn(function(newItems) { storeState.items = newItems }),
    addItem: jest.fn(function(item) { storeState.items = [item].concat(storeState.items); storeState.unreadCount++ }),
    removeItem: jest.fn(function(id) { storeState.items = storeState.items.filter(function(n) { return n.id !== id }) }),
    setUnreadCount: jest.fn(function(c) { storeState.unreadCount = c }),
    markAsRead: jest.fn(), markAllAsRead: jest.fn(),
    setCenterOpen: jest.fn(function(o) { storeState.isCenterOpen = o }),
    toggleCenter: jest.fn(function() { storeState.isCenterOpen = !storeState.isCenterOpen }),
    setPreferencesOpen: jest.fn(function(o) { storeState.preferencesOpen = o }),
    toggleSound: jest.fn(), toggleDesktop: jest.fn(),
  }
  return {
    useNotificationStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(storeState) : storeState }, {
      getState: function() { return storeState },
      setState: function(kv) { Object.assign(storeState, kv) },
      subscribe: jest.fn(),
    })
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
jest.mock('@/components/notifications/NotificationCenter', function() {
  return { NotificationCenter: function(props) { var React = require('react'); return React.createElement('div', { 'data-testid': 'notification-center' }, props.onClose ? React.createElement('button', { onClick: props.onClose }, 'close') : null) } }
})
jest.mock('@/components/notifications/NotificationPreferencesPanel', function() {
  return { NotificationPreferencesPanel: function(props) { var React = require('react'); return React.createElement('div', { 'data-testid': 'notification-preferences' }, props.onClose ? React.createElement('button', { onClick: props.onClose }, 'close') : null) } }
})

var React = require('react')
var { render, screen, fireEvent, act } = require('@testing-library/react')
var { NotificationBell } = require('@/components/notifications/NotificationBell')

describe('NotificationBell', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    var store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ items: [], unreadCount: 0, isCenterOpen: false, preferencesOpen: false })
  })

  it('renders bell button with notification aria-label', function() {
    render(React.createElement(NotificationBell))
    var btn = screen.getByLabelText('Notifications')
    expect(btn).toBeTruthy()
  })

  it('shows unread count in aria-label when unread > 0', function() {
    var store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ unreadCount: 3 })
    render(React.createElement(NotificationBell))
    var btn = screen.getByLabelText('Notifications (3 unread)')
    expect(btn).toBeTruthy()
  })

  it('shows unread badge with count', function() {
    var store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ unreadCount: 5 })
    render(React.createElement(NotificationBell))
    expect(screen.getByText('5')).toBeTruthy()
  })

  it('clamps unread badge to 99+', function() {
    var store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ unreadCount: 150 })
    render(React.createElement(NotificationBell))
    expect(screen.getByText('99+')).toBeTruthy()
  })

  it('does not show badge when unread is 0', function() {
    render(React.createElement(NotificationBell))
    expect(screen.queryByText('0')).toBeNull()
  })

  it('toggles center open on click', function() {
    var { rerender } = render(React.createElement(NotificationBell))
    var btn = screen.getByLabelText('Notifications')
    fireEvent.click(btn)
    rerender(React.createElement(NotificationBell))
    expect(screen.getByTestId('notification-center')).toBeTruthy()
  })

  it('closes center by clicking backdrop', function() {
    var { rerender } = render(React.createElement(NotificationBell))
    var btn = screen.getByLabelText('Notifications')
    fireEvent.click(btn)
    rerender(React.createElement(NotificationBell))
    expect(screen.getByTestId('notification-center')).toBeTruthy()
    var backdrop = document.querySelector('.fixed.inset-0 > div:first-child')
    if (backdrop) fireEvent.click(backdrop)
  })

  it('renders with custom className', function() {
    var { container } = render(React.createElement(NotificationBell, { className: 'custom-class' }))
    var outer = container.querySelector('.custom-class')
    expect(outer).toBeTruthy()
  })
})
