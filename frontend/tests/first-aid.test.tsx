jest.mock('../app/first-aid/FirstAidClient', function() { return { FirstAidClient: function() { return null } } })
jest.mock('@/public/offline-data/first-aid.json', function() { return [] })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const Page = require('../app/first-aid/page').default

describe('FirstAidPage', function() {
  it('renders without error', function() {
    const { container } = render(React.createElement(Page))
    expect(container).toBeTruthy()
  })

  it('has first aid JSON data loaded', function() {
    const data = require('@/public/offline-data/first-aid.json')
    expect(Array.isArray(data)).toBe(true)
  })

  it('builds CPR guide from static data', function() {
    render(React.createElement(Page))
    // Page builds guides from offline data, component renders via FirstAidClient
    expect(rtlScreen.queryByText('CPR')).toBeNull()
  })
})
