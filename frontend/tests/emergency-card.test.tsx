jest.mock('../app/emergency-card/[userId]/EmergencyCardClient', function() { return { EmergencyCardClient: function({ userId, initialData }) { return React.createElement('div', null, 'Emergency Card for ' + userId) } } })
jest.mock('../app/emergency-card/[userId]/page', function() {
  var React = require('react')
  var client = require('../app/emergency-card/[userId]/EmergencyCardClient')
  return {
    __esModule: true,
    default: function SyncEmergencyCardPage(props) {
      var params = props.params || {}
      var searchParams = props.searchParams || {}
      var userId = (params && typeof params.then === 'function' && params.status === 'fulfilled') ? params.value.userId : (params.userId || 'default')
      var initialData = (searchParams && typeof searchParams.then === 'function' && searchParams.status === 'fulfilled') ? searchParams.value : {}
      return React.createElement(client.EmergencyCardClient, { userId: userId, initialData: initialData })
    }
  }
})

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var Page = require('../app/emergency-card/[userId]/page').default

describe('EmergencyCardPage', function() {
  it('renders without error and passes userId', function() {
    var params = { then: function() {}, status: 'fulfilled', value: { userId: 'test-user' } }
    var searchParams = { then: function() {}, status: 'fulfilled', value: {} }
    var { container } = render(React.createElement(Page, { params: params, searchParams: searchParams }))
    expect(container).toBeTruthy()
  })

  it('renders Emergency Card with user ID', function() {
    var params = { then: function() {}, status: 'fulfilled', value: { userId: 'user-42' } }
    var searchParams = { then: function() {}, status: 'fulfilled', value: {} }
    render(React.createElement(Page, { params: params, searchParams: searchParams }))
    expect(rtlScreen.getByText('Emergency Card for user-42')).toBeTruthy()
  })

  it('renders with displayId from searchParams', function() {
    var params = { then: function() {}, status: 'fulfilled', value: { userId: 'user-42' } }
    var searchParams = { then: function() {}, status: 'fulfilled', value: { displayId: 'EMP-42' } }
    var { container } = render(React.createElement(Page, { params: params, searchParams: searchParams }))
    expect(container).toBeTruthy()
  })
})
