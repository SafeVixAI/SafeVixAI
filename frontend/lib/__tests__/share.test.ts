// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('share', function () {
  beforeEach(function () {
    delete (navigator as any).share
    delete (navigator as any).clipboard
  })

  it('generateEmergencyLink creates correct URL', async function () {
    const mod = await import('../share')
    const link = mod.generateEmergencyLink(13.0827, 80.2707)
    expect(link).toContain('/locator')
    expect(link).toContain('lat=13.082700')
    expect(link).toContain('lon=80.270700')
  })

  it('generateSOSLink creates correct URL', async function () {
    const mod = await import('../share')
    const link = mod.generateSOSLink(13.0827, 80.2707)
    expect(link).toContain('/sos')
    expect(link).toContain('mode=sos')
  })

  it('generateTrackingLink creates correct URL', async function () {
    const mod = await import('../share')
    const link = mod.generateTrackingLink('session-abc')
    expect(link).toContain('/track/session-abc')
  })

  it('generateEmergencyCardLink creates correct URL', async function () {
    const mod = await import('../share')
    const link = mod.generateEmergencyCardLink('user-42')
    expect(link).toContain('/ec/user-42')
  })

  it('generateReportLink creates correct URL', async function () {
    const mod = await import('../share')
    const link = mod.generateReportLink(13.0, 80.0)
    expect(link).toContain('/report')
    expect(link).toContain('source=deeplink')
  })

  it('shareLink falls back to clipboard when no native share', async function () {
    const mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    const result = await mod.shareLink('Title', 'https://example.com')
    expect(result).toBe(true)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com')
  })

  it('shareLink uses navigator.share when available', async function () {
    const mod = await import('../share')
    const share = jest.fn().mockResolvedValue(undefined)
    ;(navigator as any).share = share
    const result = await mod.shareLink('Title', 'https://example.com', 'Text')
    expect(share).toHaveBeenCalledWith({ title: 'Title', text: 'Text', url: 'https://example.com' })
    expect(result).toBe(true)
  })

  it('shareEmergencyLocation generates link and shares', async function () {
    const mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    const result = await mod.shareEmergencyLocation(13.0, 80.0)
    expect(result).toBe(true)
  })

  it('shareTrackingSession generates link and shares', async function () {
    const mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    const result = await mod.shareTrackingSession('session-1')
    expect(result).toBe(true)
  })

  it('shareLink catches share error and falls through to clipboard', async function () {
    const mod = await import('../share')
    ;(navigator as any).share = jest.fn().mockRejectedValue(new Error('share failed'))
    ;(navigator as any).clipboard = { writeText: jest.fn().mockRejectedValue(new Error('clipboard error')) }
    const promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('')
    const result = await mod.shareLink('Title', 'https://example.com')
    expect(promptSpy).toHaveBeenCalledWith('Copy this link:', 'https://example.com')
    expect(result).toBe(false)
    promptSpy.mockRestore()
  })

  it('shareLink error not AbortError falls through to clipboard', async function () {
    const mod = await import('../share')
    ;(navigator as any).share = jest.fn().mockRejectedValue(new Error('network error'))
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    const result = await mod.shareLink('Title', 'https://example.com')
    expect(result).toBe(true)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com')
  })

  it('shareLink returns false on AbortError without clipboard fallback', async function () {
    const mod = await import('../share')
    ;(navigator as any).share = jest.fn().mockRejectedValue(Object.assign(new Error('abort'), { name: 'AbortError' }))
    const clipboardSpy = jest.fn()
    ;(navigator as any).clipboard = { writeText: clipboardSpy }
    const result = await mod.shareLink('Title', 'https://example.com')
    expect(result).toBe(false)
    expect(clipboardSpy).not.toHaveBeenCalled()
  })

  it('shareLink falls back to window.prompt when clipboard fails', async function () {
    const mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockRejectedValue(new Error('clipboard error')) }
    const promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('')
    const result = await mod.shareLink('Title', 'https://example.com')
    expect(promptSpy).toHaveBeenCalledWith('Copy this link:', 'https://example.com')
    expect(result).toBe(false)
    promptSpy.mockRestore()
  })
})
