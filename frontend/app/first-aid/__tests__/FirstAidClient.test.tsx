jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn() } } })
jest.mock('@/lib/store', function() { return { useAppStore: function(fn) { if (typeof fn === 'function') fn({ setSystemSidebarOpen: jest.fn() }); return jest.fn() } } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen: rtlScreen, fireEvent } = require('@testing-library/react')
var { FirstAidClient } = require('../FirstAidClient')

var mockGuides = {
  cpr: { id: 'cpr', title: 'CPR', subtitle: 'Cardiopulmonary Resuscitation', accent: '#FF6B6B', icon: 'Heart', iconType: 'filled', steps: ['Call 112', 'Check breathing', 'Start compressions'] },
  choking: { id: 'choking', title: 'Choking', subtitle: 'Heimlich maneuver', accent: '#FFA500', icon: 'AlertTriangle', iconType: 'outlined', steps: ['Recognize choking', 'Perform Heimlich'] },
  burns: { id: 'burns', title: 'Burns', subtitle: 'Burn treatment', accent: '#FF4444', icon: 'Flame', iconType: 'filled', steps: ['Cool the burn', 'Cover with sterile cloth'] },
}

describe('FirstAidClient', function() {
  it('renders first aid guides', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(rtlScreen.getByText('CPR')).toBeTruthy()
    expect(rtlScreen.getByText('Choking')).toBeTruthy()
    expect(rtlScreen.getByText('Burns')).toBeTruthy()
  })

  it('renders search input', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(rtlScreen.getByPlaceholderText(/Search/)).toBeTruthy()
  })

  it('renders guide subtitles', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(rtlScreen.getByText('Cardiopulmonary Resuscitation')).toBeTruthy()
    expect(rtlScreen.getByText('Heimlich maneuver')).toBeTruthy()
  })

  it('renders emergency mode toggle', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(rtlScreen.getByText(/Emergency/i)).toBeTruthy()
  })

  it('opens guide detail on click', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    fireEvent.click(rtlScreen.getByText('CPR'))
    expect(rtlScreen.getAllByText('Call 112').length).toBeGreaterThanOrEqual(1)
    expect(rtlScreen.getByText('Check breathing')).toBeTruthy()
    expect(rtlScreen.getByText('Start compressions')).toBeTruthy()
  })

  it('closes guide detail with close button', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    fireEvent.click(rtlScreen.getByText('CPR'))
    expect(rtlScreen.getAllByText('Call 112').length).toBeGreaterThanOrEqual(1)
    fireEvent.click(rtlScreen.getAllByText('CPR')[0])
  })

  it('filters guides by search query', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    var input = rtlScreen.getByPlaceholderText(/Search/)
    fireEvent.change(input, { target: { value: 'Burn' } })
    expect(rtlScreen.getByText('Burns')).toBeTruthy()
    expect(rtlScreen.queryByText('CPR')).toBeNull()
  })

  it('shows empty state when search has no matches', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    var input = rtlScreen.getByPlaceholderText(/Search/)
    fireEvent.change(input, { target: { value: 'zzzznonexistent' } })
    expect(rtlScreen.getByText(/No protocols match/)).toBeTruthy()
  })

  it('toggles step completion in guide detail', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    fireEvent.click(rtlScreen.getByText('CPR'))
    var steps = rtlScreen.getAllByText('Call 112')
    fireEvent.click(steps[0])
    expect(rtlScreen.getByText('first_aid.complete_count')).toBeTruthy()
  })

  it('renders Invoke Full Scan button', function() {
    render(React.createElement(FirstAidClient, { guides: mockGuides }))
    expect(rtlScreen.getByText(/Invoke Full Scan/)).toBeTruthy()
  })
})
