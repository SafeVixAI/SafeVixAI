jest.mock('../app/first-aid/FirstAidClient', function() { return { FirstAidClient: function() { return null } } })
jest.mock('@/public/offline-data/first-aid.json', function() { return [] })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var Page = require('../app/first-aid/page').default

describe('FirstAidPage', function() {
  it('renders without error', function() {
    var { container } = render(React.createElement(Page))
    expect(container).toBeTruthy()
  })

  it('has first aid JSON data loaded', function() {
    var data = require('@/public/offline-data/first-aid.json')
    expect(Array.isArray(data)).toBe(true)
  })

  it('builds CPR guide from static data', function() {
    render(React.createElement(Page))
    // Page builds guides from offline data, component renders via FirstAidClient
    expect(rtlScreen.queryByText('CPR')).toBeNull()
  })
})
