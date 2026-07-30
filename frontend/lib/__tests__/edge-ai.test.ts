// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.useFakeTimers()

describe('edge-ai', function () {
  afterAll(function () {
    jest.useRealTimers()
  })

  it('generateEdgeResponse returns offline pothole response', async function () {
    const mod = await import('../edge-ai')
    const promise = mod.generateEdgeResponse('There is a pothole on the road', false)
    jest.advanceTimersByTime(1200)
    const result = await promise
    expect(result).toContain('Motor Vehicles Act')
  })

  it('generateEdgeResponse returns offline accident response', async function () {
    const mod = await import('../edge-ai')
    const promise = mod.generateEdgeResponse('I see an accident ahead', false)
    jest.advanceTimersByTime(1200)
    const result = await promise
    expect(result).toContain('SOS')
  })

  it('generateEdgeResponse returns default offline response', async function () {
    const mod = await import('../edge-ai')
    const promise = mod.generateEdgeResponse('What is the weather?', false)
    jest.advanceTimersByTime(1200)
    const result = await promise
    expect(result).toContain('Protocol Sentinel')
  })

  it('generateEdgeResponse returns online response', async function () {
    const mod = await import('../edge-ai')
    const promise = mod.generateEdgeResponse('Tell me about traffic rules', true)
    jest.advanceTimersByTime(1200)
    const result = await promise
    expect(result).toContain('[Cloud AI Response]')
  })
})
