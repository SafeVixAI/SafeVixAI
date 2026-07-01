jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('react-i18next', function() { return { useTranslation: function() { return { t: function(k, fb) { return typeof fb === 'string' ? fb : k } } } } })
jest.mock('../app/landing/hooks/useSmoothScroll', function() { return { useSmoothScroll: function() {} } })
jest.mock('../app/landing/hooks/useBackendPrewarm', function() { return { useBackendPrewarm: function() {} } })
jest.mock('../app/landing/components/LandingNavbar', function() { return function() { return null } })
jest.mock('../app/landing/components/HeroSection', function() { return function() { return null } })
jest.mock('../app/landing/components/CrisisSection', function() { return function() { return null } })
jest.mock('../app/landing/components/HowItWorks', function() { return function() { return null } })
jest.mock('../app/landing/components/CoreModules', function() { return function() { return null } })
jest.mock('../app/landing/components/CommandCenter', function() { return function() { return null } })
jest.mock('../app/landing/components/AIInfrastructure', function() { return function() { return null } })
jest.mock('../app/landing/components/NationalNetwork', function() { return function() { return null } })
jest.mock('../app/landing/components/TechStack', function() { return function() { return null } })
jest.mock('../app/landing/components/MissionSection', function() { return function() { return null } })
jest.mock('../app/landing/components/CTASection', function() { return function() { return null } })
jest.mock('../app/landing/components/LandingFooter', function() { return function() { return null } })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var LandingPage = require('../app/landing/page').default

describe('Landing Page', function() {
  it('renders sr-only heading', function() {
    render(React.createElement(LandingPage))
    expect(screen.getByText('SafeVixAI - Road Safety Platform')).toBeTruthy()
  })

  it('renders main element', function() {
    render(React.createElement(LandingPage))
    expect(document.querySelector('main')).toBeTruthy()
  })

  it('renders without error', function() {
    var { container } = render(React.createElement(LandingPage))
    expect(container).toBeTruthy()
  })
})
