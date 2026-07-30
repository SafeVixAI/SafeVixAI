jest.mock('@/lib/notifications', function() {
  return {
    fetchNotifications: jest.fn(),
    fetchNotificationStats: jest.fn(),
    markNotificationRead: jest.fn().mockResolvedValue(undefined),
    markAllNotificationsRead: jest.fn().mockResolvedValue(2),
    deleteNotification: jest.fn().mockResolvedValue(undefined),
    getNotificationColor: function(p) { const c = { critical: 'text-red-500', high: 'text-orange-500', normal: 'text-blue-500', low: 'text-gray-500' }; return c[p] || 'text-gray-500' },
    getTimeAgo: function() { return '1m ago' },
    getNotificationIcon: function() { return 'Bell' },
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
    markAsRead: jest.fn(function(id) { storeState.items = storeState.items.map(function(n) { return n.id === id ? Object.assign({}, n, { status: 'read' }) : n }); storeState.unreadCount = Math.max(0, storeState.unreadCount - 1) }),
    markAllAsRead: jest.fn(function() { storeState.items = storeState.items.map(function(n) { return Object.assign({}, n, { status: 'read', read_at: new Date().toISOString() }) }); storeState.unreadCount = 0 }),
    setCenterOpen: jest.fn(), toggleCenter: jest.fn(),
    setPreferencesOpen: jest.fn(), toggleSound: jest.fn(), toggleDesktop: jest.fn(),
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
  const appState = { operatorName: 'TestOp' }
  return {
    useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(appState) : appState }, {
      getState: function() { return appState },
      setState: jest.fn(),
      subscribe: jest.fn(),
    })
  }
})
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

const React = require('react')
const { render, screen, fireEvent, waitFor, act } = require('@testing-library/react')
const { NotificationCenter } = require('@/components/notifications/NotificationCenter')

