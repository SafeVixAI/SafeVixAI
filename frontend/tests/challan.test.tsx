jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { from: jest.fn(), to: jest.fn(), fromTo: jest.fn(), set: jest.fn() } } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('@/lib/store', function() {
  var state = {
    challanState: { violation: '183', vehicle: '4W', jurisdiction: 'Tamil Nadu (TN)', isRepeat: false },
    setChallanState: jest.fn(),
    garageVehicles: [],
    lastSyncedGarage: null,
    riskAnalysis: { estimatedLiability: null, riskScore: null, riskLevel: null, predictedViolationsCount: null, recommendations: [] },
    setGarageVehicles: jest.fn(),
    setLastSyncedGarage: jest.fn(),
    setRiskAnalysis: jest.fn()
  }
  return { useAppStore: Object.assign(function(sel) { return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return state }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('swr', function() { return { __esModule: true, default: function() { return { data: null, isLoading: false, error: null, mutate: jest.fn() } } } })
jest.mock('@/lib/api', function() { return { calculateChallan: jest.fn(), syncGarage: jest.fn(), predictFineLiability: jest.fn(), draftDisputeAppeal: jest.fn() } })
jest.mock('@/lib/challan-metadata', function() { return { loadChallanMetadata: jest.fn() } })
jest.mock('zustand/react/shallow', function() { return { useShallow: function(fn) { return fn } } })
jest.mock('@/lib/analytics', function() { return { track: { challanCalculated: jest.fn(), chatbotQueried: jest.fn() } } })
jest.mock('@/hooks/useSwipe', function() { return { useSwipe: function() { return { onTouchStart: jest.fn(), onTouchEnd: jest.fn() } } } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent, act } = require('@testing-library/react')
var ChallanPage = require('../app/challan/page').default

describe('Challan Page', function() {
  it('renders Estimation Terminal heading', function() {
    var { getByText } = render(React.createElement(ChallanPage))
    expect(getByText('Estimation Terminal')).toBeTruthy()
  })

  it('renders vehicle class options', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('2-Wheeler')).toBeTruthy()
    expect(screen.getByText('Car/LMV')).toBeTruthy()
    expect(screen.getByText('Truck')).toBeTruthy()
    expect(screen.getByText('Bus/COMM')).toBeTruthy()
  })

  it('renders violation options with MVA sections', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Speeding (>20km/h Limit)')).toBeTruthy()
    expect(screen.getByText('Section 185 - Drunk driving')).toBeTruthy()
    expect(screen.getByText('Driving Without License')).toBeTruthy()
  })

  it('renders state jurisdiction selector', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Tamil Nadu (TN)')).toBeTruthy()
    expect(screen.getByText('Delhi (DL)')).toBeTruthy()
    expect(screen.getByText('Maharashtra (MH)')).toBeTruthy()
  })

  it('renders Garage section indicator', function() {
    var { container } = render(React.createElement(ChallanPage))
    expect(container.textContent).toContain('Garage')
  })

  it('renders Disobedience / Red Light violation', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Disobedience / Red Light')).toBeTruthy()
  })

  it('renders No Seatbelt/Helmet violation', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('No Seatbelt/Helmet')).toBeTruthy()
  })

  it('renders Uttar Pradesh and West Bengal jurisdiction options', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Uttar Pradesh (UP)')).toBeTruthy()
    expect(screen.getByText('West Bengal (WB)')).toBeTruthy()
    expect(screen.getByText('Karnataka (KA)')).toBeTruthy()
  })

  it('renders Garage tab text', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Garage')).toBeTruthy()
  })

  it('renders Risk tab text', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Risk')).toBeTruthy()
  })

  it('renders Dispute tab text', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('Dispute')).toBeTruthy()
  })

  it('switches to Garage tab on click', function() {
    render(React.createElement(ChallanPage))
    act(function() { fireEvent.click(screen.getByText('Garage')) })
    expect(screen.getByText('Garage Inventory')).toBeTruthy()
    expect(screen.getByText('{{count}} Vehicles')).toBeTruthy()
  })

  it('switches to Risk tab on click', function() {
    render(React.createElement(ChallanPage))
    act(function() { fireEvent.click(screen.getByText('Risk')) })
    expect(screen.getByText('Estimated Annual Fine')).toBeTruthy()
    expect(screen.getByText('Rs. --')).toBeTruthy()
  })

  it('switches to Dispute tab on click', function() {
    render(React.createElement(ChallanPage))
    act(function() { fireEvent.click(screen.getByText('Dispute')) })
    expect(screen.getByText('Dispute Assistant')).toBeTruthy()
    expect(screen.getByText('No Petition')).toBeTruthy()
  })

  it('shows Detailed Report button', function() {
    render(React.createElement(ChallanPage))
    expect(screen.getByText('DETAILED REPORT')).toBeTruthy()
  })

  it('switches back to Calculator tab from Garage tab', function() {
    render(React.createElement(ChallanPage))
    act(function() { fireEvent.click(screen.getByText('Garage')) })
    act(function() { fireEvent.click(screen.getByText('Calc')) })
    expect(screen.getByText('Total Liability')).toBeTruthy()
  })
})
