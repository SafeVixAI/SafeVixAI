// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('navigation-launch', function () {
  beforeEach(function () {
    localStorage.clear()
  })

  afterEach(function () {
    jest.restoreAllMocks()
  })

  it('openGoogleMaps creates correct URL', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openGoogleMaps({ lat: 13.08, lon: 80.27, name: 'Apollo' })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('google.com/maps/dir')
    expect(url).toContain('13.08')
    expect(url).toContain('80.27')
  })

  it('openGoogleMaps works without name', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openGoogleMaps({ lat: 13.08, lon: 80.27 })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('destination=13.08')
    expect(url).not.toContain('destination_place_id')
  })

  it('openWaze creates correct URL', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openWaze({ lat: 13.08, lon: 80.27 })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('waze.com/ul')
    expect(url).toContain('navigate=yes')
  })

  it('openAppleMaps creates correct URL', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openAppleMaps({ lat: 13.08, lon: 80.27, name: 'Hospital' })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('maps.apple.com')
    expect(url).toContain('daddr=13.08')
  })

  it('openAppleMaps works without name', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openAppleMaps({ lat: 10, lon: 20 })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('daddr=10')
    expect(url).not.toContain('q=')
  })

  it('getPreferredNavApp returns google when no preference', async function () {
    const mod = await import('../navigation-launch')
    expect(mod.getPreferredNavApp()).toBe('google')
  })

  it('setPreferredNavApp saves and getPreferredNavApp retrieves', async function () {
    const mod = await import('../navigation-launch')
    mod.setPreferredNavApp('waze')
    expect(mod.getPreferredNavApp()).toBe('waze')
  })

  it('getPreferredNavApp returns google for invalid saved value', async function () {
    const mod = await import('../navigation-launch')
    localStorage.setItem('svai_preferred_nav_app', 'invalid')
    expect(mod.getPreferredNavApp()).toBe('google')
  })

  it('openBestNavApp calls waze when pref is waze (lines 94-95)', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.setPreferredNavApp('waze')
    mod.openBestNavApp({ lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('waze.com')
  })

  it('openBestNavApp defaults to google when no pref (lines 101-102)', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openBestNavApp({ lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('google.com/maps')
  })

  it('openNavApp routes to waze', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openNavApp('waze', { lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('waze.com')
  })

  it('openNavApp routes to apple (line 115-116)', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openNavApp('apple', { lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('maps.apple.com')
  })

  it('openNavApp defaults to google (lines 118-120)', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openNavApp('google', { lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('google.com/maps')
  })

  it('NAV_APPS lists 3 apps', async function () {
    const mod = await import('../navigation-launch')
    expect(mod.NAV_APPS).toHaveLength(3)
  })

  it('openBestNavApp routes to apple when pref is apple', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.setPreferredNavApp('apple')
    mod.openBestNavApp({ lat: 10, lon: 20 })
    expect(openSpy.mock.calls[0][0]).toContain('maps.apple.com')
  })

  it('getPreferredNavApp returns apple on iOS platform', async function () {
    const originalUa = navigator.userAgent
    Object.defineProperty(navigator, 'userAgent', { value: 'iPad', configurable: true, writable: true })
    const mod = await import('../navigation-launch')
    expect(mod.getPreferredNavApp()).toBe('apple')
    Object.defineProperty(navigator, 'userAgent', { value: 'Android', configurable: true, writable: true })
    const mod2 = await import('../navigation-launch')
    expect(mod2.getPreferredNavApp()).toBe('google')
    Object.defineProperty(navigator, 'userAgent', { value: originalUa, configurable: true, writable: true })
  })

  it('getPreferredNavApp returns google for iOS with waze saved', async function () {
    const originalUa = navigator.userAgent
    Object.defineProperty(navigator, 'userAgent', { value: 'iPad', configurable: true, writable: true })
    localStorage.setItem('svai_preferred_nav_app', 'waze')
    const mod = await import('../navigation-launch')
    expect(mod.getPreferredNavApp()).toBe('waze')
    Object.defineProperty(navigator, 'userAgent', { value: originalUa, configurable: true, writable: true })
  })

  it('openGoogleMaps includes destination_place_id when name provided', async function () {
    const mod = await import('../navigation-launch')
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return null })
    mod.openGoogleMaps({ lat: 13.08, lon: 80.27, name: 'Apollo Hospital' })
    const url = openSpy.mock.calls[0][0]
    expect(url).toContain('destination_place_id')
  })

  it('openExternal sets opener to null when popup exists', async function () {
    const mockPopup = { opener: 'original' } as any
    const openSpy = jest.spyOn(window, 'open').mockImplementation(function () { return mockPopup })
    const mod = await import('../navigation-launch')
    mod.openGoogleMaps({ lat: 10, lon: 20 })
    expect(mockPopup.opener).toBeNull()
    openSpy.mockRestore()
  })
})
