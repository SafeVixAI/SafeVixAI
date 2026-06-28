// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { renderHook, act } from '@testing-library/react'

describe('use-hydrated', function () {
  it('returns false initially', async function () {
    var mod = await import('../use-hydrated')
    var { result } = renderHook(function () { return mod.useHydrated() })
    expect(result.current).toBe(false)
  })

  it('markHydrated updates hook state', async function () {
    var mod = await import('../use-hydrated')
    var { result } = renderHook(function () { return mod.useHydrated() })
    act(function () { mod.markHydrated() })
    expect(result.current).toBe(true)
  })

  it('markHydrated can be called multiple times safely', async function () {
    var mod = await import('../use-hydrated')
    expect(function () { mod.markHydrated(); mod.markHydrated() }).not.toThrow()
  })

  it('returns true immediately when already hydrated', async function () {
    var mod = await import('../use-hydrated')
    mod.markHydrated()
    var { result } = renderHook(function () { return mod.useHydrated() })
    expect(result.current).toBe(true)
  })
})
