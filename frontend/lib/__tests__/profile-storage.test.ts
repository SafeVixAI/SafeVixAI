// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

describe('profile-storage', function () {
  beforeEach(function () {
    // jsdom does not expose window.indexedDB; polyfill for browser-path tests
    if (typeof window !== 'undefined' && !('indexedDB' in window)) {
      Object.defineProperty(window, 'indexedDB', { value: {}, writable: true, configurable: true })
    }
  })

  it('openProfileDb opens database', async function () {
    const mod = await import('../profile-storage')
    const db = await mod.openProfileDb()
    expect(db).toBeDefined()
  })

  it('openProfileDb returns null when not browser', async function () {
    // Simulate non-browser by removing indexedDB from window
    delete (window as any).indexedDB
    jest.resetModules()
    const mod = await import('../profile-storage')
    const db = await mod.openProfileDb()
    expect(db).toBeNull()
  })

  it('loadUserProfileFromIndexedDB returns null when not browser', async function () {
    delete (window as any).indexedDB
    jest.resetModules()
    const mod = await import('../profile-storage')
    const result = await mod.loadUserProfileFromIndexedDB()
    expect(result).toBeNull()
  })

  it('migrateUserProfileFromLocalStorage handles parse errors', async function () {
    const getItemMock = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('invalid-json')
    const mod = await import('../profile-storage')
    await expect(mod.migrateUserProfileFromLocalStorage()).resolves.toBeUndefined()
    getItemMock.mockRestore()
  })

  it('migrateUserProfileFromLocalStorage happy path — stores profile and cleans localStorage', async function () {
    const profile = { name: 'Test', bloodGroup: 'O+', phone: '+91' }
    const raw = JSON.stringify({ state: { userProfile: profile, other: 'data' } })
    const getItemSpy = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(raw)
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem').mockReturnValue()
    jest.resetModules()
    const mod = await import('../profile-storage')
    await mod.migrateUserProfileFromLocalStorage()
    expect(getItemSpy).toHaveBeenCalledWith('svai-storage')
    expect(setItemSpy).toHaveBeenCalled()
    const storedVal = JSON.parse(setItemSpy.mock.calls[0][1])
    expect(storedVal.state.userProfile).toBeUndefined()
    expect(storedVal.state.other).toBe('data')
    getItemSpy.mockRestore()
    setItemSpy.mockRestore()
  })

  it('migrateUserProfileFromLocalStorage returns early when no legacy data', async function () {
    const getItemMock = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(null)
    const mod = await import('../profile-storage')
    await mod.migrateUserProfileFromLocalStorage()
    getItemMock.mockRestore()
  })

  it('migrateUserProfileFromLocalStorage returns early when not browser', async function () {
    delete (window as any).indexedDB
    jest.resetModules()
    const mod = await import('../profile-storage')
    await expect(mod.migrateUserProfileFromLocalStorage()).resolves.toBeUndefined()
  })

  it('saveUserProfileToIndexedDB stores profile', async function () {
    const profile = { id: 'u1', name: 'Test', bloodGroup: 'O+', phone: '+91', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' }
    const mod = await import('../profile-storage')
    await expect(mod.saveUserProfileToIndexedDB(profile)).resolves.toBeUndefined()
  })

  it('saveUserProfileToIndexedDB returns early when not browser', async function () {
    delete (window as any).indexedDB
    jest.resetModules()
    const mod = await import('../profile-storage')
    const profile = { id: 'u1', name: 'Test', bloodGroup: 'O+', phone: '+91', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' }
    await expect(mod.saveUserProfileToIndexedDB(profile)).resolves.toBeUndefined()
  })

  it('loadUserProfileFromIndexedDB returns profile when exists', async function () {
    const mod = await import('../profile-storage')
    const profile = await mod.loadUserProfileFromIndexedDB()
    expect(profile).toBeNull()
  })

  it('exports all expected functions', async function () {
    const mod = await import('../profile-storage')
    expect(typeof mod.openProfileDb).toBe('function')
    expect(typeof mod.saveUserProfileToIndexedDB).toBe('function')
    expect(typeof mod.loadUserProfileFromIndexedDB).toBe('function')
    expect(typeof mod.migrateUserProfileFromLocalStorage).toBe('function')
  })

})

