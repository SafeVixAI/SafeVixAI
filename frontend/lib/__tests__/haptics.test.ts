// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('haptics', function () {
  it('exports haptics object with all feedback types', async function () {
    const mod = await import('../haptics')
    expect(typeof mod.haptics.light).toBe('function')
    expect(typeof mod.haptics.medium).toBe('function')
    expect(typeof mod.haptics.heavy).toBe('function')
    expect(typeof mod.haptics.sos).toBe('function')
    expect(typeof mod.haptics.warning).toBe('function')
  })

  it('calls do not throw when navigator.vibrate is undefined', async function () {
    const mod = await import('../haptics')
    expect(function () { mod.haptics.light() }).not.toThrow()
    expect(function () { mod.haptics.medium() }).not.toThrow()
    expect(function () { mod.haptics.heavy() }).not.toThrow()
    expect(function () { mod.haptics.sos() }).not.toThrow()
    expect(function () { mod.haptics.warning() }).not.toThrow()
  })

  it('calls navigator.vibrate when available', async function () {
    const vibrate = jest.fn()
    const orig = navigator.vibrate
    ;(navigator as any).vibrate = vibrate
    const mod = await import('../haptics')
    mod.haptics.light()
    expect(vibrate).toHaveBeenCalledWith(10)
    mod.haptics.medium()
    expect(vibrate).toHaveBeenCalledWith(30)
    ;(navigator as any).vibrate = orig
  })
})
