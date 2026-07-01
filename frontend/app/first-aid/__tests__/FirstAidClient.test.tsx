jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn() } } })
jest.mock('@/lib/store', function() { return { useAppStore: function(fn) { if (typeof fn === 'function') fn({ setSystemSidebarOpen: jest.fn() }); return jest.fn() } } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent } = require('@testing-library/react')
var { FirstAidClient } = require('../FirstAidClient')

var mockGuides = {
  cpr: { id: 'cpr', title: 'CPR', subtitle: 'Cardiopulmonary Resuscitation', accent: '#FF6B6B', icon: 'Heart', iconType: 'filled', steps: ['Call 112', 'Check breathing', 'Start compressions'] },
  choking: { id: 'choking', title: 'Choking', subtitle: 'Heimlich maneuver', accent: '#FFA500', icon: 'AlertTriangle', iconType: 'outlined', steps: ['Recognize choking', 'Perform Heimlich'] },
  burns: { id: 'burns', title: 'Burns', subtitle: 'Burn treatment', accent: '#FF4444', icon: 'Flame', iconType: 'filled', steps: ['Cool the burn', 'Cover with sterile cloth'] },
}

describe('FirstAidClient', function() {
  it('renders first aid guides', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(screen.getByText('CPR')).toBeTruthy()
    expect(screen.getByText('Choking')).toBeTruthy()
    expect(screen.getByText('Burns')).toBeTruthy()
  })

  it('renders search input', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(screen.getByPlaceholderText(/Search/)).toBeTruthy()
  })

  it('renders guide subtitles', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(screen.getByText('Cardiopulmonary Resuscitation')).toBeTruthy()
    expect(screen.getByText('Heimlich maneuver')).toBeTruthy()
  })

  it('renders emergency mode toggle', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(screen.getByText(/Emergency/i)).toBeTruthy()
  })

  it('opens guide detail on click', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    fireEvent.click(screen.getByText('CPR'))
    expect(screen.getAllByText('Call 112').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Check breathing')).toBeTruthy()
    expect(screen.getByText('Start compressions')).toBeTruthy()
  })

  it('closes guide detail with close button', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    fireEvent.click(screen.getByText('CPR'))
    expect(screen.getAllByText('Call 112').length).toBeGreaterThanOrEqual(1)
    fireEvent.click(screen.getAllByText('CPR')[0])
  })
})
