// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('share', function () {
  beforeEach(function () {
    delete (navigator as any).share
    delete (navigator as any).clipboard
  })

  it('generateEmergencyLink creates correct URL', async function () {
    var mod = await import('../share')
    var link = mod.generateEmergencyLink(13.0827, 80.2707)
    expect(link).toContain('/locator')
    expect(link).toContain('lat=13.082700')
    expect(link).toContain('lon=80.270700')
  })

  it('generateSOSLink creates correct URL', async function () {
    var mod = await import('../share')
    var link = mod.generateSOSLink(13.0827, 80.2707)
    expect(link).toContain('/sos')
    expect(link).toContain('mode=sos')
  })

  it('generateTrackingLink creates correct URL', async function () {
    var mod = await import('../share')
    var link = mod.generateTrackingLink('session-abc')
    expect(link).toContain('/track/session-abc')
  })

  it('generateEmergencyCardLink creates correct URL', async function () {
    var mod = await import('../share')
    var link = mod.generateEmergencyCardLink('user-42')
    expect(link).toContain('/ec/user-42')
  })

  it('generateReportLink creates correct URL', async function () {
    var mod = await import('../share')
    var link = mod.generateReportLink(13.0, 80.0)
    expect(link).toContain('/report')
    expect(link).toContain('source=deeplink')
  })

  it('shareLink falls back to clipboard when no native share', async function () {
    var mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    var result = await mod.shareLink('Title', 'https://example.com')
    expect(result).toBe(true)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com')
  })

  it('shareLink uses navigator.share when available', async function () {
    var mod = await import('../share')
    var share = jest.fn().mockResolvedValue(undefined)
    ;(navigator as any).share = share
    var result = await mod.shareLink('Title', 'https://example.com', 'Text')
    expect(share).toHaveBeenCalledWith({ title: 'Title', text: 'Text', url: 'https://example.com' })
    expect(result).toBe(true)
  })

  it('shareEmergencyLocation generates link and shares', async function () {
    var mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    var result = await mod.shareEmergencyLocation(13.0, 80.0)
    expect(result).toBe(true)
  })

  it('shareTrackingSession generates link and shares', async function () {
    var mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockResolvedValue(undefined) }
    var result = await mod.shareTrackingSession('session-1')
    expect(result).toBe(true)
  })

  it('shareLink catches share error and falls through to clipboard', async function () {
    var mod = await import('../share')
    ;(navigator as any).share = jest.fn().mockRejectedValue(new Error('share failed'))
    ;(navigator as any).clipboard = { writeText: jest.fn().mockRejectedValue(new Error('clipboard error')) }
    var promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('')
    var result = await mod.shareLink('Title', 'https://example.com')
    expect(promptSpy).toHaveBeenCalledWith('Copy this link:', 'https://example.com')
    expect(result).toBe(false)
    promptSpy.mockRestore()
  })

  it('shareLink falls back to window.prompt when clipboard fails', async function () {
    var mod = await import('../share')
    ;(navigator as any).clipboard = { writeText: jest.fn().mockRejectedValue(new Error('clipboard error')) }
    var promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('')
    var result = await mod.shareLink('Title', 'https://example.com')
    expect(promptSpy).toHaveBeenCalledWith('Copy this link:', 'https://example.com')
    expect(result).toBe(false)
    promptSpy.mockRestore()
  })
})