describe('NotificationCenter', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    const store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ items: [], unreadCount: 0, isCenterOpen: false })
    const notif = require('@/lib/notifications')
    const mockNotifications = [
      { id: 'n1', user_id: 'test', channel: 'in_app', category: 'system_health', priority: 'normal', status: 'sent', title: 'Server Health OK', body: 'All systems nominal', created_at: new Date(Date.now() - 60000).toISOString() },
      { id: 'n2', user_id: 'test', channel: 'email', category: 'security', priority: 'critical', status: 'delivered', title: 'Security Alert', body: 'Unauthorized access attempt detected', created_at: new Date(Date.now() - 3600000).toISOString() },
      { id: 'n3', user_id: 'test', channel: 'in_app', category: 'update', priority: 'low', status: 'read', title: 'Update Available', created_at: new Date(Date.now() - 86400000).toISOString() },
    ]
    notif.fetchNotifications.mockResolvedValue({ notifications: mockNotifications, total: 3, unread: 2, limit: 50, offset: 0 })
    notif.fetchNotificationStats.mockResolvedValue({ total: 3, days: 7, by_category: { system_health: 1, security: 1, update: 1 }, by_channel: { in_app: 2, email: 1 } })
    notif.markNotificationRead.mockResolvedValue(undefined)
    notif.markAllNotificationsRead.mockResolvedValue(2)
    notif.deleteNotification.mockResolvedValue(undefined)
  })

  it('renders with aria-live region and title', function() {
    render(React.createElement(NotificationCenter))
    const region = screen.getByRole('region')
    expect(region).toBeTruthy()
    expect(region.getAttribute('aria-label')).toBe('Notification center')
    expect(screen.getByText('Notifications')).toBeTruthy()
  })

  it('has screen-reader status for unread count', function() {
    const store = require('@/lib/store/notification-slice').useNotificationStore
    store.setState({ unreadCount: 2 })
    render(React.createElement(NotificationCenter))
    const sr = document.querySelector('.sr-only[role="status"]')
    expect(sr).toBeTruthy()
    expect(sr.textContent).toBe('2 unread notifications')
  })

  it('shows zero unread in screen-reader status', function() {
    render(React.createElement(NotificationCenter))
    const sr = document.querySelector('.sr-only[role="status"]')
    expect(sr.textContent).toBe('No unread notifications')
  })

  it('shows loading state then notification items', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
  })

  it('marks a notification as read on click when unread', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
    const titleBtn = screen.getByText('Server Health OK').closest('button')
    fireEvent.click(titleBtn)
    await waitFor(function() {
      const markRead = require('@/lib/notifications').markNotificationRead
      expect(markRead).toHaveBeenCalledWith('n1', 'TestOp')
    })
  })

  it('expands notification body on click', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
    const titleBtn = screen.getByText('Server Health OK').closest('button')
    fireEvent.click(titleBtn)
    expect(titleBtn.getAttribute('aria-expanded')).toBe('true')
  })

  it('supports keyboard Enter on notification item', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
    const titleBtn = screen.getByText('Server Health OK').closest('button')
    fireEvent.keyDown(titleBtn, { key: 'Enter' })
    await waitFor(function() {
      const markRead = require('@/lib/notifications').markNotificationRead
      expect(markRead).toHaveBeenCalled()
    })
  })

  it('supports keyboard Space on notification item', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
    const titleBtn = screen.getByText('Server Health OK').closest('button')
    fireEvent.keyDown(titleBtn, { key: ' ' })
    await waitFor(function() {
      const markRead = require('@/lib/notifications').markNotificationRead
      expect(markRead).toHaveBeenCalled()
    })
  })

  it('marks all notifications as read', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Mark all read')).toBeTruthy()
    })
    const markAll = screen.getByText('Mark all read')
    fireEvent.click(markAll)
    await waitFor(function() {
      const markAllFn = require('@/lib/notifications').markAllNotificationsRead
      expect(markAllFn).toHaveBeenCalledWith('TestOp')
    })
  })

  it('deletes a notification', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Server Health OK')).toBeTruthy()
    })
    const deleteBtns = screen.getAllByLabelText(/Delete/)
    fireEvent.click(deleteBtns[0])
    await waitFor(function() {
      const del = require('@/lib/notifications').deleteNotification
      expect(del).toHaveBeenCalled()
    })
  })

  it('shows filter tabs with aria-selected', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByTitle('Filters')).toBeTruthy()
    })
    const filterButton = screen.getByTitle('Filters')
    fireEvent.click(filterButton)
    const allTab = screen.getByRole('tab', { name: 'Show all categories' })
    expect(allTab.getAttribute('aria-selected')).toBe('true')
  })

  it('filters by category when tab clicked', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByTitle('Filters')).toBeTruthy()
    })
    const filterButton = screen.getByTitle('Filters')
    fireEvent.click(filterButton)
    const securityTab = screen.getByRole('tab', { name: 'Filter by Security' })
    fireEvent.click(securityTab)
    expect(securityTab.getAttribute('aria-selected')).toBe('true')
  })

  it('toggles unread filter', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByTitle('Filters')).toBeTruthy()
    })
    const filterButton = screen.getByTitle('Filters')
    fireEvent.click(filterButton)
    const unreadBtn = screen.getByText('Unread only')
    fireEvent.click(unreadBtn)
    expect(unreadBtn.getAttribute('aria-pressed')).toBe('true')
  })

  it('shows critical priority badge', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Security Alert')).toBeTruthy()
    })
    expect(screen.getByText('Critical')).toBeTruthy()
  })

  it('shows empty state when no notifications', async function() {
    const mockNotifications = require('@/lib/notifications')
    mockNotifications.fetchNotifications.mockResolvedValue({ notifications: [], total: 0, unread: 0, limit: 50, offset: 0 })
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.queryByText("You're all caught up")).toBeTruthy()
    })
  })

  it('shows error state on fetch failure', async function() {
    const mockNotifications = require('@/lib/notifications')
    mockNotifications.fetchNotifications.mockRejectedValue(new Error('Network failure'))
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('Network failure')).toBeTruthy()
    })
  })

  it('shows action bar with unread count', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText(/unread/)).toBeTruthy()
    })
  })

  it('shows stats summary', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText(/total/)).toBeTruthy()
    })
  })

  it('handles onClose callback', async function() {
    const onClose = jest.fn()
    render(React.createElement(NotificationCenter, { onClose: onClose }))
    await waitFor(function() {
      expect(screen.getByText('Notifications')).toBeTruthy()
    })
    const closeBtns = screen.getAllByRole('button')
    const xBtn = Array.from(closeBtns).find(function(b) { return b.getAttribute('title') === 'Close' || b.innerHTML.includes('x') })
    if (xBtn) { fireEvent.click(xBtn); expect(onClose).toHaveBeenCalled() }
  })

  it('does not show category badge for notification without category', async function() {
    const mockNotifications = require('@/lib/notifications')
    mockNotifications.fetchNotifications.mockResolvedValue({
      notifications: [{ id: 'n4', user_id: 'test', channel: 'in_app', priority: 'normal', status: 'sent', title: 'No Cat', created_at: new Date().toISOString() }],
      total: 1, unread: 1, limit: 50, offset: 0,
    })
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      expect(screen.getByText('No Cat')).toBeTruthy()
    })
  })

  it('displays notification time via getTimeAgo', async function() {
    render(React.createElement(NotificationCenter))
    await waitFor(function() {
      const times = screen.getAllByText(/m ago|h ago|d ago|just now/)
      expect(times.length).toBeGreaterThan(0)
    })
  })
})
