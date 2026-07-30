// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { renderHook, act } from '@testing-library/react'

describe('use-hydrated', function () {
  it('returns false initially', async function () {
    const mod = await import('../use-hydrated')
    const { result } = renderHook(function () { return mod.useHydrated() })
    expect(result.current).toBe(false)
  })

  it('markHydrated updates hook state', async function () {
    const mod = await import('../use-hydrated')
    const { result } = renderHook(function () { return mod.useHydrated() })
    act(function () { mod.markHydrated() })
    expect(result.current).toBe(true)
  })

  it('markHydrated can be called multiple times safely', async function () {
    const mod = await import('../use-hydrated')
    expect(function () { mod.markHydrated(); mod.markHydrated() }).not.toThrow()
  })

  it('returns true immediately when already hydrated', async function () {
    const mod = await import('../use-hydrated')
    mod.markHydrated()
    const { result } = renderHook(function () { return mod.useHydrated() })
    expect(result.current).toBe(true)
  })
})
