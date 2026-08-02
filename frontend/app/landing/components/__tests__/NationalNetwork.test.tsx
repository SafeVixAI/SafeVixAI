jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  const React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
    useCountUp: function() { return React.useRef(null) },
  }
})

const React = require('react')
const { render, screen: rtlScreen, waitFor } = require('@testing-library/react')
const { fetchPublicStats } = require('@/lib/api')

jest.mock('@/lib/api', () => ({
  fetchPublicStats: jest.fn().mockResolvedValue({
    total_complaints_filed: 1000,
    total_resolved: 500,
    active_field_officers: 150,
    resolution_rate: 85
  })
}))

const NationalNetwork = require('../NationalNetwork').default

describe('NationalNetwork', function() {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches and renders live stats', async function() {
    render(React.createElement(NationalNetwork))
    expect(fetchPublicStats).toHaveBeenCalledTimes(1)
    
    // Wait for the mock data to render
    await waitFor(() => {
      expect(rtlScreen.getByText('Total Incidents')).toBeTruthy()
      expect(rtlScreen.getByText('Incidents Resolved')).toBeTruthy()
      expect(rtlScreen.getByText('Active Officers')).toBeTruthy()
      expect(rtlScreen.getByText('Resolution Rate')).toBeTruthy()
    })
  })
  it('handles fetch error silently', async function() {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    fetchPublicStats.mockRejectedValueOnce(new Error('Network error'))
    
    render(React.createElement(NationalNetwork))
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error))
    })
    consoleSpy.mockRestore()
  })

  it('renders the section overline', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('NATIONAL NETWORK')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('Connected Intelligence')).toBeTruthy()
  })

  it('renders the section description', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/A unified network connecting hospitals/)).toBeTruthy()
  })

  it('renders the India SVG map with aria-label', function() {
    render(React.createElement(NationalNetwork))
    const map = rtlScreen.getByRole('img')
    expect(map.getAttribute('aria-label')).toContain('National network map')
  })



  it('renders stat counter labels', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('States Connected')).toBeTruthy()
    expect(rtlScreen.getByText('Hospitals Linked')).toBeTruthy()
    expect(rtlScreen.getByText('Police Stations')).toBeTruthy()
    expect(rtlScreen.getByText('Citizens Protected')).toBeTruthy()
  })

  it('renders descriptive content about end-to-end coverage', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/end-to-end coverage/)).toBeTruthy()
  })

  it('renders network status indicator', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('Network Status: Operational')).toBeTruthy()
  })

  it('renders network status details', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/All 28 state nodes online/)).toBeTruthy()
  })
})
