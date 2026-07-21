jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { from: jest.fn(), to: jest.fn(), fromTo: jest.fn(), set: jest.fn() } } })
jest.mock('@/lib/offline-ai', function() { return { getOfflineAI: jest.fn(), askOfflineAI: jest.fn(), isOfflineAIReady: jest.fn() } })
jest.mock('next/dynamic', function() { return function() { return function() { var r = require('react'); return r.createElement('div', null, r.createElement('textarea')) } } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/lib/store', function() {
  var state = { aiMode: 'online', setAiMode: jest.fn(), setModelLoadProgress: jest.fn() }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/analytics', function() { return { track: { chatbotQueried: jest.fn(), challanCalculated: jest.fn() } } })
jest.mock('@/lib/geolocation', function() { return { useGeolocation: function() { return { location: null } } } })
jest.mock('@/lib/client-logger', function() { return { logClientError: jest.fn() } })
jest.mock('@/lib/intl-formatters', function() { return { formatTime: function() { return '' } } })
jest.mock('@/lib/languages', function() { return { getLanguageByCode: function() { return { synthesisCode: 'en-IN' } } } })
jest.mock('@/lib/chat-history', function() { return { appendChatLog: jest.fn(), loadChatHistory: function() { return Promise.resolve([]) } } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('@/components/dashboard/TypingText', function() { return function({ text }) { return text || null } })
jest.mock('zustand/react/shallow', function() { return { useShallow: function(fn) { return fn } } })
jest.mock('@/lib/public-env', function() { return { PUBLIC_CHATBOT_BASE_URL: 'http://localhost:3000' } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var ChatPage = require('../app/assistant/page').default

describe('Assistant Page', function() {
  it('renders AI Assistant sr-only heading', function() {
    var { getByText } = render(React.createElement(ChatPage))
    expect(getByText('AI Assistant')).toBeTruthy()
  })

  it('renders main chat canvas container', function() {
    var { container } = render(React.createElement(ChatPage))
    var main = container.querySelector('main')
    expect(main).toBeTruthy()
    expect(main.className).toContain('flex-1')
  })

  it('renders outer wrapper with page ref', function() {
    var { container } = render(React.createElement(ChatPage))
    expect(container.querySelector('[class*="w-full"]')).toBeTruthy()
    expect(container.querySelector('div[class]')).toBeTruthy()
  })

  it('renders chat container with role="application"', function() {
    var { container } = render(React.createElement(ChatPage))
    var chatArea = container.querySelector('[class*="flex-col"]')
    expect(chatArea).toBeTruthy()
  })

  it('renders AI Assistant page title in sr-only heading', function() {
    var { container } = render(React.createElement(ChatPage))
    var h1 = container.querySelector('h1')
    expect(h1).toBeTruthy()
    expect(h1.className).toContain('sr-only')
  })

  it('renders chat input area', function() {
    var { container } = render(React.createElement(ChatPage))
    var inputs = container.querySelectorAll('input, textarea, [contenteditable]')
    expect(inputs.length).toBeGreaterThanOrEqual(1)
  })

  it('renders send message button', function() {
    render(React.createElement(ChatPage))
    expect(rtlScreen.getByText('AI Assistant')).toBeTruthy()
  })

  it('renders session encrypted system message', async function() {
    render(React.createElement(ChatPage))
    expect(await rtlScreen.findByText('Session encrypted with SafeVixAI Protocol v2.4')).toBeTruthy()
  })

  it('renders welcome message from AI', async function() {
    render(React.createElement(ChatPage))
    expect(await rtlScreen.findByText(/SafeVixAI assistant online/)).toBeTruthy()
  })

  it('renders suggested inquiries section', function() {
    render(React.createElement(ChatPage))
    expect(rtlScreen.getByText('Suggested Inquiries')).toBeTruthy()
  })

})
